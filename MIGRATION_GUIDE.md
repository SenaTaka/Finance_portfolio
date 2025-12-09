# Migration Guide to Modular Architecture

> 📘 **日本語版** | [MIGRATION_GUIDE_JP.md](MIGRATION_GUIDE_JP.md)

This guide helps you migrate from the old monolithic structure to the new modular architecture.

## What Changed?

### Directory Structure

**Before:**
```
Finance_portfolio/
├── portfolio_calculator.py
├── efficient_frontier.py
├── sharpe_optimized.py
├── crash_scenario_analysis.py
├── portfolio_app.py
└── get_stock_price.py
```

**After:**
```
Finance_portfolio/
├── src/
│   ├── core/
│   │   └── portfolio_calculator.py
│   ├── data/
│   │   ├── cache_manager.py
│   │   └── stock_data_fetcher.py
│   ├── analysis/
│   │   ├── efficient_frontier.py
│   │   ├── sharpe_optimized.py
│   │   └── crash_scenario_analysis.py
│   ├── ui/
│   │   ├── chart_utils.py
│   │   └── data_loader.py
│   └── utils/
│       ├── config.py
│       ├── file_utils.py
│       └── region_classifier.py
├── portfolio_calculator.py (legacy, still works)
├── portfolio_calculator_new.py (new entry point)
└── portfolio_app.py (will be refactored next)
```

## Migration Steps

### 1. For Command-Line Usage

**Old way (still works):**
```bash
python portfolio_calculator.py portfolio.csv
python portfolio_calculator.py portfolio_jp.csv --force-refresh
```

**New way (recommended):**
```bash
python portfolio_calculator_new.py portfolio.csv
python portfolio_calculator_new.py portfolio_jp.csv --force-refresh
```

Both work identically! The old script is kept for backward compatibility.

### 2. For Imports in Python Code

**Old imports:**
```python
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier
from sharpe_optimized import calculate_sharpe_scores
```

**New imports:**
```python
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier, calculate_sharpe_scores
from src.data import CacheManager, StockDataFetcher
from src.ui import DataLoader, chart_utils
from src.utils import Config, RegionClassifier
```

### 3. For Streamlit App (portfolio_app.py)

The Streamlit app currently still uses old imports. This will be updated in a future phase.

**Current (works):**
```python
from portfolio_calculator import PortfolioCalculator
from efficient_frontier import calculate_efficient_frontier
```

**Future (recommended for new code):**
```python
from src.core import PortfolioCalculator
from src.analysis import calculate_efficient_frontier
```

## Backward Compatibility

### What Still Works

✅ All existing command-line scripts
✅ All existing Python imports (old modules remain in root)
✅ All CSV input files (portfolio.csv, portfolio_jp.csv)
✅ All output formats (result files, correlation matrices)
✅ All cache files (data/ticker_cache.json)
✅ All existing tests

### What's New

✨ Modular architecture for easier maintenance
✨ Separated concerns (data, business logic, UI, analysis)
✨ Centralized configuration
✨ Reusable UI components
✨ Better testability
✨ Clearer code organization

## Examples

### Example 1: Using the New Portfolio Calculator

```python
from src.core import PortfolioCalculator

# Create calculator
calculator = PortfolioCalculator(
    csv_file="portfolio.csv",
    force_refresh=False
)

# Run calculation
calculator.run()
```

### Example 2: Using Cache Manager

```python
from src.data import CacheManager

# Initialize cache
cache = CacheManager(cache_dir="data")

# Check if data needs update
if cache.needs_price_update("AAPL"):
    print("Need to fetch new price data")

# Get cached data
data = cache.get("AAPL")

# Save cache
cache.save()
```

### Example 3: Using Data Fetcher

```python
from src.data import StockDataFetcher

# Create fetcher
fetcher = StockDataFetcher()

# Get risk-free rate
rf_rate = fetcher.get_risk_free_rate()

# Get stock info
info = fetcher.get_stock_info("AAPL")

# Get price history
history = fetcher.get_stock_history("AAPL", period="1y")

# Calculate volatility
sigma, sharpe = fetcher.calculate_volatility_and_sharpe(history)
```

### Example 4: Using Configuration

```python
from src.utils import config

# Access configuration
print(config.DATA_DIR)  # "data"
print(config.OUTPUT_DIR)  # "output"
print(config.DEFAULT_RISK_FREE_RATE)  # 4.0

# Ensure directories exist
config.ensure_directories()
```

### Example 5: Using Region Classifier

```python
from src.utils import RegionClassifier

# Classify countries
region = RegionClassifier.classify("Japan")  # "Asia"
region = RegionClassifier.classify("United States")  # "North America"

# Get all regions
regions = RegionClassifier.get_all_regions()
```

### Example 6: Using File Utils

```python
from src.utils import file_utils

# Get latest result file
latest = file_utils.get_latest_result_file("portfolio_result_*.csv")

# Extract timestamp
timestamp = file_utils.extract_timestamp_from_filename(latest)

# Find correlation file
corr_file = file_utils.find_correlation_file(latest)

# Get all result files
us_files, jp_files = file_utils.get_portfolio_files()
```

### Example 7: Using UI Components

```python
from src.ui import DataLoader, chart_utils

# Load data
loader = DataLoader()
df, files = loader.load_combined_latest()

# Create charts
fig = chart_utils.create_pie_chart(
    data=df,
    values_col="value_jp",
    names_col="ticker",
    title="Portfolio Allocation"
)

# Apply mobile layout
fig = chart_utils.apply_mobile_layout(fig)
```

## Testing Your Migration

### 1. Test Imports

```bash
python3 -c "from src.core import PortfolioCalculator; print('✓ Imports work')"
```

### 2. Test Calculation

```bash
python portfolio_calculator_new.py portfolio.csv
```

### 3. Run Tests

```bash
python test_efficient_frontier.py
python test_cache.py
python test_risk_free_rate.py
```

## Troubleshooting

### Import Errors

If you see:
```
ModuleNotFoundError: No module named 'src'
```

Solution: Add the project root to your Python path:
```python
import sys
sys.path.insert(0, '/path/to/Finance_portfolio')
```

### Cache Issues

If cache behavior seems wrong:
```python
from src.data import CacheManager

cache = CacheManager()
cache.clear()  # Clear all cache
cache.save()
```

### Configuration Issues

If settings don't match your setup:
```python
from src.utils import Config

# Modify configuration
Config.DATA_DIR = "my_data"
Config.OUTPUT_DIR = "my_output"
```

## Rollback Plan

If you need to roll back to the old structure:

1. The old modules still exist in the root directory
2. Just use the old imports and scripts
3. All functionality remains intact

## Next Steps

1. **Phase 1**: Start using new imports in new code
2. **Phase 2**: Gradually migrate existing scripts
3. **Phase 3**: Refactor portfolio_app.py to use new modules
4. **Phase 4**: Remove legacy modules when fully migrated

## Questions?

- Review `ARCHITECTURE.md` for design details
- Check module docstrings for API documentation
- Examine example code in this guide
- Look at existing tests for usage patterns

## Benefits of Migration

✨ **Easier to maintain**: Clear module boundaries
✨ **Easier to test**: Mock dependencies easily
✨ **Easier to extend**: Add new features without touching existing code
✨ **Better performance**: Optimized caching and data access
✨ **More scalable**: Ready for large-scale development
