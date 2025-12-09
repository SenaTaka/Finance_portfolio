"""Tests for news and sentiment analysis module."""

import unittest
from datetime import datetime

try:
    from src.news import NewsFetcher, SentimentAnalyzer
    NEWS_AVAILABLE = True
except ImportError:
    NEWS_AVAILABLE = False


@unittest.skipIf(not NEWS_AVAILABLE, "News module not available")
class TestSentimentAnalyzer(unittest.TestCase):
    """Test sentiment analyzer."""
    
    def setUp(self):
        """Set up analyzer."""
        self.analyzer = SentimentAnalyzer(use_textblob=False)  # Use keyword-based for tests
    
    def test_positive_sentiment(self):
        """Test detection of positive sentiment."""
        text = "Company reports record profit and strong growth in Q3"
        result = self.analyzer.analyze_text(text)
        
        self.assertEqual(result['label'], 'positive')
        self.assertGreater(result['score'], 0)
    
    def test_negative_sentiment(self):
        """Test detection of negative sentiment."""
        text = "Stock crashes as company faces bankruptcy and layoffs"
        result = self.analyzer.analyze_text(text)
        
        self.assertEqual(result['label'], 'negative')
        self.assertLess(result['score'], 0)
    
    def test_neutral_sentiment(self):
        """Test detection of neutral sentiment."""
        text = "Company announces new product release date"
        result = self.analyzer.analyze_text(text)
        
        self.assertEqual(result['label'], 'neutral')
    
    def test_analyze_article(self):
        """Test article analysis."""
        article = {
            'title': 'Stock surges on strong earnings beat',
            'publisher': 'Test News'
        }
        
        result = self.analyzer.analyze_article(article)
        
        self.assertIn('sentiment', result)
        self.assertIn('score', result['sentiment'])
        self.assertIn('label', result['sentiment'])
    
    def test_analyze_multiple_articles(self):
        """Test analysis of multiple articles."""
        articles = [
            {'title': 'Stock gains on positive news'},
            {'title': 'Company faces challenges'},
        ]
        
        results = self.analyzer.analyze_articles(articles)
        
        self.assertEqual(len(results), 2)
        for result in results:
            self.assertIn('sentiment', result)
    
    def test_get_ticker_sentiment(self):
        """Test aggregate ticker sentiment."""
        articles = [
            {'title': 'Stock surges on earnings beat', 'sentiment': {'score': 0.5, 'label': 'positive'}},
            {'title': 'Company reports growth', 'sentiment': {'score': 0.3, 'label': 'positive'}},
            {'title': 'Minor setback reported', 'sentiment': {'score': -0.2, 'label': 'negative'}},
        ]
        
        sentiment = self.analyzer.get_ticker_sentiment(articles)
        
        self.assertIn('average_score', sentiment)
        self.assertIn('label', sentiment)
        self.assertIn('positive_count', sentiment)
        self.assertIn('negative_count', sentiment)
        self.assertEqual(sentiment['total_articles'], 3)


@unittest.skipIf(not NEWS_AVAILABLE, "News module not available")
class TestNewsFetcher(unittest.TestCase):
    """Test news fetcher."""
    
    def setUp(self):
        """Set up fetcher."""
        self.fetcher = NewsFetcher()
    
    def test_fetcher_initialization(self):
        """Test fetcher can be initialized."""
        self.assertIsNotNone(self.fetcher)
    
    # Note: The following tests require network access and may fail if:
    # - Network is unavailable
    # - Yahoo Finance API changes
    # - No news available for the ticker
    # They are marked as skippable for automated testing
    
    @unittest.skip("Requires network access")
    def test_get_ticker_news(self):
        """Test fetching news for a ticker (requires network)."""
        articles = self.fetcher.get_ticker_news('AAPL', max_articles=5)
        
        if articles:  # May be empty if no news available
            self.assertIsInstance(articles, list)
            self.assertLessEqual(len(articles), 5)
            
            # Check article structure
            article = articles[0]
            self.assertIn('title', article)
            self.assertIn('publisher', article)
            self.assertIn('link', article)
            self.assertIn('published', article)


if __name__ == "__main__":
    unittest.main()
