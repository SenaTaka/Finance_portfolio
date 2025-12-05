import yfinance as yf
import sys

def get_stock_data(ticker, period='1mo'):
    """Get stock data including time-series and P/E ratio."""
    try:
        stock = yf.Ticker(ticker)
        
        # Get historical data
        hist_data = stock.history(period=period)
        
        # Get current info including P/E ratio
        info = stock.info
        
        return {
            'history': hist_data,
            'current_price': hist_data['Close'].iloc[-1] if not hist_data.empty else None,
            'pe_ratio': info.get('trailingPE', 'N/A'),
            'forward_pe': info.get('forwardPE', 'N/A'),
            'company_name': info.get('longName', ticker)
        }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        ticker = sys.argv[1].strip().upper()
    else:
        ticker = input("Enter ticker symbol: ").strip().upper()
    
    # Get data for the last month
    data = get_stock_data(ticker, period='1mo')
    
    if data and data['current_price']:
        print(f"\n{'='*50}")
        print(f"{data['company_name']} ({ticker})")
        print(f"{'='*50}")
        print(f"Current Price: ${data['current_price']:.2f}")
        print(f"P/E Ratio (Trailing): {data['pe_ratio']}")
        print(f"P/E Ratio (Forward): {data['forward_pe']}")
        print(f"\nHistorical Data (last {len(data['history'])} trading days):")
        print(f"{'='*50}")
        print(data['history'][['Open', 'High', 'Low', 'Close', 'Volume']].to_string())
    else:
        print(f"\nCould not retrieve data for {ticker}")
