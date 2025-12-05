import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np


def get_risk_free_rate():
    """Get the US 10-year Treasury yield (^TNX) as the risk-free rate"""
    try:
        ticker = "^TNX"
        tnx = yf.Ticker(ticker)
        hist = tnx.history(period="1d")
        if not hist.empty:
            rate = hist['Close'].iloc[-1]
            print(f"Current risk-free rate (^TNX): {rate:.2f}%")
            return rate
    except Exception as e:
        print(f"Risk-free rate fetch error: {e}")
    return 4.0  # Default fallback


def calculate_portfolio(csv_file):
    """
    Read ticker and share count from CSV file and calculate stock prices and portfolio ratios (Japan stocks supported)
    
    Parameters:
    csv_file: Path to CSV file (columns: ticker, shares)
    * For Japan stocks, add .T to the stock code (e.g., 7203.T for Toyota)
    """
    # Read CSV file
    df = pd.read_csv(csv_file)
    
    # Get risk-free rate
    risk_free_rate = get_risk_free_rate()

    # Get stock price, PER, volatility (sigma), and Sharpe ratio
    prices = []
    pers = []
    sigmas = []
    sharpe_ratios = []
    company_names = []
    
    for ticker in df['ticker']:
        try:
            stock = yf.Ticker(ticker)
            
            # Get company name
            info = stock.info
            name = info.get('longName', info.get('shortName', ticker))
            company_names.append(name)
            
            # Get stock price
            hist_1d = stock.history(period='1d')
            if len(hist_1d) > 0:
                price = hist_1d['Close'].iloc[-1]
            else:
                price = 0
            prices.append(price)
            
            # Get PER
            per = info.get('trailingPE', None)
            # For Japan stocks, also try forwardPE
            if per is None:
                per = info.get('forwardPE', None)
            pers.append(per)
            
            # Calculate volatility (sigma) and Sharpe ratio from 1 year of data
            hist = stock.history(period='1y')
            if len(hist) > 1:
                returns = hist['Close'].pct_change().dropna()
                # Annualize daily return standard deviation (252 trading days)
                sigma = returns.std() * np.sqrt(252) * 100  # Percent display
                sigmas.append(sigma)
                
                # Calculate Sharpe ratio
                mean_return = returns.mean() * 252 * 100  # Annualized return (%)
                # risk_free_rate is now dynamic
                if sigma > 0:
                    sharpe = (mean_return - risk_free_rate) / sigma
                    sharpe_ratios.append(sharpe)
                else:
                    sharpe_ratios.append(None)
                    sharpe = None
            else:
                sigmas.append(None)
                sharpe_ratios.append(None)
                sigma = None
                sharpe = None
            
            per_str = f"{per:.2f}" if per else "N/A"
            sigma_str = f"{sigma:.2f}%" if sigma else "N/A"
            sharpe_str = f"{sharpe:.2f}" if sharpe else "N/A"
            
            # Determine currency by ticker suffix (.T for Japan stocks)
            currency = "¥" if ticker.endswith('.T') else "$"
            print(f"{ticker} ({name}): {currency}{price:.2f}, PER: {per_str}, σ: {sigma_str}, Sharpe: {sharpe_str}")
        except Exception as e:
            print(f"{ticker}: Error - {e}")
            company_names.append(ticker)
            prices.append(0)
            pers.append(None)
            sigmas.append(None)
            sharpe_ratios.append(None)
    
    # Insert company name as second column
    df.insert(1, 'name', company_names)
    df['price'] = prices
    df['PER'] = pers
    df['sigma'] = sigmas
    df['sharpe'] = sharpe_ratios
    
    # Calculate valuation
    df['value'] = df['shares'] * df['price']
    
    # Total portfolio value
    total_value = df['value'].sum()
    
    # Calculate ratio
    df['ratio'] = (df['value'] / total_value * 100).round(2)
    
    # Sort by ratio in descending order
    df = df.sort_values('ratio', ascending=False)
    
    # Display results
    print("\n=== Portfolio Details ===")
    print(df.to_string(index=False))
    
    # Determine currency (handle mixed Japan and US stocks)
    has_jp = df['ticker'].str.endswith('.T').any()
    has_us = (~df['ticker'].str.endswith('.T')).any()
    
    if has_jp and has_us:
        print(f"\nTotal Value: ¥/$ {total_value:,.2f} (mixed)")
    elif has_jp:
        print(f"\nTotal Value: ¥{total_value:,.2f}")
    else:
        print(f"\nTotal Value: ${total_value:,.2f}")
    
    # Save results to CSV (with date and time)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = csv_file.replace('.csv', f'_result_{timestamp}.csv')
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    return df


if __name__ == "__main__":
    # Usage example
    import sys
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = "portfolio_jp.csv"
    
    calculate_portfolio(csv_file)
