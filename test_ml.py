"""Tests for machine learning module."""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from src.ml import StockPredictor, FeatureEngineer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


@unittest.skipIf(not ML_AVAILABLE, "ML module not available")
class TestFeatureEngineer(unittest.TestCase):
    """Test feature engineering."""
    
    def setUp(self):
        """Create sample price data."""
        dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # Generate synthetic price data with trend
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
        
        self.price_df = pd.DataFrame({
            'Close': prices
        }, index=dates)
    
    def test_add_technical_indicators(self):
        """Test adding technical indicators."""
        result = FeatureEngineer.add_technical_indicators(self.price_df)
        
        # Check that indicators were added
        self.assertIn('SMA_5', result.columns)
        self.assertIn('SMA_20', result.columns)
        self.assertIn('RSI', result.columns)
        self.assertIn('MACD', result.columns)
        self.assertIn('BB_upper', result.columns)
        
        # Check RSI is in valid range (0-100)
        rsi_values = result['RSI'].dropna()
        self.assertTrue((rsi_values >= 0).all())
        self.assertTrue((rsi_values <= 100).all())
    
    def test_add_lag_features(self):
        """Test adding lag features."""
        result = FeatureEngineer.add_lag_features(self.price_df, lags=[1, 5])
        
        self.assertIn('Close_lag_1', result.columns)
        self.assertIn('Close_lag_5', result.columns)
        self.assertIn('Return_lag_1', result.columns)
    
    def test_add_time_features(self):
        """Test adding time features."""
        result = FeatureEngineer.add_time_features(self.price_df)
        
        self.assertIn('day_of_week', result.columns)
        self.assertIn('month', result.columns)
        self.assertIn('day_of_week_sin', result.columns)
        self.assertIn('month_sin', result.columns)
    
    def test_create_features(self):
        """Test creating all features."""
        result = FeatureEngineer.create_features(self.price_df)
        
        # Should have many feature columns
        self.assertGreater(len(result.columns), 10)
        
        # Should not have NaN (dropped in processing)
        self.assertEqual(result.isna().sum().sum(), 0)


@unittest.skipIf(not ML_AVAILABLE, "ML module not available")
class TestStockPredictor(unittest.TestCase):
    """Test stock predictor."""
    
    def setUp(self):
        """Create sample price data."""
        dates = pd.date_range(start='2022-01-01', end='2023-12-31', freq='D')
        np.random.seed(42)
        
        # Generate synthetic price data
        prices = 100 + np.cumsum(np.random.randn(len(dates)) * 2)
        
        self.price_df = pd.DataFrame({
            'Close': prices
        }, index=dates)
    
    def test_predictor_initialization(self):
        """Test predictor can be initialized."""
        predictor = StockPredictor(model_type='random_forest')
        self.assertIsNotNone(predictor)
        self.assertFalse(predictor.trained)
    
    def test_prepare_data(self):
        """Test data preparation."""
        predictor = StockPredictor()
        X, y = predictor.prepare_data(self.price_df)
        
        self.assertIsInstance(X, pd.DataFrame)
        self.assertIsInstance(y, pd.Series)
        self.assertGreater(len(X), 0)
        self.assertEqual(len(X), len(y))
    
    def test_train_model(self):
        """Test model training."""
        predictor = StockPredictor(model_type='random_forest')
        metrics = predictor.train(self.price_df, test_size=0.2)
        
        self.assertTrue(predictor.trained)
        self.assertIn('test_mse', metrics)
        self.assertIn('test_r2', metrics)
        self.assertGreater(metrics['train_size'], 0)
        self.assertGreater(metrics['test_size'], 0)
    
    def test_predict_next_day(self):
        """Test next day prediction."""
        predictor = StockPredictor()
        predictor.train(self.price_df)
        
        prediction = predictor.predict_next_day(self.price_df)
        
        self.assertIn('current_price', prediction)
        self.assertIn('predicted_price', prediction)
        self.assertIn('predicted_return', prediction)
        self.assertIn('direction', prediction)
        
        self.assertIsInstance(prediction['predicted_price'], float)
        self.assertIn(prediction['direction'], ['up', 'down'])
    
    def test_predict_multi_day(self):
        """Test multi-day prediction."""
        predictor = StockPredictor()
        predictor.train(self.price_df)
        
        predictions = predictor.predict_multi_day(self.price_df, days=5)
        
        self.assertEqual(len(predictions), 5)
        self.assertIn('predicted_price', predictions.columns)
        self.assertIn('day', predictions.columns)
    
    def test_feature_importance(self):
        """Test getting feature importance."""
        predictor = StockPredictor(model_type='random_forest')
        predictor.train(self.price_df)
        
        importance = predictor.get_feature_importance()
        
        self.assertIsInstance(importance, pd.DataFrame)
        self.assertGreater(len(importance), 0)
        self.assertIn('feature', importance.columns)
        self.assertIn('importance', importance.columns)


if __name__ == "__main__":
    unittest.main()
