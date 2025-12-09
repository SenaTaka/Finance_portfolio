# Finance Portfolio Management System v2.0

> **Version 2.0** - Complete Enterprise Portfolio Management Platform

A comprehensive, database-backed portfolio management system with machine learning predictions, real-time updates, and sentiment analysis.

---

## 🌟 What's New in Version 2.0

### Major Features Added

1. **💾 Database Backend** - SQLite database replacing JSON cache
2. **📊 Portfolio History** - Automatic value tracking over time
3. **📁 Multiple Portfolios** - Manage unlimited portfolios
4. **🤖 ML Predictions** - Stock price forecasting with AI
5. **⚡ Real-time Updates** - WebSocket price streaming
6. **📰 News & Sentiment** - Market sentiment analysis

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/SenaTaka/Finance_portfolio.git
cd Finance_portfolio

# Install dependencies
pip install -r requirements.txt

# Initialize database
python db_manager.py init
```

### Import Your First Portfolio

```bash
# Import from CSV
python db_manager.py import portfolio.csv --name "My Portfolio"

# Launch UI
streamlit run portfolio_app_db.py
```

---

## 📚 Core Features

### 1. Database Management

**Replace JSON cache with SQLite database:**

```bash
# Initialize database
python db_manager.py init

# Migrate existing JSON cache
python db_manager.py migrate

# List portfolios
python db_manager.py list

# View portfolio details
python db_manager.py show 1

# Cache statistics
python db_manager.py cache
```

### 2. Portfolio Management

**Create and manage multiple portfolios:**

```python
from src.database import PortfolioManager

mgr = PortfolioManager()

# Create portfolio
portfolio = mgr.create_portfolio("Tech Stocks", "High growth tech companies")

# Add holdings
holdings = [
    {'ticker': 'AAPL', 'shares': 10},
    {'ticker': 'GOOGL', 'shares': 5}
]
mgr.set_holdings(portfolio.id, holdings)

# Get holdings
df = mgr.get_holdings(portfolio.id)

# Get history
history = mgr.get_history(portfolio.id, days=30)
```

### 3. Machine Learning Predictions

**Predict stock prices with ML:**

```python
from src.ml import StockPredictor
import yfinance as yf

# Get price history
ticker = yf.Ticker("AAPL")
history = ticker.history(period="1y")

# Train model
predictor = StockPredictor(model_type='random_forest')
metrics = predictor.train(history)

# Predict next day
prediction = predictor.predict_next_day(history)
print(f"Predicted price: ${prediction['predicted_price']:.2f}")
print(f"Direction: {prediction['direction']}")
print(f"Expected return: {prediction['predicted_return']:.2f}%")

# Multi-day forecast
forecast = predictor.predict_multi_day(history, days=5)
print(forecast)
```

**Technical Indicators Included:**
- Moving Averages (SMA, EMA)
- MACD
- RSI (Relative Strength Index)
- Bollinger Bands
- Volatility & Momentum
- And 10+ more...

### 4. Real-time Price Streaming

**Stream live prices via WebSocket:**

```bash
# Stream portfolio holdings
python realtime_server.py --portfolio-id 1 --interval 60

# Stream specific tickers
python realtime_server.py --tickers AAPL GOOGL MSFT --interval 30
```

**Client Example (JavaScript):**

```javascript
const ws = new WebSocket('ws://localhost:8765');

// Subscribe to tickers
ws.send(JSON.stringify({
    action: 'subscribe',
    tickers: ['AAPL', 'GOOGL']
}));

// Receive updates
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log(`${data.ticker}: $${data.data.price}`);
};
```

### 5. News & Sentiment Analysis

**Analyze market sentiment:**

```python
from src.news import NewsFetcher, SentimentAnalyzer

# Fetch news
fetcher = NewsFetcher()
articles = fetcher.get_ticker_news('AAPL', max_articles=10)

# Analyze sentiment
analyzer = SentimentAnalyzer()
articles_with_sentiment = analyzer.analyze_articles(articles)

