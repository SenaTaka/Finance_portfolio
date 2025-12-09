"""
Portfolio Calculator Core Module

Main business logic for portfolio calculations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import os

from ..data.cache_manager import CacheManager
from ..data.stock_data_fetcher import StockDataFetcher


class PortfolioCalculator:
    """Core portfolio calculation logic."""
    
    def __init__(
        self,
        csv_file: str,
        force_refresh: bool = False,
        cache_dir: str = "data"
    ):
        """
        Initialize portfolio calculator.
        
        Args:
            csv_file: Path to portfolio CSV file
            force_refresh: Force refresh of all cached data
            cache_dir: Directory for cache storage
        """
        self.csv_file = csv_file
        self.force_refresh = force_refresh
        self.cache_manager = CacheManager(cache_dir=cache_dir)
        self.data_fetcher = StockDataFetcher()
        self.usd_jpy = 1.0
        
    def get_ticker_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with ticker data or None if error
        """
        try:
            cached = self.cache_manager.get(ticker)
            now_str = datetime.now().isoformat()
            
            # Determine what needs to be fetched
            need_metadata = self.cache_manager.needs_metadata_update(ticker, self.force_refresh)
            need_volatility = self.cache_manager.needs_volatility_update(ticker, self.force_refresh)
            need_price = self.cache_manager.needs_price_update(ticker, self.force_refresh)
            
            hist = None
            current_price = None
            
            # Fetch historical data if needed for volatility
            if need_volatility:
                print(f"  {ticker}: Fetching 1 year of data...")
                hist = self.data_fetcher.get_stock_history(ticker, period='1y')
                if hist is None or hist.empty:
                    return None
                
                current_price = hist['Close'].iloc[-1]
                
                # Calculate volatility and sharpe
                sigma, sharpe = self.data_fetcher.calculate_volatility_and_sharpe(
                    hist, 
                    self.data_fetcher.risk_free_rate
                )
                
                # Update cache
                cached['sigma'] = sigma
                cached['sharpe'] = sharpe
                cached['volatility_updated'] = now_str
                
                # Store history for correlation matrix
                cached['history'] = hist['Close'].tolist()
                cached['history_index'] = [d.isoformat() for d in hist.index]
                
            elif need_price:
                # Only fetch recent price data
                print(f"  {ticker}: Fetching current price...")
                current_price = self.data_fetcher.get_stock_price(ticker, period='1d')
                if current_price is None:
                    # Fall back to cached price if available
                    current_price = cached.get('price')
            else:
                # Use cached data
                print(f"  {ticker}: Using cached data")
                current_price = cached.get('price')
            
            # Update price cache
            if current_price is not None:
                cached['price'] = current_price
                cached['price_updated'] = now_str
            
            # Fetch metadata if needed
            if need_metadata:
                print(f"  {ticker}: Fetching metadata...")
                info = self.data_fetcher.get_stock_info(ticker)
                cached.update(info)
                cached['metadata_updated'] = now_str
            
            # Update cache
            self.cache_manager.set(ticker, cached)
            
            # Build result from cache
            result = {
                'price': cached.get('price'),
                'PER': cached.get('PER'),
                'sigma': cached.get('sigma'),
                'sharpe': cached.get('sharpe'),
                'dividend_yield': cached.get('dividend_yield'),
                'currency': cached.get('currency', 'USD'),
                'name': cached.get('name', ticker),
                'sector': cached.get('sector'),
                'industry': cached.get('industry'),
                'country': cached.get('country'),
            }
            
            # Reconstruct history if available
            if cached.get('history') and cached.get('history_index'):
                try:
                    result['history'] = pd.Series(
                        cached['history'],
                        index=pd.to_datetime(cached['history_index'])
                    )
                except (ValueError, TypeError) as e:
                    print(f"  {ticker}: Failed to reconstruct history: {e}")
                    result['history'] = None
            
            return result
            
        except Exception as e:
            print(f"{ticker}: データ取得エラー - {e}")
            return None
    
    def calculate_correlation_matrix(
        self, 
        hist_data: Dict[str, pd.Series]
    ) -> Optional[pd.DataFrame]:
        """
        Calculate correlation matrix from historical data.
        
        Args:
            hist_data: Dictionary mapping tickers to price history Series
            
        Returns:
            Correlation DataFrame or None
        """
        if not hist_data:
            return None
        
        try:
            price_df = pd.DataFrame(hist_data)
            # Daily return correlation
            corr_df = price_df.pct_change().dropna().corr()
            return corr_df
        except Exception as e:
            print(f"Failed to calculate correlation matrix: {e}")
            return None
    
    def calculate_portfolio(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate portfolio metrics.
        
        Args:
            df: DataFrame with ticker data
            
        Returns:
            DataFrame with calculated portfolio data
        """
        # Fetch exchange rate
        self.usd_jpy = self.data_fetcher.get_exchange_rate()
        
        # Fetch risk-free rate
        self.data_fetcher.get_risk_free_rate()
        
        results = []
        hist_data = {}
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            shares = row['shares']
            
            print(f"Fetching data: {ticker}...")
            data = self.get_ticker_data(ticker)
            
            if data:
                data['ticker'] = ticker
                data['shares'] = shares
                
                # Store historical data for correlation
                if data.get('history') is not None:
                    hist_data[ticker] = data.pop('history')
                
                # Calculate values based on currency
                price = data['price']
                currency = data.get('currency', 'USD')
                
                if currency == 'JPY':
                    val_jp = price * shares
                    val_usd = val_jp / self.usd_jpy if self.usd_jpy > 0 else 0
                else:
                    val_usd = price * shares
                    val_jp = val_usd * self.usd_jpy
                
                data['value'] = val_usd
                data['value_jp'] = int(val_jp)
                results.append(data)
            else:
                # Error case: empty data
                results.append({
                    'ticker': ticker,
                    'shares': shares,
                    'price': 0,
                    'PER': None,
                    'sigma': None,
                    'sharpe': None,
                    'dividend_yield': None,
                    'value': 0,
                    'value_jp': 0,
                    'currency': 'N/A',
                    'name': 'N/A',
                    'sector': 'Unknown'
                })
        
        result_df = pd.DataFrame(results)
        
        # Calculate allocation ratio
        total_value = result_df['value'].sum()
        if total_value > 0:
            result_df['ratio'] = (result_df['value'] / total_value * 100).round(2)
        else:
            result_df['ratio'] = 0
        
        # Add exchange rate metadata
        result_df['usd_jpy_rate'] = self.usd_jpy
        
        # Sort by ratio
        result_df = result_df.sort_values('ratio', ascending=False)
        
        return result_df, hist_data
    
    def save_results(
        self, 
        result_df: pd.DataFrame, 
        hist_data: Dict[str, pd.Series],
        output_dir: str = "output"
    ) -> str:
        """
        Save calculation results to files.
        
        Args:
            result_df: Results DataFrame
            hist_data: Historical data for correlation matrix
            output_dir: Output directory
            
        Returns:
            Path to output file
        """
        # Create output directory
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.basename(self.csv_file)
        
        # Save correlation matrix
        if hist_data:
            corr_df = self.calculate_correlation_matrix(hist_data)
            if corr_df is not None:
                corr_file = os.path.join(
                    output_dir, 
                    base_name.replace('.csv', f'_corr_{timestamp}.csv')
                )
                corr_df.to_csv(corr_file)
                print(f"Saved correlation matrix to {corr_file}")
        
        # Save results
        output_file = os.path.join(
            output_dir,
            base_name.replace('.csv', f'_result_{timestamp}.csv')
        )
        
        # Organize column order
        cols = [
            'ticker', 'name', 'shares', 'currency', 'price', 'value', 'value_jp', 'ratio',
            'PER', 'sigma', 'sharpe', 'dividend_yield', 'sector', 'industry', 'country', 'usd_jpy_rate'
        ]
        cols = [c for c in cols if c in result_df.columns]
        
        result_df[cols].to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
        return output_file
    
    def run(self) -> None:
        """Execute portfolio calculation workflow."""
        if not os.path.exists(self.csv_file):
            print(f"Error: File {self.csv_file} not found.")
            return
        
        print(f"Starting portfolio calculation: {self.csv_file}")
        df = pd.read_csv(self.csv_file)
        
        # Calculate portfolio
        result_df, hist_data = self.calculate_portfolio(df)
        
        # Display results
        pd.options.display.float_format = '{:.2f}'.format
        print("\n=== Portfolio Details ===")
        display_cols = ['ticker', 'name', 'shares', 'price', 'value', 'value_jp', 'ratio', 'PER', 'sharpe']
        display_cols = [c for c in display_cols if c in result_df.columns]
        print(result_df[display_cols].to_string(index=False))
        
        total_value = result_df['value'].sum()
        total_value_jp = result_df['value_jp'].sum()
        print(f"\nTotal Value (USD): ${total_value:,.2f}")
        print(f"Total Value (JPY): ¥{total_value_jp:,.0f}")
        print(f"Exchange Rate: 1 USD = {self.usd_jpy:.2f} JPY")
        
        # Save results
        self.save_results(result_df, hist_data)
        
        # Save cache
        self.cache_manager.save()
        print("Cache saved")
