"""News & Sentiment page - Market news and sentiment analysis."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from typing import List, Dict

try:
    from src.news import NewsFetcher, SentimentAnalyzer
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False


class NewsSentimentPage:
    """News and sentiment analysis page."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render the news and sentiment page.
        
        Args:
            df: Portfolio DataFrame
        """
        st.title("📰 News & Sentiment Analysis")
        
        if not NEWS_AVAILABLE:
            st.error("News module not available. Please check installation.")
            return
        
        st.markdown("""
        Get the latest market news and AI-powered sentiment analysis for your portfolio stocks.
        Sentiment analysis helps identify market mood and potential price movements.
        """)
        
        # Initialize components
        from ..constants import SENTIMENT_USE_TEXTBLOB
        fetcher = NewsFetcher()
        analyzer = SentimentAnalyzer(use_textblob=SENTIMENT_USE_TEXTBLOB)  # Configurable via constants
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["📰 News Feed", "📊 Sentiment Overview", "🔍 Stock Details"])
        
        with tab1:
            NewsSentimentPage._render_news_feed(df, fetcher, analyzer)
        
        with tab2:
            NewsSentimentPage._render_sentiment_overview(df, fetcher, analyzer)
        
        with tab3:
            NewsSentimentPage._render_stock_details(df, fetcher, analyzer)
    
    @staticmethod
    def _render_news_feed(df: pd.DataFrame, fetcher: NewsFetcher, analyzer: SentimentAnalyzer):
        """Render combined news feed for portfolio.
        
        Args:
            df: Portfolio DataFrame
            fetcher: News fetcher instance
            analyzer: Sentiment analyzer instance
        """
        st.subheader("📰 Latest News Feed")
        
        max_articles = st.slider("Number of articles", 5, 30, 15)
        
        if st.button("Fetch Latest News", key="fetch_feed"):
            with st.spinner("Fetching news for your portfolio..."):
                tickers = df['ticker'].unique().tolist()
                articles = fetcher.get_recent_news_feed(tickers, max_total=max_articles)
                
                if not articles:
                    st.warning("No news articles found for your portfolio stocks.")
                    return
                
                # Analyze sentiment
                articles_with_sentiment = analyzer.analyze_articles(articles)
                
                # Display articles
                for article in articles_with_sentiment:
                    sentiment = article.get('sentiment', {})
                    label = sentiment.get('label', 'neutral')
                    score = sentiment.get('score', 0)
                    
                    # Sentiment badge
                    if label == 'positive':
                        badge = "🟢 Positive"
                        badge_color = "green"
                    elif label == 'negative':
                        badge = "🔴 Negative"
                        badge_color = "red"
                    else:
                        badge = "⚪ Neutral"
                        badge_color = "gray"
                    
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**[{article['title']}]({article['link']})**")
                            st.caption(f"{article['ticker']} • {article['publisher']} • {article['published'].strftime('%Y-%m-%d %H:%M')}")
                        
                        with col2:
                            st.markdown(f":{badge_color}[{badge}]")
                            st.caption(f"Score: {score:.2f}")
                        
                        st.divider()
    
    @staticmethod
    def _render_sentiment_overview(df: pd.DataFrame, fetcher: NewsFetcher, analyzer: SentimentAnalyzer):
        """Render sentiment overview for all stocks.
        
        Args:
            df: Portfolio DataFrame
            fetcher: News fetcher instance
            analyzer: Sentiment analyzer instance
        """
        st.subheader("📊 Portfolio Sentiment Overview")
        
        articles_per_stock = st.slider("Articles per stock", 3, 15, 5, key="overview_slider")
        
        if st.button("Analyze Sentiment", key="analyze_sentiment"):
            with st.spinner("Analyzing sentiment for your portfolio..."):
                tickers = df['ticker'].unique().tolist()
                sentiment_results = []
                
                progress_bar = st.progress(0)
                
                for i, ticker in enumerate(tickers):
                    try:
                        # Fetch news
                        articles = fetcher.get_ticker_news(ticker, max_articles=articles_per_stock)
                        
                        if not articles:
                            continue
                        
                        # Analyze sentiment
                        articles_with_sentiment = analyzer.analyze_articles(articles)
                        ticker_sentiment = analyzer.get_ticker_sentiment(articles_with_sentiment)
                        
                        sentiment_results.append({
                            'ticker': ticker,
                            'sentiment': ticker_sentiment['label'],
                            'score': ticker_sentiment['average_score'],
                            'positive': ticker_sentiment['positive_count'],
                            'negative': ticker_sentiment['negative_count'],
                            'neutral': ticker_sentiment['neutral_count'],
                            'total_articles': ticker_sentiment['total_articles'],
                            'confidence': ticker_sentiment.get('confidence', 0)
                        })
                        
                    except Exception as e:
                        st.warning(f"Could not analyze {ticker}: {str(e)}")
                    
                    progress_bar.progress((i + 1) / len(tickers))
                
                progress_bar.empty()
                
                if sentiment_results:
                    sentiment_df = pd.DataFrame(sentiment_results)
                    
                    # Summary metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        positive_count = len(sentiment_df[sentiment_df['sentiment'] == 'positive'])
                        st.metric("Positive Stocks", f"{positive_count}/{len(sentiment_df)}")
                    
                    with col2:
                        negative_count = len(sentiment_df[sentiment_df['sentiment'] == 'negative'])
                        st.metric("Negative Stocks", f"{negative_count}/{len(sentiment_df)}")
                    
                    with col3:
                        avg_score = sentiment_df['score'].mean()
                        st.metric("Average Score", f"{avg_score:.2f}")
                    
                    with col4:
                        total_articles = sentiment_df['total_articles'].sum()
                        st.metric("Total Articles", total_articles)
                    
                    # Sentiment distribution chart
                    st.subheader("Sentiment Distribution")
                    
                    fig = px.bar(
                        sentiment_df,
                        x='ticker',
                        y='score',
                        color='sentiment',
                        color_discrete_map={
                            'positive': 'green',
                            'negative': 'red',
                            'neutral': 'gray'
                        },
                        title='Sentiment Scores by Stock',
                        hover_data=['total_articles', 'confidence']
                    )
                    fig.update_layout(xaxis_title="Stock", yaxis_title="Sentiment Score")
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed table
                    st.subheader("Detailed Sentiment Analysis")
                    st.dataframe(
                        sentiment_df.style.format({
                            'score': '{:.2f}',
                            'confidence': '{:.2f}'
                        }).background_gradient(subset=['score'], cmap='RdYlGn'),
                        use_container_width=True
                    )
                else:
                    st.warning("No sentiment data could be collected.")
    
    @staticmethod
    def _render_stock_details(df: pd.DataFrame, fetcher: NewsFetcher, analyzer: SentimentAnalyzer):
        """Render detailed news and sentiment for a specific stock.
        
        Args:
            df: Portfolio DataFrame
            fetcher: News fetcher instance
            analyzer: Sentiment analyzer instance
        """
        st.subheader("🔍 Stock-Specific Analysis")
        
        # Stock selector
        tickers = df['ticker'].unique().tolist()
        selected_ticker = st.selectbox("Select Stock", tickers, key="detail_ticker")
        
        max_articles = st.slider("Number of articles", 5, 20, 10, key="detail_slider")
        
        if st.button("Fetch & Analyze", key="detail_button"):
            with st.spinner(f"Analyzing {selected_ticker}..."):
                try:
                    # Fetch news
                    articles = fetcher.get_ticker_news(selected_ticker, max_articles=max_articles)
                    
                    if not articles:
                        st.warning(f"No news articles found for {selected_ticker}.")
                        return
                    
                    # Analyze sentiment
                    articles_with_sentiment = analyzer.analyze_articles(articles)
                    ticker_sentiment = analyzer.get_ticker_sentiment(articles_with_sentiment)
                    
                    # Display overall sentiment
                    st.subheader(f"Overall Sentiment for {selected_ticker}")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        sentiment_emoji = {
                            'positive': '🟢',
                            'negative': '🔴',
                            'neutral': '⚪'
                        }
                        emoji = sentiment_emoji.get(ticker_sentiment['label'], '⚪')
                        st.metric("Sentiment", f"{emoji} {ticker_sentiment['label'].upper()}")
                    
                    with col2:
                        st.metric("Average Score", f"{ticker_sentiment['average_score']:.2f}")
                    
                    with col3:
                        st.metric("Confidence", f"{ticker_sentiment.get('confidence', 0):.2f}")
                    
                    with col4:
                        st.metric("Articles Analyzed", ticker_sentiment['total_articles'])
                    
                    # Sentiment breakdown
                    st.subheader("Sentiment Breakdown")
                    
                    breakdown_data = {
                        'Category': ['Positive', 'Neutral', 'Negative'],
                        'Count': [
                            ticker_sentiment['positive_count'],
                            ticker_sentiment['neutral_count'],
                            ticker_sentiment['negative_count']
                        ]
                    }
                    
                    fig = px.pie(
                        breakdown_data,
                        values='Count',
                        names='Category',
                        color='Category',
                        color_discrete_map={
                            'Positive': 'green',
                            'Neutral': 'gray',
                            'Negative': 'red'
                        }
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Individual articles
                    st.subheader("Individual Articles")
                    
                    for i, article in enumerate(articles_with_sentiment, 1):
                        sentiment = article.get('sentiment', {})
                        label = sentiment.get('label', 'neutral')
                        score = sentiment.get('score', 0)
                        
                        with st.expander(f"{i}. {article['title']}"):
                            st.markdown(f"**Publisher:** {article['publisher']}")
                            st.markdown(f"**Published:** {article['published'].strftime('%Y-%m-%d %H:%M')}")
                            st.markdown(f"**Link:** [{article['link']}]({article['link']})")
                            
                            # Sentiment indicator
                            if label == 'positive':
                                st.success(f"Sentiment: {label.upper()} (Score: {score:.2f})")
                            elif label == 'negative':
                                st.error(f"Sentiment: {label.upper()} (Score: {score:.2f})")
                            else:
                                st.info(f"Sentiment: {label.upper()} (Score: {score:.2f})")
                    
                except Exception as e:
                    st.error(f"Error analyzing {selected_ticker}: {str(e)}")
                    st.exception(e)
