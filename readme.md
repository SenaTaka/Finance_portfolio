# portfolio_calculator.py

> 📘 **日本語ドキュメント** | [README_JP.md](README_JP.md) | [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md) | [MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)

## Overview
This script reads a CSV file (containing tickers and share counts), fetches current stock prices and financial metrics from Yahoo Finance, and calculates portfolio valuations and allocation ratios.

## Features
1. **Stock Price & Exchange Rate Fetching**: Uses `yfinance` to get the latest stock prices and USD/JPY exchange rates.
   - For Japan stocks (`.T` suffix), it fetches Japanese company names from Yahoo! Finance (Japan).
2. **Metrics Calculation**:
   - **PER (Price to Earnings Ratio)**: Fetches `trailingPE`.
   - **Volatility (σ)**: Calculates annualized standard deviation from daily returns over the past year (252 trading days).
   - **Sharpe Ratio**: Uses dynamically fetched US 10-year Treasury yield (^TNX) as the risk-free rate.
3. **Portfolio Analysis**:
   - Calculates valuation for each stock (in USD and JPY).
   - Calculates allocation ratio of each stock relative to the total portfolio.
   - Sorts by allocation ratio in descending order.
4. **Result Saving**: Saves calculation results to a timestamped CSV file.
5. **Caching**: Caches data to reduce API request load.
   - **Metadata (company name, sector, industry, country)**: Cached for 1 week
   - **Volatility & Sharpe Ratio**: Cached for 24 hours
   - **Stock Price**: Cached for 15 minutes
   - Cache is stored in `data/ticker_cache.json`.

## Requirements
The following Python libraries are required:
- pandas
- yfinance
- numpy
- scipy (for efficient frontier calculation)
- requests
- beautifulsoup4
- streamlit (for Web UI)
- plotly (for Web UI)

## Usage

```bash
python portfolio_calculator.py [csv_file] [--force-refresh]
```

If no arguments are provided, it defaults to reading `portfolio.csv`.
You can also specify other files like `portfolio_jp.csv`.

### Options
- `--force-refresh` or `-f`: Ignores cache and fetches all data from API.

### Examples
```bash
# Normal execution (uses cache)
python portfolio_calculator.py

# Ignore cache and full refresh
python portfolio_calculator.py --force-refresh

# Update Japan stocks portfolio
python portfolio_calculator.py portfolio_jp.csv
```

## Input File Format (CSV)
Prepare a CSV file with the following columns:

| ticker | shares |
|--------|--------|
| AAPL   | 10     |
| 7203.T | 100    |

* For Japan stocks, add `.T` suffix to the ticker code (e.g., Toyota: `7203.T`).
The script automatically detects the currency (USD/JPY) and calculates accordingly.

## Output
Upon execution, results are displayed in the console and saved as files:
- Location: `output/` directory
- Filename: `[original_filename]_result_YYYYMMDD_HHMMSS.csv`
- Added columns: `name`, `sector`, `price`, `PER`, `sigma`, `sharpe`, `value`, `value_jp`, `ratio`, `usd_jpy_rate`
- **Note**: `value_jp` (JPY valuation) is rounded to an integer.
- **Correlation Matrix**: Saved separately as `[original_filename]_corr_YYYYMMDD_HHMMSS.csv`.

## Web UI (Streamlit)
Calculation results can be visualized in a browser.

### Starting the UI
```bash
# Standard UI (file-based)
streamlit run portfolio_app.py

# V2 UI (modular with advanced features)
streamlit run portfolio_app_v2.py
```

### Core Features
- **Combined View**: By default, automatically combines the latest results from `portfolio.csv` (US stocks) and `portfolio_jp.csv` (Japan stocks) to display as a single portfolio.
- **Data Update**: Click the "Update Data" button in the sidebar to fetch and recalculate the latest information from `portfolio.csv` and `portfolio_jp.csv`.
  - **Caching**: Normal updates use cache to reduce API requests.
  - **Full Refresh Option**: Check the "Force full refresh" checkbox to ignore cache and fetch all data.
- **History View (US/JP History)**: Select "US History" or "JP History" in the sidebar to view and select past history files individually.
- **Advanced Analysis**:
  - **Sector Analysis**: Displays sector allocation in a pie chart.
  - **Risk/Return Analysis**: Shows a scatter plot of volatility (risk) vs Sharpe ratio (efficiency) to compare stock characteristics.
  - **Correlation Matrix**: Displays stock price correlation as a heatmap to verify diversification effects (when viewing individual files).
  - **Sharpe Optimized**: Provides portfolio optimization and rebalancing suggestions based on Sharpe ratio. Parameters (Sharpe/Volatility emphasis) can be adjusted.
- Displays portfolio allocation ratio (pie chart) and Sharpe ratio (bar chart).

### ✨ NEW: Advanced Features (V2 UI)

#### 🤖 Machine Learning Predictions
- AI-powered stock price forecasting using Random Forest models
- Next-day and 5-day price predictions
- Feature importance analysis showing which indicators matter most
- Portfolio-wide predictions with bullish/bearish signals
- Model performance metrics (R², MAE, training size)

#### ⚡ Real-time Updates
- Live price tracking with auto-refresh (60-second intervals)
- Manual refresh on-demand
- Day high/low and volume data
- Change indicators (up/down with percentages)
- Portfolio summary statistics

#### 📰 News & Sentiment Analysis
- Latest market news from Yahoo Finance
- AI-powered sentiment analysis (positive/negative/neutral)
- News feed with sentiment badges
- Portfolio-wide sentiment overview
- Stock-specific detailed analysis with confidence scores

**See [ADVANCED_FEATURES_GUIDE.md](ADVANCED_FEATURES_GUIDE.md) for detailed usage instructions.**

### Efficient Frontier (Modern Portfolio Theory)
Displays the efficient frontier based on Modern Portfolio Theory (MPT) and provides optimal portfolio allocation suggestions.

#### Features
- **Efficient Frontier Visualization**: Displays the relationship between portfolio risk (volatility) and return in a graph.
  - Distribution of randomly generated portfolios
  - Efficient frontier curve (red line)
  - Individual risk/return position for each stock
  
- **Optimal Portfolio Suggestions**:
  - **Maximum Sharpe Ratio Portfolio**: Allocation with the highest risk-adjusted return
  - **Minimum Volatility Portfolio**: Allocation with the lowest risk
  - **Equal Weight Portfolio**: Equal allocation to all assets
  - **Current Portfolio**: Allocation based on current holdings

- **Rebalancing Recommendations**: Provides specific trade amounts to transition from the current portfolio to the optimal portfolio.

#### How to Use
1. Click "Update Data" button to update data (requires price history data)
2. Review various portfolio suggestions in the "Efficient Frontier" section
3. Check specific trade amounts for optimal allocation in "Required Trades"

#### Technical Details
- Calculates expected returns and covariance matrix from 1 year of price data
- Mean-variance optimization using `scipy.optimize.minimize`
- Risk-free rate: US 10-year Treasury yield (dynamically fetched)