# Get overall sentiment
ticker_sentiment = analyzer.get_ticker_sentiment(articles_with_sentiment)
print(f"Sentiment: {ticker_sentiment['label']}")
print(f"Score: {ticker_sentiment['average_score']:.2f}")
print(f"Confidence: {ticker_sentiment['confidence']:.2f}")
```

---

## 🖥️ User Interfaces

### Multi-Portfolio Dashboard

```bash
streamlit run portfolio_app_db.py
```

Features:
- Select from multiple portfolios
- View historical performance
- Compare portfolios side-by-side
- Import from CSV
- Create new portfolios
- Update data with one click

### Legacy UI (Still Supported)

```bash
streamlit run portfolio_app.py
```

---

## 📊 Architecture

```
Finance_portfolio/
├── src/
│   ├── database/          # Database models and managers
│   │   ├── models.py
│   │   ├── cache_manager.py
│   │   ├── portfolio_manager.py
│   │   └── migrate_json_to_db.py
│   ├── ml/                # Machine learning
│   │   ├── predictor.py
│   │   ├── feature_engineering.py
│   │   └── portfolio_predictor.py
│   ├── realtime/          # WebSocket server
│   │   ├── websocket_server.py
│   │   └── price_updater.py
│   ├── news/              # News & sentiment
│   │   ├── news_fetcher.py
│   │   └── sentiment_analyzer.py
│   ├── analysis/          # Financial analysis
│   ├── core/              # Core business logic
│   └── utils/             # Utilities
├── data/
│   ├── portfolio.db       # SQLite database
│   └── ml_models/         # Trained models
├── db_manager.py          # Database CLI
├── realtime_server.py     # WebSocket server
├── portfolio_calculator_db.py  # Calculator
└── portfolio_app_db.py    # Multi-portfolio UI
```

---

## 🔧 Configuration

### Database

Database file: `data/portfolio.db`

Configure in `src/database/models.py`:

```python
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "portfolio.db")
```

### Cache TTL

Configure in `DatabaseCacheManager`:

```python
CACHE_TTL_METADATA = 24 * 7  # 1 week
CACHE_TTL_VOLATILITY = 24    # 1 day
CACHE_TTL_PRICE = 0.25       # 15 minutes
```

### ML Models

Default model directory: `data/ml_models/`

Supported models:
- Random Forest (default)
- Gradient Boosting

---

## 🧪 Testing

Run all tests:

```bash
# Database tests
python test_database.py

# ML tests
python test_ml.py

# News tests
python test_news.py

# Cache tests
python test_cache.py
```

---

## 📖 Documentation

- [DATABASE_MIGRATION_GUIDE.md](DATABASE_MIGRATION_GUIDE.md) - Migration instructions
- [FEATURE_IMPLEMENTATION_SUMMARY.md](FEATURE_IMPLEMENTATION_SUMMARY.md) - Complete feature docs
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [ARCHITECTURE_JP.md](ARCHITECTURE_JP.md) - System architecture (Japanese)

---

## 🔄 Migration from v1.x

### Step-by-Step Migration

1. **Install new dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database:**
   ```bash
   python db_manager.py init
   ```

3. **Migrate JSON cache** (if exists):
   ```bash
   python db_manager.py migrate
   ```

4. **Import portfolios:**
   ```bash
   python db_manager.py import portfolio.csv --name "US Stocks"
   python db_manager.py import portfolio_jp.csv --name "Japan Stocks"
   ```

5. **Launch new UI:**
   ```bash
   streamlit run portfolio_app_db.py
   ```

### Backward Compatibility

The old system still works! You can use both:

```bash
# Old system (JSON cache)
python portfolio_calculator.py portfolio.csv

# New system (Database)
python portfolio_calculator_db.py portfolio.csv
```

---

## 📦 Dependencies

Core dependencies:
- `pandas` - Data analysis
- `yfinance` - Yahoo Finance API
- `streamlit` - Web UI
- `sqlalchemy` - Database ORM
- `scikit-learn` - Machine learning
- `websockets` - Real-time streaming
- `textblob` - Sentiment analysis

See [requirements.txt](requirements.txt) for complete list.

---

## 🛠️ Troubleshooting

### Database Issues

**Database locked:**
```bash
# Check connections
lsof data/portfolio.db

# Restart if needed
python db_manager.py init
```

### ML Predictions Fail

**Insufficient data:**
- Need 100+ days of historical data
- Check data quality

### WebSocket Connection Issues

**Connection refused:**
```bash
# Check if server is running
ps aux | grep realtime_server

# Start server
python realtime_server.py --portfolio-id 1
```

---

## 🚧 Performance Tips

1. **Use force_refresh sparingly** - Only when necessary
2. **Regular updates** - Keep cache warm
3. **Vacuum database** - Periodically optimize:
   ```bash
   sqlite3 data/portfolio.db "VACUUM;"
   ```

---

## 🗺️ Roadmap

### Planned Features

- [ ] PostgreSQL support
- [ ] Advanced ML models (LSTM, GRU)
- [ ] Multiple news sources
- [ ] Social media sentiment
- [ ] Mobile app
- [ ] Email alerts
- [ ] Custom dashboards

---

## 🤝 Contributing

Contributions welcome! Please:

1. Follow the modular structure
2. Add tests for new features
3. Update documentation
4. Maintain backward compatibility

---

## 📄 License

[Add license information]

---

## 👥 Authors

[Add author information]

---

## 🙏 Acknowledgments

- Yahoo Finance API (via yfinance)
- Modern Portfolio Theory principles
- Streamlit framework
- scikit-learn team
- All contributors

---

## 📞 Support

For issues or questions:
1. Check documentation
2. Review test files
3. Open a GitHub issue

---

**Built with ❤️ for better portfolio management**
