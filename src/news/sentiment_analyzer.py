"""Sentiment analysis for news articles."""

from typing import Dict, Any, List
import logging
import re

logger = logging.getLogger(__name__)

# Try to import TextBlob for sentiment analysis
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False


class SentimentAnalyzer:
    """Analyze sentiment of news articles."""
    
    # Keywords for basic sentiment analysis (fallback)
    POSITIVE_KEYWORDS = [
        'profit', 'gain', 'growth', 'rise', 'surge', 'jump', 'rally', 'bullish',
        'upgrade', 'beat', 'outperform', 'success', 'strong', 'positive', 'up',
        'increase', 'high', 'record', 'breakthrough', 'innovation', 'milestone'
    ]
    
    NEGATIVE_KEYWORDS = [
        'loss', 'decline', 'fall', 'drop', 'crash', 'bearish', 'downgrade',
        'miss', 'underperform', 'weak', 'negative', 'down', 'decrease', 'low',
        'lawsuit', 'investigation', 'scandal', 'bankruptcy', 'layoff', 'cut'
    ]
    
    def __init__(self, use_textblob: bool = True):
        """Initialize sentiment analyzer.
        
        Args:
            use_textblob: Whether to use TextBlob (if available)
        """
        self.use_textblob = use_textblob and TEXTBLOB_AVAILABLE
        
        if use_textblob and not TEXTBLOB_AVAILABLE:
            logger.warning("TextBlob not available. Install with: pip install textblob")
            logger.info("Using keyword-based sentiment analysis instead")
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with sentiment score and label
        """
        if self.use_textblob:
            return self._analyze_with_textblob(text)
        else:
            return self._analyze_with_keywords(text)
    
    def _analyze_with_textblob(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using TextBlob.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with polarity, subjectivity, and label
        """
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity  # -1 (negative) to 1 (positive)
        subjectivity = blob.sentiment.subjectivity  # 0 (objective) to 1 (subjective)
        
        # Determine label
        if polarity > 0.1:
            label = 'positive'
        elif polarity < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': float(polarity),
            'subjectivity': float(subjectivity),
            'label': label,
            'method': 'textblob'
        }
    
    def _analyze_with_keywords(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using keyword matching (fallback).
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary with score and label
        """
        text_lower = text.lower()
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in self.POSITIVE_KEYWORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_KEYWORDS if word in text_lower)
        
        # Calculate score
        total = positive_count + negative_count
        if total == 0:
            score = 0
        else:
            score = (positive_count - negative_count) / total
        
        # Determine label
        if score > 0.2:
            label = 'positive'
        elif score < -0.2:
            label = 'negative'
        else:
            label = 'neutral'
        
        return {
            'score': float(score),
            'positive_count': positive_count,
            'negative_count': negative_count,
            'label': label,
            'method': 'keywords'
        }
    
    def analyze_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment of a news article.
        
        Args:
            article: Article dictionary with 'title' key
            
        Returns:
            Article dictionary with added 'sentiment' key
        """
        title = article.get('title', '')
        sentiment = self.analyze_text(title)
        
        article['sentiment'] = sentiment
        return article
    
    def analyze_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze sentiment of multiple articles.
        
        Args:
            articles: List of article dictionaries
            
        Returns:
            List of articles with sentiment analysis
        """
        return [self.analyze_article(article) for article in articles]
    
    def get_ticker_sentiment(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate overall sentiment for a ticker from its articles.
        
        Args:
            articles: List of articles with sentiment
            
        Returns:
            Dictionary with aggregate sentiment metrics
        """
        if not articles:
            return {
                'average_score': 0,
                'label': 'neutral',
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'total_articles': 0
            }
        
        scores = [a['sentiment']['score'] for a in articles if 'sentiment' in a]
        labels = [a['sentiment']['label'] for a in articles if 'sentiment' in a]
        
        avg_score = sum(scores) / len(scores) if scores else 0
        
        # Determine overall label
        if avg_score > 0.1:
            overall_label = 'positive'
        elif avg_score < -0.1:
            overall_label = 'negative'
        else:
            overall_label = 'neutral'
        
        return {
            'average_score': float(avg_score),
            'label': overall_label,
            'positive_count': labels.count('positive'),
            'negative_count': labels.count('negative'),
            'neutral_count': labels.count('neutral'),
            'total_articles': len(articles),
            'confidence': abs(avg_score)  # How confident we are in the sentiment
        }
