#!/usr/bin/env python3
"""
Demo script showing how to use advanced features programmatically.

This script demonstrates:
1. Machine learning predictions
2. News fetching and sentiment analysis
3. Real-time price updates

Run: python examples/advanced_features_demo.py
"""

import pandas as pd
from datetime import datetime, timedelta
import yfinance as yf

# Import advanced features
from src.ml import StockPredictor, FeatureEngineer
from src.news import NewsFetcher, SentimentAnalyzer


def demo_ml_predictions(ticker: str = "AAPL"):
    """Demonstrate ML predictions for a stock."""
    print(f"\n{'='*60}")
    print(f"🤖 Machine Learning Prediction Demo for {ticker}")
    print(f"{'='*60}\n")
    
    # Fetch historical data
    print(f"Fetching 1 year of data for {ticker}...")
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    stock = yf.Ticker(ticker)
    history = stock.history(start=start_date, end=end_date)
    
    if len(history) < 100:
        print(f"❌ Insufficient data for {ticker}")
        return
    
    print(f"✓ Loaded {len(history)} days of price data\n")
    
    # Train model
    from src.ui.constants import ML_MODEL_TYPE
    print(f"Training {ML_MODEL_TYPE} model...")
    predictor = StockPredictor(model_type=ML_MODEL_TYPE)
    metrics = predictor.train(history, test_size=0.2)
    
    print(f"✓ Model trained successfully")
    print(f"  - R² Score: {metrics['test_r2']:.3f}")
    print(f"  - MAE: ${metrics['test_mae']:.2f}")
    print(f"  - Training size: {metrics['train_size']} days\n")
    
    # Next day prediction
    print("Next Day Prediction:")
    prediction = predictor.predict_next_day(history)
    
    print(f"  Current Price: ${prediction['current_price']:.2f}")
    print(f"  Predicted Price: ${prediction['predicted_price']:.2f}")
    print(f"  Expected Change: {prediction['predicted_return']:+.2f}%")
    print(f"  Direction: {prediction['direction'].upper()} {'📈' if prediction['direction'] == 'up' else '📉'}\n")
    
    # Multi-day forecast
    print("5-Day Forecast:")
    forecast = predictor.predict_multi_day(history, days=5)
    
    for _, row in forecast.iterrows():
        print(f"  Day {row['day']}: ${row['predicted_price']:.2f} ({row['predicted_return']:+.2f}%)")
    
    # Feature importance
    print("\nTop 5 Important Features:")
    importance = predictor.get_feature_importance()
    for _, row in importance.head(5).iterrows():
        print(f"  {row['feature']}: {row['importance']:.4f}")


def demo_news_sentiment(ticker: str = "AAPL"):
    """Demonstrate news fetching and sentiment analysis."""
    print(f"\n{'='*60}")
    print(f"📰 News & Sentiment Analysis Demo for {ticker}")
    print(f"{'='*60}\n")
    
    # Fetch news
    print(f"Fetching latest news for {ticker}...")
    fetcher = NewsFetcher()
    articles = fetcher.get_ticker_news(ticker, max_articles=5)
    
    if not articles:
        print(f"❌ No news found for {ticker}")
        return
    
    print(f"✓ Fetched {len(articles)} articles\n")
    
    # Analyze sentiment
    from src.ui.constants import SENTIMENT_USE_TEXTBLOB
    print("Analyzing sentiment...")
    analyzer = SentimentAnalyzer(use_textblob=SENTIMENT_USE_TEXTBLOB)
    articles_with_sentiment = analyzer.analyze_articles(articles)
    ticker_sentiment = analyzer.get_ticker_sentiment(articles_with_sentiment)
    
    print(f"✓ Sentiment analysis complete\n")
    
    # Overall sentiment
    print("Overall Sentiment:")
    sentiment_emoji = {
        'positive': '🟢',
        'negative': '🔴',
        'neutral': '⚪'
    }
    emoji = sentiment_emoji.get(ticker_sentiment['label'], '⚪')
    
    print(f"  {emoji} {ticker_sentiment['label'].upper()}")
    print(f"  Score: {ticker_sentiment['average_score']:.2f}")
    print(f"  Confidence: {ticker_sentiment.get('confidence', 0):.2f}")
    print(f"  Positive: {ticker_sentiment['positive_count']}")
    print(f"  Neutral: {ticker_sentiment['neutral_count']}")
    print(f"  Negative: {ticker_sentiment['negative_count']}\n")
    
    # Individual articles
    print("Recent Articles:")
    for i, article in enumerate(articles_with_sentiment[:3], 1):
        sentiment = article.get('sentiment', {})
        label = sentiment.get('label', 'neutral')
        score = sentiment.get('score', 0)
        
        emoji = sentiment_emoji.get(label, '⚪')
        print(f"\n  {i}. {article['title']}")
        print(f"     {article['publisher']} • {article['published'].strftime('%Y-%m-%d')}")
        print(f"     Sentiment: {emoji} {label.upper()} (Score: {score:.2f})")


