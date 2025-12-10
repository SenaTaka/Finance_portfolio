"""Pages for the Finance Portfolio application.

This package contains individual pages for the multi-page Streamlit app.
"""

from .home import HomePage
from .analysis import AnalysisPage
from .optimization import OptimizationPage
from .rebalancing import RebalancingPage
from .history import HistoryPage
from .ml_predictions import MLPredictionsPage
from .news_sentiment import NewsSentimentPage

__all__ = [
    'HomePage',
    'AnalysisPage',
    'OptimizationPage',
    'RebalancingPage',
    'HistoryPage',
    'MLPredictionsPage',
    'NewsSentimentPage',
]
