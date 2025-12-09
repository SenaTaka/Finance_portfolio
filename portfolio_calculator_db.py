"""Portfolio calculator with database backend."""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import argparse

# Import database components
from src.database import DatabaseCacheManager, init_db, PortfolioManager


class PortfolioCalculatorDB:
    """Portfolio calculator using database for cache and history tracking."""
    
    def __init__(self, csv_file, force_refresh=False, portfolio_name=None):
        """Initialize portfolio calculator with database backend.
        
        Args:
            csv_file: Path to CSV file with portfolio holdings
            force_refresh: If True, ignore cache and fetch fresh data
            portfolio_name: Name for the portfolio (defaults to filename)
        """
        self.csv_file = csv_file
        self.usd_jpy = 1.0
        self.force_refresh = force_refresh
        self.risk_free_rate = 4.0  # Default fallback
        
        # Initialize database
        init_db()
        
        # Create cache manager
        self.cache_manager = DatabaseCacheManager()
        
        # Create portfolio manager
        self.portfolio_manager = PortfolioManager()
        
        # Determine portfolio name
        if portfolio_name is None:
            portfolio_name = os.path.splitext(os.path.basename(csv_file))[0]
        self.portfolio_name = portfolio_name
        
        # Get or create portfolio
        self.portfolio = self.portfolio_manager.get_portfolio_by_name(portfolio_name)
        if self.portfolio is None:
            self.portfolio = self.portfolio_manager.create_portfolio(
                portfolio_name, 
                f"Portfolio from {csv_file}"
            )
    
    def get_risk_free_rate(self):
        """Get the US 10-year Treasury yield (^TNX) as the risk-free rate"""
        try:
            ticker = "^TNX"
            tnx = yf.Ticker(ticker)
            hist = tnx.history(period="1d")
            if not hist.empty:
                raw_rate = hist['Close'].iloc[-1]
                # ^TNX is quoted 10x (e.g. 42.5 for 4.25%), so normalize to percent
                rate = raw_rate / 10 if raw_rate > 20 else raw_rate
                self.risk_free_rate = rate
                print(f"現在のリスクフリーレート(^TNX): {self.risk_free_rate:.2f}%")
            else:
                print("Failed to fetch risk-free rate. Using default value (4.0%).")
        except Exception as e:
            print(f"Risk-free rate fetch error: {e}")
    
    def get_exchange_rate(self):
        """Get USD/JPY exchange rate"""
        try:
            ticker = "JPY=X"
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1d")
            if not hist.empty:
                self.usd_jpy = hist['Close'].iloc[-1]
                print(f"Current USD/JPY rate: {self.usd_jpy:.2f} JPY")
            else:
                print("Failed to fetch exchange rate. Using 100 JPY per USD.")
                self.usd_jpy = 100.0
        except Exception as e:
            print(f"Exchange rate fetch error: {e}")
            self.usd_jpy = 100.0
    
    def get_japanese_name(self, ticker):
        """Get Japanese company name from Yahoo! Finance (Japan)"""
        try:
            url = f"https://finance.yahoo.co.jp/quote/{ticker}"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.title.text
                match = re.search(r'^(.*?)【', title)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass
        return None
    
    def get_ticker_data(self, ticker):
        """Get individual stock data (with database caching)"""
        try:
            cached = self.cache_manager.get_ticker(ticker) or {}
            now_str = datetime.now().isoformat()
            
            # Determine what needs to be fetched
            need_metadata = self.force_refresh or not self.cache_manager.is_cache_valid(
                cached.get('metadata_updated'), self.cache_manager.CACHE_TTL_METADATA
            )
            need_volatility = self.force_refresh or not self.cache_manager.is_cache_valid(
                cached.get('volatility_updated'), self.cache_manager.CACHE_TTL_VOLATILITY
            )
            need_price = self.force_refresh or not self.cache_manager.is_cache_valid(
                cached.get('price_updated'), self.cache_manager.CACHE_TTL_PRICE
            )
            
            stock = yf.Ticker(ticker)
            hist = None
            current_price = None
            
            # Fetch historical data only if needed for volatility calculation
            if need_volatility:
                print(f"  {ticker}: Fetching 1 year of data...")
                hist = stock.history(period='1y')
                if hist.empty:
                    return None
                current_price = hist['Close'].iloc[-1]
                
                # Calculate volatility and sharpe
                sigma = None
                sharpe = None
                if len(hist) > 1:
                    returns = hist['Close'].pct_change().dropna()
                    sigma = returns.std() * np.sqrt(252) * 100
                    mean_return = returns.mean() * 252 * 100
                    risk_free_rate = self.risk_free_rate
                    if sigma > 0:
                        sharpe = (mean_return - risk_free_rate) / sigma
                    else:
                        sharpe = 0
                
                # Store in cache
                cached['sigma'] = sigma
                cached['sharpe'] = sharpe
                cached['volatility_updated'] = now_str
                
                # Store history for efficient frontier
                cached['history'] = hist['Close'].tolist()
                cached['history_index'] = [d.isoformat() for d in hist.index]
            
            # Fetch price only if needed
            if need_price and hist is None:
                print(f"  {ticker}: Fetching price...")
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            if current_price is not None:
                cached['price'] = current_price
                cached['price_updated'] = now_str
            else:
                current_price = cached.get('price')
            
            # Fetch metadata if needed
            if need_metadata:
                print(f"  {ticker}: Fetching metadata...")
                info = stock.info
                
                # Get Japanese name for .T tickers
                if ticker.endswith('.T'):
                    jp_name = self.get_japanese_name(ticker)
                    if jp_name:
                        cached['name'] = jp_name
                    else:
                        cached['name'] = info.get('longName', ticker)
                else:
                    cached['name'] = info.get('longName', ticker)
                
                cached['sector'] = info.get('sector', 'Unknown')
                cached['industry'] = info.get('industry', 'Unknown')
                cached['country'] = info.get('country', 'Unknown')
                cached['currency'] = info.get('currency', 'USD')
                cached['PER'] = info.get('trailingPE')
                cached['dividend_yield'] = info.get('dividendYield')
                cached['metadata_updated'] = now_str
            
            # Save updated cache to database
            self.cache_manager.set_ticker(ticker, cached)
            
            return {
                'ticker': ticker,
                'price': cached.get('price'),
                'name': cached.get('name', ticker),
                'sector': cached.get('sector', 'Unknown'),
                'industry': cached.get('industry', 'Unknown'),
                'country': cached.get('country', 'Unknown'),
                'currency': cached.get('currency', 'USD'),
                'PER': cached.get('PER'),
                'sigma': cached.get('sigma'),
                'sharpe': cached.get('sharpe'),
                'dividend_yield': cached.get('dividend_yield'),
            }
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
            return None
    
    def run(self):
        """Run portfolio calculation and save results"""
        print(f"Loading portfolio from {self.csv_file}...")
        df = pd.read_csv(self.csv_file)
        
        # Update portfolio holdings in database
        holdings = df[['ticker', 'shares']].to_dict('records')
        self.portfolio_manager.set_holdings(self.portfolio.id, holdings)
        
        # Fetch rates
        self.get_risk_free_rate()
        self.get_exchange_rate()
        
        print("Fetching ticker data...")
        results = []
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            shares = row['shares']
            
            ticker_data = self.get_ticker_data(ticker)
            if ticker_data is None:
                continue
            
            price = ticker_data['price']
            if price is None:
                print(f"  {ticker}: No price available, skipping")
                continue
            
            value = price * shares
            value_jp = value * self.usd_jpy
            
            results.append({
                'ticker': ticker,
                'name': ticker_data['name'],
                'shares': shares,
                'currency': ticker_data['currency'],
                'price': price,
                'PER': ticker_data['PER'],
                'sigma': ticker_data['sigma'],
                'sharpe': ticker_data['sharpe'],
                'dividend_yield': ticker_data['dividend_yield'],
                'value': value,
                'value_jp': round(value_jp),
                'usd_jpy_rate': self.usd_jpy,
                'sector': ticker_data['sector'],
                'industry': ticker_data['industry'],
                'country': ticker_data['country'],
            })
        
        result_df = pd.DataFrame(results)
        
        if result_df.empty:
            print("No data to process")
            return
        
        # Calculate allocation ratios
        total_value_jp = result_df['value_jp'].sum()
        result_df['ratio'] = (result_df['value_jp'] / total_value_jp * 100).round(2)
        result_df = result_df.sort_values('ratio', ascending=False)
        
        # Save to output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(os.path.basename(self.csv_file))[0]
        output_file = f"output/{base_name}_result_{timestamp}.csv"
        
        os.makedirs('output', exist_ok=True)
        result_df.to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
        # Save to portfolio history
        total_value_usd = result_df['value'].sum()
        holdings_snapshot = result_df.to_dict('records')
        self.portfolio_manager.add_history_snapshot(
            self.portfolio.id,
            total_value_usd,
            total_value_jp,
            self.usd_jpy,
            holdings_snapshot
        )
        print(f"Snapshot saved to portfolio history")
        
        # Calculate and save correlation matrix if we have enough data
        tickers_with_history = []
        for ticker in result_df['ticker']:
            cached = self.cache_manager.get_ticker(ticker)
            if cached and 'history' in cached:
                tickers_with_history.append(ticker)
        
        if len(tickers_with_history) >= 2:
            print("\nCalculating correlation matrix...")
            price_data = {}
            for ticker in tickers_with_history:
                cached = self.cache_manager.get_ticker(ticker)
                if cached and cached.get('history') and cached.get('history_index'):
                    try:
                        hist_series = pd.Series(
                            cached['history'],
                            index=pd.to_datetime(cached['history_index'])
                        )
                        price_data[ticker] = hist_series
                    except Exception:
                        pass
            
            if len(price_data) >= 2:
                price_df = pd.DataFrame(price_data)
                price_df = price_df.ffill().bfill()
                returns_df = price_df.pct_change().dropna()
                corr_matrix = returns_df.corr()
                
                corr_file = f"output/{base_name}_corr_{timestamp}.csv"
                corr_matrix.to_csv(corr_file)
                print(f"Correlation matrix saved to {corr_file}")
        
        # Display summary
        print("\n=== Portfolio Summary ===")
        print(f"Total Value: ${total_value_usd:,.2f} USD")
        print(f"Total Value: ¥{total_value_jp:,.0f} JPY")
        print(f"USD/JPY Rate: {self.usd_jpy:.2f}")
        print(f"\nTop 5 Holdings:")
        print(result_df[['ticker', 'name', 'value_jp', 'ratio']].head())
    
    def close(self):
        """Clean up resources"""
        self.cache_manager.close()
        self.portfolio_manager.close()


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(description='Portfolio Calculator with Database Backend')
    parser.add_argument('csv_file', nargs='?', default='portfolio.csv',
                       help='CSV file containing ticker and shares (default: portfolio.csv)')
    parser.add_argument('-f', '--force-refresh', action='store_true',
                       help='Force refresh all data from API (ignore cache)')
    parser.add_argument('-n', '--name', type=str,
                       help='Portfolio name (defaults to filename)')
    
    args = parser.parse_args()
    
    calculator = PortfolioCalculatorDB(args.csv_file, args.force_refresh, args.name)
    try:
        calculator.run()
    finally:
        calculator.close()


if __name__ == "__main__":
    main()
