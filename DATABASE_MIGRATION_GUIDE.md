# Database Migration Guide

## Overview

This guide explains how to migrate from the JSON-based cache system to the new SQLite database backend.

## What's New

### Features Added

1. **Database Backend**: SQLite database replaces JSON file cache
2. **Multiple Portfolio Support**: Manage multiple portfolios in one database
3. **History Tracking**: Automatic tracking of portfolio value over time
4. **Better Performance**: Faster queries and concurrent access
5. **Data Integrity**: ACID transactions and referential integrity

### Database Schema

The new system uses the following tables:

- `ticker_cache`: Stores cached ticker data (prices, volatility, metadata)
- `portfolios`: Portfolio definitions
- `portfolio_holdings`: Current holdings in each portfolio
- `portfolio_history`: Historical snapshots of portfolio values

## Migration Steps

### Option 1: Automatic Migration (Recommended)

If you have an existing JSON cache file at `data/ticker_cache.json`:

```bash
python -m src.database.migrate_json_to_db
```

This will:
1. Create the new database at `data/portfolio.db`
2. Import all ticker data from JSON cache
3. Create a backup of your JSON file at `data/ticker_cache.json.backup`

### Option 2: Fresh Start

If you don't have existing cache or want to start fresh:

```bash
# Initialize the database (this happens automatically on first use)
python -c "from src.database import init_db; init_db()"
```

### Option 3: Import Portfolios from CSV

Import existing portfolio CSV files:

```bash
# Using the new database-backed calculator
python portfolio_calculator_db.py portfolio.csv --name "US Portfolio"
python portfolio_calculator_db.py portfolio_jp.csv --name "JP Portfolio"
```

Or use the Python API:

```python
from src.database import PortfolioManager

mgr = PortfolioManager()
mgr.import_from_csv("portfolio.csv", "US Portfolio")
mgr.import_from_csv("portfolio_jp.csv", "JP Portfolio")
mgr.close()
```

## Usage

### Using the New Calculator

The new calculator works the same as the old one:

```bash
# Basic usage
python portfolio_calculator_db.py portfolio.csv

# With options
python portfolio_calculator_db.py portfolio.csv --force-refresh --name "My Portfolio"
```

### Using the New UI

Launch the multi-portfolio UI:

```bash
streamlit run portfolio_app_db.py
```

Features:
- Select from multiple portfolios
- Import portfolios from CSV
- Create new portfolios
- View historical performance
- Compare multiple portfolios

### Programmatic Access

```python
from src.database import (
    DatabaseCacheManager,
    PortfolioManager,
    init_db
)

# Initialize database
init_db()

# Work with cache
cache_mgr = DatabaseCacheManager()
ticker_data = cache_mgr.get_ticker("AAPL")
cache_mgr.close()

# Work with portfolios
portfolio_mgr = PortfolioManager()

# Create portfolio
portfolio = portfolio_mgr.create_portfolio("My Portfolio")

# Add holdings
holdings = [
    {'ticker': 'AAPL', 'shares': 10},
    {'ticker': 'GOOGL', 'shares': 5}
]
portfolio_mgr.set_holdings(portfolio.id, holdings)

# Get history
history = portfolio_mgr.get_history(portfolio.id, days=30)
print(history)

portfolio_mgr.close()
```

## Backward Compatibility

The old `portfolio_calculator.py` still works with JSON cache. You can use both systems:

- Old system: `python portfolio_calculator.py portfolio.csv`
- New system: `python portfolio_calculator_db.py portfolio.csv`

However, we recommend migrating to the database system for better features.

## Database Location

- Database file: `data/portfolio.db`
- Backup recommended: Copy this file regularly for backup

## Troubleshooting

### Database locked error

If you get "database is locked" errors:
1. Close all apps using the database
2. Check for stale connections: `lsof data/portfolio.db`
3. Restart the application

### Migration fails

If migration fails:
1. Check the backup file exists: `data/ticker_cache.json.backup`
2. Review error messages
3. Try manual migration or fresh start

### Data not appearing

After migration:
1. Verify database exists: `ls -l data/portfolio.db`
2. Check data was imported: 
   ```python
   from src.database import get_session, TickerCache
   session = get_session()
   count = session.query(TickerCache).count()
   print(f"Tickers in database: {count}")
   ```

## Performance Tips

1. **Use force_refresh sparingly**: Only use `--force-refresh` when necessary
2. **Regular updates**: Update data regularly to keep cache warm
3. **Vacuum database**: Periodically run `VACUUM` on the database
   ```bash
   sqlite3 data/portfolio.db "VACUUM;"
   ```

## Advanced Features

### History Tracking

Portfolio values are automatically tracked. View history:

```python
from src.database import PortfolioManager

mgr = PortfolioManager()
history = mgr.get_history(portfolio_id=1, days=365)
print(history)
```

### Multiple Portfolios

Manage multiple portfolios easily:

```python
mgr = PortfolioManager()

# List all portfolios
portfolios = mgr.list_portfolios()

# Compare portfolios
for p in portfolios:
    holdings = mgr.get_holdings(p.id)
    print(f"{p.name}: {len(holdings)} holdings")
```

## Future Enhancements

The database backend enables future features:
- Machine learning predictions (Phase 4)
- Real-time updates via WebSocket (Phase 5)
- News and sentiment analysis (Phase 6)
- User authentication and multi-user support
- Cloud database support

## Support

For issues or questions:
1. Check the test files: `test_database.py`
2. Review the implementation: `src/database/`
3. Open a GitHub issue

## Database Schema Reference

### ticker_cache
- `ticker` (string): Stock ticker symbol
- `price` (float): Current price
- `price_updated` (datetime): Last price update
- `name`, `sector`, `industry`, `country`: Metadata
- `sigma`, `sharpe`: Risk metrics
- `history`: Historical prices (JSON)

### portfolios
- `id`: Primary key
- `name`: Portfolio name
- `description`: Description
- `is_active`: Active status

### portfolio_holdings
- `portfolio_id`: Foreign key to portfolios
- `ticker`: Stock ticker
- `shares`: Number of shares

### portfolio_history
- `portfolio_id`: Foreign key to portfolios
- `total_value_usd`, `total_value_jpy`: Portfolio values
- `snapshot_date`: Timestamp
- `holdings_snapshot`: Detailed holdings (JSON)
