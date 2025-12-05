import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import json
import argparse

# Cache configuration
CACHE_DIR = "data"
CACHE_FILE = os.path.join(CACHE_DIR, "ticker_cache.json")
# Cache TTL settings (in hours)
CACHE_TTL_METADATA = 24 * 7  # 1 week for sector, industry, country, name
CACHE_TTL_VOLATILITY = 24  # 1 day for volatility/sharpe calculations
CACHE_TTL_PRICE = 0.25  # 15 minutes for price data


def load_cache():
    """Load cache from file."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {}


def save_cache(cache):
    """Save cache to file."""
    if not os.path.exists(CACHE_DIR):
        os.makedirs(CACHE_DIR)
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def is_cache_valid(cached_time_str, ttl_hours):
    """Check if cached data is still valid based on TTL."""
    if not cached_time_str:
        return False
    try:
        cached_time = datetime.fromisoformat(cached_time_str)
        return datetime.now() - cached_time < timedelta(hours=ttl_hours)
    except (ValueError, TypeError):
        return False


class PortfolioCalculator:
    def __init__(self, csv_file, force_refresh=False):
        self.csv_file = csv_file
        self.usd_jpy = 1.0
        self.force_refresh = force_refresh
        self.cache = load_cache()
        self.risk_free_rate = 4.0  # Default fallback

    def get_risk_free_rate(self):
        """Get the US 10-year Treasury yield (^TNX) as the risk-free rate"""
        try:
            ticker = "^TNX"
            tnx = yf.Ticker(ticker)
            # Get 1 day history
            hist = tnx.history(period="1d")
            if not hist.empty:
                # ^TNX is in percent (e.g. 4.3), so divide by 100
                self.risk_free_rate = hist['Close'].iloc[-1]
                print(f"Current risk-free rate (^TNX): {self.risk_free_rate:.2f}%")
            else:
                print("Failed to fetch risk-free rate. Using default value (4.0%).")
        except Exception as e:
            print(f"Risk-free rate fetch error: {e}")
            # Keep default

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
                # "トヨタ自動車(株)【7203】..." から社名を抽出
                match = re.search(r'^(.*?)【', title)
                if match:
                    return match.group(1).strip()
        except Exception:
            pass
        return None

    def get_ticker_data(self, ticker):
        """Get individual stock data (with caching)"""
        try:
            cached = self.cache.get(ticker, {})
            now_str = datetime.now().isoformat()
            
            # Determine what needs to be fetched
            need_metadata = self.force_refresh or not is_cache_valid(
                cached.get('metadata_updated'), CACHE_TTL_METADATA
            )
            need_volatility = self.force_refresh or not is_cache_valid(
                cached.get('volatility_updated'), CACHE_TTL_VOLATILITY
            )
            need_price = self.force_refresh or not is_cache_valid(
                cached.get('price_updated'), CACHE_TTL_PRICE
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
                    # Use dynamic risk free rate
                    risk_free_rate = self.risk_free_rate
                    if sigma > 0:
                        sharpe = (mean_return - risk_free_rate) / sigma
                
                # Update cache with volatility data
                cached['sigma'] = sigma
                cached['sharpe'] = sharpe
                cached['volatility_updated'] = now_str
                # Store history as list for correlation matrix
                cached['history'] = hist['Close'].tolist()
                cached['history_index'] = [d.isoformat() for d in hist.index]
            elif need_price:
                # Only fetch recent price data
                print(f"  {ticker}: Fetching current price...")
                hist = stock.history(period='1d')
                if hist.empty:
                    # Fall back to cached price if available
                    current_price = cached.get('price')
                else:
                    current_price = hist['Close'].iloc[-1]
            else:
                # Use cached price
                print(f"  {ticker}: Using cached data")
                current_price = cached.get('price')
            
            # Update price cache
            if current_price is not None:
                cached['price'] = current_price
                cached['price_updated'] = now_str
            
            # Fetch metadata only if needed
            if need_metadata:
                print(f"  {ticker}: Fetching metadata...")
                info = stock.info
                
                # PER and dividend yield (can change but cached with metadata)
                cached['PER'] = info.get('trailingPE')
                dividend_yield = info.get('dividendYield')
                if dividend_yield is not None:
                    dividend_yield = dividend_yield * 100
                cached['dividend_yield'] = dividend_yield
                cached['currency'] = info.get('currency', 'USD')
                cached['sector'] = info.get('sector')
                cached['industry'] = info.get('industry')
                cached['country'] = info.get('country')
                
                # 社名取得
                name = None
                if ticker.endswith('.T'):
                    name = self.get_japanese_name(ticker)
                if not name:
                    name = info.get('longName') or info.get('shortName') or ticker
                cached['name'] = name
                cached['metadata_updated'] = now_str
            
            # Update main cache
            self.cache[ticker] = cached
            
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
            
            # Reconstruct history for correlation matrix if available
            if cached.get('history') and cached.get('history_index'):
                try:
                    result['history'] = pd.Series(
                        cached['history'],
                        index=pd.to_datetime(cached['history_index'])
                    )
                except (ValueError, TypeError) as e:
                    print(f"  {ticker}: Failed to reconstruct history data: {e}")
                    result['history'] = None
            
            return result
            
        except Exception as e:
            print(f"{ticker}: データ取得エラー - {e}")
            return None

    def run(self):
        if not os.path.exists(self.csv_file):
            print(f"Error: File {self.csv_file} not found.")
            return

        print(f"Starting portfolio calculation: {self.csv_file}")
        df = pd.read_csv(self.csv_file)
        
        # 為替レート取得
        self.get_exchange_rate()
        # リスクフリーレート取得
        self.get_risk_free_rate()
        
        results = []
        hist_data = {}
        
        for index, row in df.iterrows():
            ticker = row['ticker']
            shares = row['shares']
            
            print(f"Fetching data: {ticker}...")
            data = self.get_ticker_data(ticker)
            
            if data:
                data['ticker'] = ticker
                data['shares'] = shares
                
                # ヒストリカルデータを保存（相関行列用）
                if data.get('history') is not None:
                    hist_data[ticker] = data.pop('history')
                
                # 通貨に応じた計算
                price = data['price']
                currency = data.get('currency', 'USD')
                
                if currency == 'JPY':
                    # 日本円の場合
                    val_jp = price * shares
                    val_usd = val_jp / self.usd_jpy if self.usd_jpy > 0 else 0
                else:
                    # 米ドル（またはその他）の場合、とりあえずUSD扱いとして計算
                    # 必要なら他の通貨対応もここに追加
                    val_usd = price * shares
                    val_jp = val_usd * self.usd_jpy
                
                data['value'] = val_usd
                data['value_jp'] = int(val_jp)
                results.append(data)
            else:
                # エラー時の空データ
                results.append({
                    'ticker': ticker, 'shares': shares, 
                    'price': 0, 'PER': None, 'sigma': None, 'sharpe': None, 
                    'dividend_yield': None,
                    'value': 0, 'value_jp': 0, 'currency': 'N/A', 'name': 'N/A', 'sector': 'Unknown'
                })

        result_df = pd.DataFrame(results)
        
        # 相関行列の計算と保存
        output_dir = "output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        base_name = os.path.basename(self.csv_file)
        
        if hist_data:
            try:
                price_df = pd.DataFrame(hist_data)
                # Daily return correlation
                corr_df = price_df.pct_change().dropna().corr()
                corr_file = os.path.join(output_dir, base_name.replace('.csv', f'_corr_{timestamp}.csv'))
                corr_df.to_csv(corr_file)
                print(f"Saved correlation matrix to {corr_file}")
            except Exception as e:
                print(f"Failed to calculate correlation matrix: {e}")
        
        # 比率計算
        total_value = result_df['value'].sum()
        if total_value > 0:
            result_df['ratio'] = (result_df['value'] / total_value * 100).round(2)
        else:
            result_df['ratio'] = 0

        # Sort
        result_df = result_df.sort_values('ratio', ascending=False)
        
        # Display
        pd.options.display.float_format = '{:.2f}'.format
        print("\n=== Portfolio Details ===")
        # Display column selection
        display_cols = ['ticker', 'name', 'shares', 'price', 'value', 'value_jp', 'ratio', 'PER', 'sharpe']
        # Exclude columns that don't exist
        display_cols = [c for c in display_cols if c in result_df.columns]
        print(result_df[display_cols].to_string(index=False))
        
        total_value_jp = result_df['value_jp'].sum()
        print(f"\nTotal Value (USD): ${total_value:,.2f}")
        print(f"Total Value (JPY): ¥{total_value_jp:,.0f}")
        print(f"Exchange Rate: 1 USD = {self.usd_jpy:.2f} JPY")

        # Save
        output_file = os.path.join(output_dir, base_name.replace('.csv', f'_result_{timestamp}.csv'))
        
        # Add exchange rate as metadata
        result_df['usd_jpy_rate'] = self.usd_jpy
        
        # Organize column order
        cols = [
            'ticker', 'name', 'shares', 'currency', 'price', 'value', 'value_jp', 'ratio',
            'PER', 'sigma', 'sharpe', 'dividend_yield', 'sector', 'industry', 'country', 'usd_jpy_rate'
        ]
        # Only include columns that exist
        cols = [c for c in cols if c in result_df.columns]
        
        result_df[cols].to_csv(output_file, index=False)
        print(f"\nResults saved to {output_file}")
        
        # Save cache
        save_cache(self.cache)
        print("Cache saved")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate portfolio valuations and metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python portfolio_calculator.py                    # Use portfolio.csv
  python portfolio_calculator.py portfolio_jp.csv  # Use Japan stocks portfolio
  python portfolio_calculator.py --force-refresh   # Ignore cache and full refresh
"""
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="portfolio.csv",
        help="Input CSV file (default: portfolio.csv)"
    )
    parser.add_argument(
        "-f", "--force-refresh",
        action="store_true",
        help="Ignore cache and fetch all data from API"
    )
    
    args = parser.parse_args()
    calculator = PortfolioCalculator(args.csv_file, force_refresh=args.force_refresh)
    calculator.run()