def demo_portfolio_analysis(tickers: list = None):
    """Demonstrate portfolio-level analysis."""
    if tickers is None:
        tickers = ["AAPL", "GOOGL", "MSFT"]
    
    print(f"\n{'='*60}")
    print(f"📊 Portfolio Analysis Demo")
    print(f"{'='*60}\n")
    
    print(f"Analyzing {len(tickers)} stocks: {', '.join(tickers)}\n")
    
    # ML Predictions
    print("1. ML Predictions:")
    print("-" * 40)
    
    predictions = []
    for ticker in tickers:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            stock = yf.Ticker(ticker)
            history = stock.history(start=start_date, end=end_date)
            
            if len(history) < 100:
                continue
            
            predictor = StockPredictor(model_type='random_forest')
            predictor.train(history, test_size=0.2)
            prediction = predictor.predict_next_day(history)
            
            predictions.append({
                'ticker': ticker,
                'current': prediction['current_price'],
                'predicted': prediction['predicted_price'],
                'return': prediction['predicted_return'],
                'direction': prediction['direction']
            })
            
        except Exception as e:
            print(f"  ⚠️  Could not predict {ticker}: {str(e)}")
    
    if predictions:
        pred_df = pd.DataFrame(predictions)
        pred_df = pred_df.sort_values('return', ascending=False)
        
        print("\nPredictions Summary:")
        for _, row in pred_df.iterrows():
            emoji = '📈' if row['direction'] == 'up' else '📉'
            print(f"  {row['ticker']}: ${row['current']:.2f} → ${row['predicted']:.2f} ({row['return']:+.2f}%) {emoji}")
    
    # Sentiment Analysis
    print(f"\n2. Sentiment Analysis:")
    print("-" * 40)
    
    fetcher = NewsFetcher()
    analyzer = SentimentAnalyzer(use_textblob=False)
    
    sentiments = []
    for ticker in tickers:
        try:
            articles = fetcher.get_ticker_news(ticker, max_articles=5)
            if articles:
                articles_with_sentiment = analyzer.analyze_articles(articles)
                ticker_sentiment = analyzer.get_ticker_sentiment(articles_with_sentiment)
                
                sentiments.append({
                    'ticker': ticker,
                    'sentiment': ticker_sentiment['label'],
                    'score': ticker_sentiment['average_score'],
                    'articles': ticker_sentiment['total_articles']
                })
        except Exception as e:
            print(f"  ⚠️  Could not analyze {ticker}: {str(e)}")
    
    if sentiments:
        sent_df = pd.DataFrame(sentiments)
        
        print("\nSentiment Summary:")
        for _, row in sent_df.iterrows():
            if row['sentiment'] == 'positive':
                emoji = '🟢'
            elif row['sentiment'] == 'negative':
                emoji = '🔴'
            else:
                emoji = '⚪'
            
            print(f"  {row['ticker']}: {emoji} {row['sentiment'].upper()} (Score: {row['score']:.2f}, Articles: {row['articles']})")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("Advanced Features Demo")
    print("Demonstrating ML Predictions, News & Sentiment Analysis")
    print("="*60)
    
    # Demo 1: ML Predictions for a single stock
    demo_ml_predictions("AAPL")
    
    # Demo 2: News & Sentiment for a single stock
    demo_news_sentiment("AAPL")
    
    # Demo 3: Portfolio-level analysis
    demo_portfolio_analysis(["AAPL", "GOOGL", "MSFT"])
    
    print("\n" + "="*60)
    print("Demo Complete!")
    print("="*60 + "\n")
    
    print("To use these features in the UI:")
    print("  streamlit run portfolio_app_v2.py")
    print("\nFor detailed documentation:")
    print("  See ADVANCED_FEATURES_GUIDE.md")


if __name__ == "__main__":
    main()
