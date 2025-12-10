# Advanced Features Guide

This guide explains how to use the advanced features integrated into the Finance Portfolio application.

## Overview

The Finance Portfolio application now includes three powerful advanced features:

1. **🤖 Machine Learning Predictions** - AI-powered stock price forecasting
2. **⚡ Real-time Updates** - Live price tracking with auto-refresh
3. **📰 News & Sentiment Analysis** - Market news and AI sentiment scoring

## Machine Learning Predictions

### Overview

The ML Predictions page uses Random Forest and Gradient Boosting models to forecast stock prices based on:
- Technical indicators (RSI, MACD, Bollinger Bands, etc.)
- Historical price patterns
- Volume trends
- Time-series features

### How to Use

1. **Navigate to ML Predictions Page**
   - Launch the app: `streamlit run portfolio_app_v2.py`
   - Select "🤖 ML Predictions" from the sidebar navigation

2. **Single Stock Prediction**
   - Select a stock from your portfolio using the dropdown
   - The system automatically:
     - Fetches 1 year of historical data
     - Trains a machine learning model
     - Generates predictions for the next 5 days
   
3. **View Results**
   - **Model Performance**: R² score, Mean Absolute Error, training size
   - **Next Day Prediction**: Current price, predicted price, direction (up/down)
   - **5-Day Forecast**: Chart and table showing multi-day predictions
   - **Feature Importance**: Which factors most influence the prediction

4. **Portfolio-Level Predictions**
   - Click "Generate Predictions for All Stocks"
   - Wait for batch processing to complete
   - View summary metrics:
     - Number of bullish vs bearish signals
     - Average predicted return
     - Top performing stocks
   - Interactive charts showing all predictions

### Understanding the Results

- **R² Score**: Model accuracy (1.0 = perfect, higher is better)
- **MAE**: Average prediction error in dollars (lower is better)
- **Predicted Return**: Expected price change percentage
- **Direction**: "Up" (📈) or "Down" (📉) movement prediction
- **Feature Importance**: Shows which technical indicators matter most

### Example Output

```
Current Price: $150.25
Predicted Price: $153.40 (+2.10%)
Direction: 📈 UP
R² Score: 0.847
```

### Tips

- Models work best with at least 100 days of historical data
- Higher R² scores indicate more reliable predictions
- Use predictions as one input among many for investment decisions
- Consider re-training models periodically with fresh data

## Real-time Price Updates

### Overview

Real-time updates provide live price tracking for your portfolio stocks with automatic refresh capabilities.

### How to Use

1. **Enable Auto-Refresh**
   - Open the home page (🏠 Home)
   - Check "⚡ Enable Auto-Refresh" in the sidebar
   - Prices refresh automatically every 60 seconds

2. **Manual Refresh**
   - Click "🔄 Refresh Now" button for immediate update
   - Useful when you want to check prices without waiting

3. **View Real-time Data**
   - Expand "⚡ Real-time Price Updates" section on home page
   - See live updates for all portfolio stocks:
     - Current price
     - Day change ($ and %)
     - Day high/low
     - Trading volume

### Features

- **Live Price Tracking**: Current prices from Yahoo Finance
- **Change Indicators**: Green (up) / Red (down) with percentages
- **Volume Data**: Trading activity for each stock
- **Summary Statistics**: Portfolio-level metrics
  - Number of gainers vs losers
  - Average portfolio change
  - Top performing stock

### Example Display

```
AAPL
Current Price: $150.25 (+$2.15, +1.45%)
Day High/Low: $151.00 / $148.50
Volume: 52.3M

Portfolio Summary:
Gainers: 8/10
Average Change: +0.85%
Top Performer: NVDA (+3.21%)
```

### Auto-Refresh Behavior

- Refreshes every 60 seconds when enabled
- Shows refresh count in sidebar
- Preserves user's page position during refresh
- Can be disabled anytime from sidebar

## News & Sentiment Analysis

### Overview

The News & Sentiment page fetches latest market news and analyzes sentiment using AI to help you understand market mood.

### How to Use

1. **Navigate to News & Sentiment Page**
   - Select "📰 News & Sentiment" from sidebar navigation

2. **News Feed Tab**
   - Adjust number of articles (5-30)
   - Click "Fetch Latest News"
   - View articles with sentiment badges:
     - 🟢 Positive (bullish news)
     - 🔴 Negative (bearish news)
     - ⚪ Neutral (informational)
   - Each article shows:
     - Headline
     - Publisher and timestamp
     - Sentiment score
     - Link to full article

3. **Sentiment Overview Tab**
   - Select articles per stock (3-15)
   - Click "Analyze Sentiment"
   - View portfolio-wide sentiment metrics:
     - Number of positive/negative stocks
     - Average sentiment score
     - Total articles analyzed
   - Interactive charts show sentiment distribution
   - Detailed table with per-stock breakdown

4. **Stock Details Tab**
   - Select specific stock from portfolio
   - Choose number of articles to analyze
   - Click "Fetch & Analyze"
   - See comprehensive analysis:
     - Overall sentiment (positive/negative/neutral)
     - Sentiment confidence score
     - Pie chart showing sentiment breakdown
     - Individual article details with scores

### Sentiment Scoring

- **Score Range**: -1.0 (very negative) to +1.0 (very positive)
- **Labels**:
  - Positive: Score > 0.1 (bullish indicators)
  - Negative: Score < -0.1 (bearish indicators)
  - Neutral: Score between -0.1 and 0.1
- **Confidence**: How certain the model is about the sentiment (0.0 to 1.0)

### Understanding Sentiment Results

**Positive Sentiment** (🟢)
- Indicates bullish news (earnings beats, new products, positive forecasts)
- Higher scores suggest stronger positive sentiment
- Example headlines:
  - "Company reports record quarterly earnings"
  - "Stock surges on strong product demand"

