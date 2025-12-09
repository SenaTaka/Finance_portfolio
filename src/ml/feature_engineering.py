"""Feature engineering for stock prediction."""

import pandas as pd
import numpy as np
from typing import Dict, List


class FeatureEngineer:
    """Engineer features from stock price data for ML models."""
    
    @staticmethod
    def add_technical_indicators(df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicators to price data.
        
        Args:
            df: DataFrame with 'Close' column and datetime index
            
        Returns:
            DataFrame with added technical indicator columns
        """
        df = df.copy()
        
        # Moving averages
        df['SMA_5'] = df['Close'].rolling(window=5).mean()
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        
        # Exponential moving averages
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # MACD (Moving Average Convergence Divergence)
        df['MACD'] = df['EMA_12'] - df['EMA_26']
        df['MACD_signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_diff'] = df['MACD'] - df['MACD_signal']
        
        # RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # Bollinger Bands
        df['BB_middle'] = df['Close'].rolling(window=20).mean()
        bb_std = df['Close'].rolling(window=20).std()
        df['BB_upper'] = df['BB_middle'] + (bb_std * 2)
        df['BB_lower'] = df['BB_middle'] - (bb_std * 2)
        df['BB_width'] = df['BB_upper'] - df['BB_lower']
        
        # Volatility
        df['Volatility'] = df['Close'].pct_change().rolling(window=20).std()
        
        # Price momentum
        df['Momentum_5'] = df['Close'] - df['Close'].shift(5)
        df['Momentum_20'] = df['Close'] - df['Close'].shift(20)
        
        # Rate of change
        df['ROC_10'] = ((df['Close'] - df['Close'].shift(10)) / df['Close'].shift(10)) * 100
        
        return df
    
    @staticmethod
    def add_lag_features(df: pd.DataFrame, lags: List[int] = [1, 2, 3, 5, 10]) -> pd.DataFrame:
        """Add lagged price features.
        
        Args:
            df: DataFrame with 'Close' column
            lags: List of lag periods
            
        Returns:
            DataFrame with added lag features
        """
        df = df.copy()
        
        for lag in lags:
            df[f'Close_lag_{lag}'] = df['Close'].shift(lag)
            df[f'Return_lag_{lag}'] = df['Close'].pct_change(lag)
        
        return df
    
    @staticmethod
    def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
        """Add time-based features.
        
        Args:
            df: DataFrame with datetime index
            
        Returns:
            DataFrame with added time features
        """
        df = df.copy()
        
        df['day_of_week'] = df.index.dayofweek
        df['day_of_month'] = df.index.day
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # Cyclical encoding for day of week
        df['day_of_week_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['day_of_week_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        # Cyclical encoding for month
        df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
        df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
        
        return df
    
    @staticmethod
    def create_features(df: pd.DataFrame, include_lags: bool = True,
                       include_time: bool = True) -> pd.DataFrame:
        """Create all features for prediction.
        
        Args:
            df: DataFrame with 'Close' column and datetime index
            include_lags: Whether to include lag features
            include_time: Whether to include time features
            
        Returns:
            DataFrame with all engineered features
        """
        df = FeatureEngineer.add_technical_indicators(df)
        
        if include_lags:
            df = FeatureEngineer.add_lag_features(df)
        
        if include_time:
            df = FeatureEngineer.add_time_features(df)
        
        # Drop rows with NaN (from rolling windows and lags)
        df = df.dropna()
        
        return df
    
    @staticmethod
    def get_feature_columns(df: pd.DataFrame) -> List[str]:
        """Get list of feature columns (excluding target and original data).
        
        Args:
            df: DataFrame with features
            
        Returns:
            List of feature column names
        """
        exclude = ['Close', 'Open', 'High', 'Low', 'Volume', 'target']
        return [col for col in df.columns if col not in exclude]
