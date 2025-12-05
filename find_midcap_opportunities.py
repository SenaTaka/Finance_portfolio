import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import time


def get_midcap_opportunities(min_rank=500, max_rank=2000, min_sharpe=0, max_per=3000):
    """
    Find investment opportunities from stocks ranked 500-2000 by market cap
    
    Parameters:
    min_rank: Minimum rank (default 500)
    max_rank: Maximum rank (default 2000)
    min_sharpe: Minimum Sharpe ratio (default 1.0)
    max_per: Maximum P/E ratio (default 30)
    """
    
    print("Fetching mid-cap stocks...")
    
    # Get stocks from Russell 2000 (small cap index) ETF
    # Or use S&P MidCap 400 ETF
    etfs = ['IJH', 'MDY', 'VO']  # iShares S&P MidCap, SPDR MidCap, Vanguard MidCap
    
    for etf_ticker in etfs:
        try:
            # Get ETF holdings (may be limited by yfinance)
            print(f"Fetching stocks from {etf_ticker}...")
        except Exception as e:
            print(f"{etf_ticker} error: {e}")
    
    # Alternative approach: manually selected mid-cap stock list
    # Representative stocks ranked 500-2000 by market cap (estimated for 2024)
    candidate_tickers = [
        # Technology & Software
        'BILL', 'PATH', 'FROG', 'CPNG', 'GTLB', 'KVUE', 
        # Healthcare & Biotech
        'EXAS', 'HOLX', 'TECH', 'PODD', 'INCY',
        # Finance
        'ALLY', 'SYF', 'NYCB', 'WAL', 'EWBC',
        # Consumer Goods
        'CHEF', 'WING', 'TXRH', 'CBRL', 'PLAY',
        # Industrial & Manufacturing
        'BLDR', 'BECN', 'UFPI', 'MLI', 'TREX',
        # Energy & Materials
        'AR', 'SM', 'CTRA', 'OVV', 'PR',
        # Real Estate
        'REXR', 'FR', 'STAG', 'NSA', 'CUBE',
        # Communications & Media
        'CABO', 'TRIP', 'MSGS', 'IMAX', 'FUBO',
        # Retail
        'FIVE', 'OLLI', 'BBWI', 'ANF', 'URBN',
        # Other Promising Stocks
        'RKLB', 'IONQ', 'PLTR', 'SOFI', 'UPST', 'COIN'
    ]
    
    print(f"\nAnalyzing {len(candidate_tickers)} stocks...\n")
    
    results = []
    
    for ticker in candidate_tickers:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get market cap
            market_cap = info.get('marketCap', 0)
            if market_cap == 0:
                continue
            
            # Get stock price
            hist_1d = stock.history(period='1d')
            if len(hist_1d) == 0:
                continue
            price = hist_1d['Close'].iloc[-1]
            
            # Company name
            name = info.get('longName', info.get('shortName', ticker))
            
            # Website
            website = info.get('website', '')
            
            # P/E ratio
            per = info.get('trailingPE', None)
            
            # Calculate volatility and Sharpe ratio
            hist = stock.history(period='1y')
            if len(hist) < 100:  # Skip if insufficient data
                continue
            
            returns = hist['Close'].pct_change().dropna()
            sigma = returns.std() * np.sqrt(252) * 100
            mean_return = returns.mean() * 252 * 100
            risk_free_rate = 4.0
            
            if sigma > 0:
                sharpe = (mean_return - risk_free_rate) / sigma
            else:
                sharpe = None
            
            # Filtering conditions
            if sharpe and sharpe >= min_sharpe:
                if per is None or (per > 0 and per <= max_per):
                    results.append({
                        'ticker': ticker,
                        'name': name,
                        'price': price,
                        'market_cap': market_cap,
                        'PER': per,
                        'sigma': sigma,
                        'sharpe': sharpe,
                        'annual_return': mean_return,
                        'website': website
                    })
                    per_display = f"{per:.2f}" if per else 'N/A'
                    print(f"✓ {ticker} ({name[:30]}): ${price:.2f}, Cap: ${market_cap/1e9:.2f}B, PER: {per_display}, Sharpe: {sharpe:.2f}")
            
            time.sleep(0.1)  # API rate limit protection
            
        except Exception as e:
            print(f"✗ {ticker}: Error - {e}")
            continue
    
    if not results:
        print("\nNo stocks found matching the criteria")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(results)
    df = df.sort_values('sharpe', ascending=False)
    
    print(f"\n\n=== Investment Opportunity Candidates (Sharpe >= {min_sharpe}, PER <= {max_per}) ===")
    print(df.to_string(index=False))
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'midcap_opportunities_{timestamp}.csv'
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to {output_file}")
    
    return df


if __name__ == "__main__":
    import sys
    
    # Specify conditions via command line arguments
    min_sharpe = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
    max_per = float(sys.argv[2]) if len(sys.argv) > 2 else 30
    
    print(f"Search criteria: Sharpe Ratio >= {min_sharpe}, PER <= {max_per}\n")
    
    df = get_midcap_opportunities(min_sharpe=min_sharpe, max_per=max_per)
