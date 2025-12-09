"""Fetch news articles for stocks."""

import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class NewsFetcher:
    """Fetch news articles for stocks."""
    
    def __init__(self):
        """Initialize news fetcher."""
        pass
    
    def get_ticker_news(self, ticker: str, max_articles: int = 10) -> List[Dict[str, Any]]:
        """Fetch news for a specific ticker.
        
        Args:
            ticker: Stock ticker symbol
            max_articles: Maximum number of articles to return
            
        Returns:
            List of news article dictionaries
        """
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                return []
            
            # Format news items
            articles = []
            for item in news[:max_articles]:
                article = {
                    'title': item.get('title', ''),
                    'publisher': item.get('publisher', ''),
                    'link': item.get('link', ''),
                    'published': datetime.fromtimestamp(item.get('providerPublishTime', 0)),
                    'type': item.get('type', 'news'),
                    'thumbnail': item.get('thumbnail', {}).get('resolutions', [{}])[0].get('url', '') if item.get('thumbnail') else '',
                }
                articles.append(article)
            
            return articles
        
        except Exception as e:
            logger.error(f"Error fetching news for {ticker}: {e}")
            return []
    
    def get_portfolio_news(self, tickers: List[str], 
                          articles_per_ticker: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch news for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            articles_per_ticker: Number of articles per ticker
            
        Returns:
            Dictionary mapping ticker -> list of articles
        """
        news_by_ticker = {}
        
        for ticker in tickers:
            articles = self.get_ticker_news(ticker, articles_per_ticker)
            if articles:
                news_by_ticker[ticker] = articles
        
        return news_by_ticker
    
    def get_recent_news_feed(self, tickers: List[str], 
                            max_total: int = 20) -> List[Dict[str, Any]]:
        """Get a combined news feed for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
            max_total: Maximum total articles to return
            
        Returns:
            List of news articles sorted by date (most recent first)
        """
        all_articles = []
        
        for ticker in tickers:
            articles = self.get_ticker_news(ticker, max_articles=5)
            for article in articles:
                article['ticker'] = ticker
                all_articles.append(article)
        
        # Sort by published date (most recent first)
        all_articles.sort(key=lambda x: x['published'], reverse=True)
        
        # Remove duplicates (same link)
        seen_links = set()
        unique_articles = []
        for article in all_articles:
            if article['link'] not in seen_links:
                seen_links.add(article['link'])
                unique_articles.append(article)
        
        return unique_articles[:max_total]
