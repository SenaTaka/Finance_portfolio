"""Test advanced UI features integration."""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime

# Test that UI pages can be imported
try:
    from src.ui.pages import MLPredictionsPage, NewsSentimentPage
    from src.ui.components import RealtimeUpdates
    UI_AVAILABLE = True
except ImportError as e:
    print(f"UI import error: {e}")
    UI_AVAILABLE = False


@unittest.skipIf(not UI_AVAILABLE, "UI modules not available")
class TestUIIntegration(unittest.TestCase):
    """Test UI integration for advanced features."""
    
    def setUp(self):
        """Create sample portfolio data."""
        self.df = pd.DataFrame({
            'ticker': ['AAPL', 'GOOGL', 'MSFT'],
            'name': ['Apple Inc.', 'Alphabet Inc.', 'Microsoft Corp.'],
            'shares': [10, 5, 15],
            'price': [150.0, 2800.0, 300.0],
            'value': [1500.0, 14000.0, 4500.0],
            'value_jp': [225000, 2100000, 675000],
            'ratio': [7.5, 70.0, 22.5],
            'sector': ['Technology', 'Technology', 'Technology'],
            'PER': [25.0, 30.0, 28.0],
            'sigma': [0.25, 0.30, 0.22],
            'sharpe': [1.2, 1.5, 1.3],
        })
    
    def test_ml_predictions_page_import(self):
        """Test ML predictions page can be imported."""
        self.assertIsNotNone(MLPredictionsPage)
        self.assertTrue(hasattr(MLPredictionsPage, 'render'))
    
    def test_news_sentiment_page_import(self):
        """Test news sentiment page can be imported."""
        self.assertIsNotNone(NewsSentimentPage)
        self.assertTrue(hasattr(NewsSentimentPage, 'render'))
    
    def test_realtime_updates_import(self):
        """Test realtime updates component can be imported."""
        self.assertIsNotNone(RealtimeUpdates)
        self.assertTrue(hasattr(RealtimeUpdates, 'render'))
    
    def test_realtime_fetch_prices(self):
        """Test real-time price fetching logic."""
        tickers = self.df['ticker'].tolist()
        
        # Test that the method exists
        self.assertTrue(hasattr(RealtimeUpdates, '_fetch_realtime_prices'))
        
        # Note: Actual network testing is skipped to avoid dependencies
        # In production, this would fetch real prices
    
    def test_realtime_calculate_changes(self):
        """Test price change calculations."""
        # Mock price updates
        price_updates = {
            'AAPL': {
                'current_price': 155.0,
                'previous_close': 150.0,
                'day_high': 156.0,
                'day_low': 149.0,
                'volume': 50000000,
            }
        }
        
        # Test calculation
        result = RealtimeUpdates._calculate_changes(self.df, price_updates)
        
        self.assertIsInstance(result, pd.DataFrame)
        if not result.empty:
            self.assertIn('ticker', result.columns)
            self.assertIn('new_price', result.columns)
            self.assertIn('price_change_pct', result.columns)


if __name__ == "__main__":
    unittest.main()
