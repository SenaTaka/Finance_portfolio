# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-12-09

### Added - Major Features (All 6 Phases)

#### Phase 1: Database Integration
- SQLite database backend to replace JSON cache
- `DatabaseCacheManager` for efficient caching with TTL support
- `PortfolioManager` for portfolio CRUD operations
- Database models: `TickerCache`, `Portfolio`, `PortfolioHolding`, `PortfolioHistory`
- Migration script `migrate_json_to_db.py` for JSON to database migration
- CLI tool `db_manager.py` for database management
- `portfolio_calculator_db.py` with database backend
- Comprehensive migration documentation in `DATABASE_MIGRATION_GUIDE.md`

#### Phase 2: History Tracking
- Automatic portfolio value tracking over time
- `PortfolioHistory` model with time-series data
- Historical query methods with time-period filtering
- Visual historical trends in UI

#### Phase 3: Multiple Portfolio Support
- Support for unlimited portfolios per user
- Portfolio comparison features
- Multi-portfolio UI `portfolio_app_db.py`
- Import portfolios from CSV via UI
- Side-by-side portfolio value comparison

#### Phase 4: Machine Learning Predictions
- Stock price prediction using Random Forest and Gradient Boosting
- Feature engineering with 15+ technical indicators:
  - Moving averages (SMA, EMA)
  - MACD (Moving Average Convergence Divergence)
  - RSI (Relative Strength Index)
  - Bollinger Bands
  - Volatility and momentum indicators
- `StockPredictor` class for individual stocks
- `PortfolioPredictor` for portfolio-level predictions
- Next-day and multi-day price forecasting
- Model persistence (save/load)
- Feature importance analysis

#### Phase 5: Real-time Updates (WebSocket)
- WebSocket server for real-time price streaming
- Subscription-based architecture
- `PriceStreamServer` for client connection management
- `RealTimePriceUpdater` for continuous price updates
- CLI server `realtime_server.py`
- Configurable update intervals
- Multi-client support

#### Phase 6: News & Sentiment Analysis
- News fetching from Yahoo Finance
- `NewsFetcher` for article retrieval
- `SentimentAnalyzer` with multiple methods:
  - TextBlob-based NLP sentiment analysis
  - Keyword-based sentiment analysis (fallback)
- Article-level and ticker-level sentiment scoring
- Confidence scoring for sentiment predictions
- Portfolio news feed aggregation

### Added - Infrastructure
- Comprehensive test suite:
  - `test_database.py` - Database operations
  - `test_ml.py` - Machine learning predictions
  - `test_news.py` - News and sentiment analysis
- Documentation:
  - `DATABASE_MIGRATION_GUIDE.md` - Migration instructions
  - `FEATURE_IMPLEMENTATION_SUMMARY.md` - Complete feature documentation
- Version file `VERSION` with semantic versioning

### Changed
- Updated `requirements.txt` with new dependencies:
  - sqlalchemy>=1.4.0
  - alembic>=1.7.0
  - scikit-learn>=1.0.0
  - websockets>=10.0
  - textblob>=0.15.0
- Added version constraints to all dependencies for stability

### Fixed
- Exception handling in `cache_manager.py` now preserves stack traces
- WebSocket broadcasting now filters closed connections
- Improved error handling across all modules

### Deprecated
- JSON cache system (still supported for backward compatibility)
- Single-portfolio UI `portfolio_app.py` (use `portfolio_app_db.py` instead)

### Security
- Added database connection pooling for better security
- Implemented proper error handling to prevent data leaks
- Added input validation in all API endpoints

## [1.0.0] - Previous Release

### Initial Features
- Basic portfolio calculator with JSON cache
- Yahoo Finance integration
- Risk metrics calculation (Sharpe ratio, volatility)
- Efficient frontier analysis
- Streamlit UI
- Portfolio rebalancing suggestions

---

For migration instructions, see [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md).

For complete feature documentation, see [FEATURE_IMPLEMENTATION_SUMMARY.md](FEATURE_IMPLEMENTATION_SUMMARY.md).
