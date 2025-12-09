"""Stock price prediction using machine learning."""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import pickle
import os

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

from .feature_engineering import FeatureEngineer


class StockPredictor:
    """Predict future stock prices using machine learning."""
    
    def __init__(self, model_type: str = 'random_forest'):
        """Initialize the predictor.
        
        Args:
            model_type: Type of model ('random_forest' or 'gradient_boosting')
        """
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn is required for ML predictions. Install with: pip install scikit-learn")
        
        self.model_type = model_type
        self.model = None
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.trained = False
        
        if model_type == 'random_forest':
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42
            )
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=5,
                learning_rate=0.1,
                random_state=42
            )
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def prepare_data(self, price_df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        """Prepare data for training/prediction.
        
        Args:
            price_df: DataFrame with price history (must have 'Close' column)
            
        Returns:
            Tuple of (features_df, target_series)
        """
        # Create features
        df_with_features = FeatureEngineer.create_features(price_df)
        
        # Target: next day's return
        df_with_features['target'] = df_with_features['Close'].shift(-1)
        df_with_features = df_with_features.dropna()
        
        # Get feature columns
        self.feature_columns = FeatureEngineer.get_feature_columns(df_with_features)
        
        X = df_with_features[self.feature_columns]
        y = df_with_features['target']
        
        return X, y
    
    def train(self, price_df: pd.DataFrame, test_size: float = 0.2) -> Dict[str, float]:
        """Train the prediction model.
        
        Args:
            price_df: DataFrame with price history
            test_size: Fraction of data to use for testing
            
        Returns:
            Dictionary with training metrics
        """
        X, y = self.prepare_data(price_df)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, shuffle=False
        )
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train model
        self.model.fit(X_train_scaled, y_train)
        self.trained = True
        
        # Evaluate
        y_pred_train = self.model.predict(X_train_scaled)
        y_pred_test = self.model.predict(X_test_scaled)
        
        metrics = {
            'train_mse': mean_squared_error(y_train, y_pred_train),
            'test_mse': mean_squared_error(y_test, y_pred_test),
            'train_mae': mean_absolute_error(y_train, y_pred_train),
            'test_mae': mean_absolute_error(y_test, y_pred_test),
            'train_r2': r2_score(y_train, y_pred_train),
            'test_r2': r2_score(y_test, y_pred_test),
            'train_size': len(X_train),
            'test_size': len(X_test),
        }
        
        return metrics
    
    def predict_next_day(self, price_df: pd.DataFrame) -> Dict[str, float]:
        """Predict next day's price.
        
        Args:
            price_df: DataFrame with recent price history
            
        Returns:
            Dictionary with prediction results
        """
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
        
        # Prepare features for latest data point
        df_with_features = FeatureEngineer.create_features(price_df)
        
        if df_with_features.empty:
            raise ValueError("Not enough data to create features")
        
        # Get last row (most recent)
        latest_features = df_with_features[self.feature_columns].iloc[-1:]
        
        # Scale and predict
        latest_scaled = self.scaler.transform(latest_features)
        predicted_price = self.model.predict(latest_scaled)[0]
        
        # Calculate prediction confidence (using feature importances if available)
        if hasattr(self.model, 'feature_importances_'):
            confidence = float(np.mean(self.model.feature_importances_))
        else:
            confidence = 0.5
        
        current_price = price_df['Close'].iloc[-1]
        predicted_return = ((predicted_price - current_price) / current_price) * 100
        
        return {
            'current_price': float(current_price),
            'predicted_price': float(predicted_price),
            'predicted_return': float(predicted_return),
            'confidence': confidence,
            'direction': 'up' if predicted_return > 0 else 'down',
        }
    
    def predict_multi_day(self, price_df: pd.DataFrame, days: int = 5) -> pd.DataFrame:
        """Predict multiple days ahead (iterative prediction).
        
        Args:
            price_df: DataFrame with recent price history
            days: Number of days to predict
            
        Returns:
            DataFrame with predictions
        """
        if not self.trained:
            raise ValueError("Model must be trained before making predictions")
        
        predictions = []
        current_df = price_df.copy()
        
        for i in range(days):
            pred = self.predict_next_day(current_df)
            
            # Add prediction to history for next iteration
            next_date = current_df.index[-1] + pd.Timedelta(days=1)
            new_row = pd.DataFrame({
                'Close': [pred['predicted_price']]
            }, index=[next_date])
            
            current_df = pd.concat([current_df, new_row])
            
            predictions.append({
                'date': next_date,
                'day': i + 1,
                'predicted_price': pred['predicted_price'],
                'predicted_return': pred['predicted_return'],
            })
        
        return pd.DataFrame(predictions)
    
    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance scores.
        
        Returns:
            DataFrame with features and their importance scores
        """
        if not self.trained:
            raise ValueError("Model must be trained first")
        
        if not hasattr(self.model, 'feature_importances_'):
            return pd.DataFrame()
        
        importance_df = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df
    
    def save_model(self, filepath: str):
        """Save trained model to file.
        
        Args:
            filepath: Path to save model
        """
        if not self.trained:
            raise ValueError("Model must be trained before saving")
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type,
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
    
    def load_model(self, filepath: str):
        """Load trained model from file.
        
        Args:
            filepath: Path to saved model
        """
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.feature_columns = model_data['feature_columns']
        self.model_type = model_data['model_type']
        self.trained = True


def train_ticker_model(ticker: str, price_history: pd.DataFrame,
                      model_dir: str = "data/ml_models") -> Dict[str, any]:
    """Train a prediction model for a specific ticker.
    
    Args:
        ticker: Stock ticker symbol
        price_history: DataFrame with price history
        model_dir: Directory to save models
        
    Returns:
        Dictionary with model and metrics
    """
    os.makedirs(model_dir, exist_ok=True)
    
    predictor = StockPredictor(model_type='random_forest')
    metrics = predictor.train(price_history)
    
    # Save model
    model_path = os.path.join(model_dir, f"{ticker}_model.pkl")
    predictor.save_model(model_path)
    
    # Get prediction for next day
    prediction = predictor.predict_next_day(price_history)
    
    return {
        'ticker': ticker,
        'predictor': predictor,
        'metrics': metrics,
        'prediction': prediction,
        'model_path': model_path,
    }