**Negative Sentiment** (🔴)
- Indicates bearish news (losses, layoffs, negative forecasts)
- Lower (more negative) scores suggest stronger negative sentiment
- Example headlines:
  - "Company faces regulatory challenges"
  - "Stock drops on weak guidance"

**Neutral Sentiment** (⚪)
- Factual/informational news without clear positive/negative tone
- Example headlines:
  - "Company announces annual shareholder meeting"
  - "New product launch scheduled for Q2"

### Example Output

```
Portfolio Sentiment Overview
===========================
Positive Stocks: 7/10
Negative Stocks: 2/10
Average Score: +0.23
Total Articles: 50

AAPL - Overall Sentiment
========================
Sentiment: 🟢 POSITIVE
Average Score: +0.45
Confidence: 0.82
Articles Analyzed: 10

Breakdown:
- Positive: 7 articles
- Neutral: 2 articles
- Negative: 1 article
```

### Tips for Using Sentiment Analysis

1. **Context Matters**: Read full articles, not just headlines
2. **Aggregate Data**: Look at overall sentiment trends, not individual articles
3. **Confidence Scores**: Higher confidence = more reliable sentiment
4. **Combine with Other Data**: Use sentiment alongside price data and technical analysis
5. **Recency**: Check publication dates - recent news is usually more relevant

## Integration with Portfolio Management

### Combined Usage Workflow

Here's how to use all three features together:

1. **Morning Routine**
   - Enable auto-refresh on home page
   - Check real-time price movements
   - Review sentiment on news page

2. **Weekly Analysis**
   - Generate ML predictions for all stocks
   - Identify stocks with strong positive predictions
   - Cross-reference with sentiment analysis
   - Look for alignment: positive predictions + positive sentiment

3. **Investment Decisions**
   - Use ML predictions for price targets
   - Use sentiment to gauge market mood
   - Use real-time data for entry/exit timing
   - Combine with fundamental analysis

### Best Practices

1. **Don't Rely on One Signal**
   - Use ML predictions + sentiment + technical analysis
   - Consider multiple timeframes
   - Verify with fundamental data

2. **Regular Updates**
   - Re-train ML models monthly
   - Check news daily for your holdings
   - Monitor real-time prices during trading hours

3. **Risk Management**
   - ML predictions are probabilistic, not certain
   - Negative sentiment doesn't always mean sell
   - Use stop-losses and position sizing

4. **Data Quality**
   - Ensure sufficient historical data for ML (100+ days)
   - Check news sources are reputable
   - Verify real-time price accuracy

## Technical Details

### Machine Learning

- **Models**: Random Forest (primary), Gradient Boosting (alternative)
- **Features**: 15+ technical indicators + lag features + time features
- **Training**: 80/20 train/test split
- **Validation**: MSE, MAE, R² metrics

### News & Sentiment

- **News Source**: Yahoo Finance
- **Sentiment Methods**: 
  - Keyword-based analysis (always available)
  - TextBlob NLP (optional, enhanced accuracy)
- **Update Frequency**: On-demand

### Real-time Updates

- **Price Source**: Yahoo Finance API
- **Update Interval**: 60 seconds (configurable)
- **Data Points**: Price, volume, high/low, changes

## Troubleshooting

### ML Predictions Issues

**Problem**: "Insufficient data for prediction"
- **Solution**: Stock needs at least 100 days of price history
- **Workaround**: Wait for more historical data to accumulate

**Problem**: Low R² score (< 0.3)
- **Solution**: Model may not fit well for this stock
- **Workaround**: Try longer training period or different stocks

### Real-time Updates Issues

**Problem**: Prices not updating
- **Solution**: Check internet connection and Yahoo Finance availability
- **Workaround**: Use manual refresh button

**Problem**: Auto-refresh causing lag
- **Solution**: Disable auto-refresh if performance is poor
- **Workaround**: Use manual refresh instead

### News & Sentiment Issues

**Problem**: "No news articles found"
- **Solution**: Stock may not have recent news coverage
- **Workaround**: Check major index ETFs or larger companies

**Problem**: Sentiment seems inaccurate
- **Solution**: Keyword-based analysis has limitations
- **Workaround**: Install TextBlob for better accuracy: `pip install textblob`

## API Limits and Performance

### Yahoo Finance Rate Limits

- Be mindful of API rate limits
- Avoid excessive requests in short time periods
- Use caching when possible

### Performance Optimization

- ML training can take 10-30 seconds per stock
- Batch operations may take several minutes
- News fetching depends on network speed
- Consider analyzing fewer stocks for faster results

## Future Enhancements

Planned improvements:

1. **ML Models**
   - LSTM/GRU for better time-series prediction
   - Ensemble methods combining multiple models
   - Anomaly detection for unusual patterns

2. **Real-time**
   - WebSocket integration for push updates
   - Multiple data sources
   - Order book data

3. **Sentiment**
   - Multiple news sources (NewsAPI, Bloomberg)
   - Advanced NLP (BERT, FinBERT)
   - Social media sentiment (Twitter, Reddit)

## Support

For issues or questions:
- Check existing tests: `test_ml.py`, `test_news.py`, `test_ui_advanced_features.py`
- Review code documentation in source files
- See FEATURE_IMPLEMENTATION_SUMMARY.md for technical details

## Conclusion

These advanced features transform the Finance Portfolio app from a simple tracker into a comprehensive investment analysis platform. By combining ML predictions, real-time data, and sentiment analysis, you gain multiple perspectives on your portfolio and individual stocks.

Remember: These are tools to inform decisions, not replace human judgment. Always do your own research and consider your risk tolerance before making investment decisions.
