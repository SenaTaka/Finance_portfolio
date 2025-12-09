# Finance Portfolio Management System

A comprehensive, modular portfolio management system with support for portfolio valuation, optimization, and analysis using Modern Portfolio Theory.

> 📘 **日本語ドキュメント** | [README_JP.md](README_JP.md) | [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md) | [MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)

## ⚠️ Important: New Modular Architecture

This project has been refactored with a modular architecture for better scalability and maintainability. See [ARCHITECTURE.md](ARCHITECTURE.md) for details and [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for migration instructions.

## 🌟 Key Features

- **Portfolio Valuation**: Track multiple portfolios (US and Japan stocks)
- **Real-time Data**: Fetch latest stock prices and metrics from Yahoo Finance
- **Smart Caching**: TTL-based caching reduces API calls
- **Risk Analysis**: Calculate volatility, Sharpe ratio, and correlation
- **Portfolio Optimization**: Modern Portfolio Theory-based optimization
- **Scenario Analysis**: Stress testing and crash scenario modeling
- **Web UI**: Interactive Streamlit-based dashboard
- **Mobile-Friendly**: Responsive design for all devices

## 📁 Project Structure

```
Finance_portfolio/
├── src/                          # Main source code (NEW!)
│   ├── core/                     # Business logic
│   ├── data/                     # Data access layer
│   ├── analysis/                 # Analysis modules
│   ├── ui/                       # UI components
│   └── utils/                    # Utilities
├── tests/                        # Test files
├── data/                         # Cache storage
├── output/                       # Results output
├── portfolio.csv                 # US portfolio input
├── portfolio_jp.csv              # Japan portfolio input
├── portfolio_app.py              # Streamlit web app
└── requirements.txt              # Dependencies
```

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/SenaTaka/Finance_portfolio.git
cd Finance_portfolio

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Calculate portfolio (using new modular architecture)
python portfolio_calculator_new.py portfolio.csv

# Or use the legacy entry point (still works)
python portfolio_calculator.py portfolio.csv

# Force refresh (ignore cache)
python portfolio_calculator_new.py portfolio.csv --force-refresh

# Start web UI
streamlit run portfolio_app.py
```

## 📊 Portfolio Input Format

Create a CSV file with your portfolio:

```csv
ticker,shares
AAPL,10
GOOGL,5
7203.T,100
```

**Notes:**
- For Japan stocks, add `.T` suffix (e.g., Toyota: `7203.T`)
- The system automatically detects currency (USD/JPY)

## 🏗️ Modular Architecture

### Core Components

1. **Data Layer** (`src/data/`)
   - `CacheManager`: Smart caching with TTL
   - `StockDataFetcher`: Yahoo Finance integration

2. **Core Layer** (`src/core/`)
   - `PortfolioCalculator`: Main calculation engine

3. **Analysis Layer** (`src/analysis/`)
   - `efficient_frontier.py`: Modern Portfolio Theory
   - `sharpe_optimized.py`: Sharpe ratio optimization
   - `crash_scenario_analysis.py`: Stress testing

4. **UI Layer** (`src/ui/`)
   - `chart_utils.py`: Reusable charts
   - `data_loader.py`: Data loading utilities

5. **Utils Layer** (`src/utils/`)
   - `config.py`: Configuration management
   - `file_utils.py`: File operations
   - `region_classifier.py`: Geographic classification

### Benefits

✅ **Modular**: Easy to understand and modify
✅ **Testable**: Components can be tested independently
✅ **Extensible**: Add new features without breaking existing code
✅ **Maintainable**: Clear separation of concerns
✅ **Scalable**: Ready for large-scale development

## 📈 Features in Detail

### Portfolio Valuation

- Real-time stock prices via Yahoo Finance
- Multi-currency support (USD, JPY)
- Exchange rate conversion
- Allocation ratio calculation

### Risk Metrics

- **Volatility (σ)**: Annualized standard deviation
- **Sharpe Ratio**: Risk-adjusted return metric
- **Correlation Matrix**: Stock price correlation analysis
- **Beta**: Market sensitivity (in scenario analysis)

### Portfolio Optimization

- **Efficient Frontier**: Visualize risk-return tradeoffs
- **Maximum Sharpe Portfolio**: Optimal risk-adjusted allocation
- **Minimum Volatility Portfolio**: Lowest-risk allocation
- **Backtesting**: Historical performance analysis

### Web Dashboard

- Portfolio allocation visualization (pie charts)
- Sector and regional analysis
- Risk vs return scatter plots
- Correlation heatmaps
- Performance comparison vs S&P 500
- Rebalancing recommendations
- Mobile-optimized interface

### Caching System

Intelligent caching reduces API calls:
- **Metadata**: Cached for 1 week
- **Volatility/Sharpe**: Cached for 24 hours
- **Stock Prices**: Cached for 15 minutes

## 🔧 Configuration

Configuration is centralized in `src/utils/config.py`:

```python
from src.utils import Config

# Access settings
print(Config.DATA_DIR)  # "data"
print(Config.CACHE_TTL_PRICE)  # 0.25 hours (15 min)

# Modify settings
Config.DEFAULT_RISK_FREE_RATE = 3.5
```

## 📚 API Examples

### Using the New Architecture

```python
# Portfolio calculation
from src.core import PortfolioCalculator

calculator = PortfolioCalculator("portfolio.csv")
calculator.run()

# Data fetching
from src.data import StockDataFetcher

fetcher = StockDataFetcher()
price = fetcher.get_stock_price("AAPL")
history = fetcher.get_stock_history("AAPL", period="1y")

# Analysis
from src.analysis import calculate_efficient_frontier

frontier_df = calculate_efficient_frontier(
    expected_returns, 
    cov_matrix, 
    n_points=50
)

# UI utilities
from src.ui import chart_utils, DataLoader

loader = DataLoader()
df, files = loader.load_combined_latest()

fig = chart_utils.create_pie_chart(
    data=df,
    values_col="value_jp",
    names_col="ticker",
    title="Portfolio Allocation"
)
```

## 🧪 Testing

```bash
# Run all tests
python test_efficient_frontier.py
python test_cache.py
python test_risk_free_rate.py

# Test imports
python -c "from src.core import PortfolioCalculator; print('✓ OK')"
```

## 📖 Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture details
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - Migration from old structure
- Module docstrings - API documentation for each module

## 🔄 Migration from Old Structure

The old structure is still supported for backward compatibility:

```python
# Old imports (still work)
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier

# New imports (recommended)
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier
```

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for complete migration instructions.

## 🛣️ Roadmap

### Phase 1: Core Refactoring ✅
- [x] Modular architecture
- [x] Separated concerns
- [x] Configuration management
- [x] Backward compatibility

### Phase 2: UI Refactoring (Next)
- [ ] Split portfolio_app.py into pages
- [ ] Component-based UI
- [ ] Improved state management

### Phase 3: Database Integration
- [ ] Replace JSON cache with database
- [ ] Historical tracking
- [ ] Multiple portfolio support

### Phase 4: Advanced Features
- [ ] Machine learning predictions
- [ ] Real-time updates (WebSocket)
- [ ] News and sentiment analysis

### Phase 5: API Layer
- [ ] REST API
- [ ] Authentication
- [ ] Rate limiting

## 🤝 Contributing

When contributing:

1. Follow the modular architecture
2. Add tests for new features
3. Update documentation
4. Maintain backward compatibility

## 📄 License

[Add your license here]

## 👥 Authors

[Add author information]

## 🙏 Acknowledgments

- Yahoo Finance API (via yfinance)
- Modern Portfolio Theory principles
- Streamlit framework

## 📞 Support

For issues or questions:
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) and [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
2. Review module docstrings
3. Open an issue on GitHub

---

**Note**: This project has been refactored with a modular architecture. All old functionality remains for backward compatibility while new code benefits from improved structure and extensibility.
