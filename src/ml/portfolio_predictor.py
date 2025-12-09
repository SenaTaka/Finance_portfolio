"""Portfolio-level ML predictions."""

import pandas as pd
from typing import Dict, List
from .predictor import StockPredictor, train_ticker_model


class PortfolioPredictor:
    """Generate ML predictions for entire portfolio."""
    
    def __init__(self, model_dir: str = "data/ml_models"):
        """Initialize portfolio predictor.
        
        Args:
            model_dir: Directory to store/load models
        """
        self.model_dir = model_dir
        self.predictors = {}
    
    def train_portfolio_models(self, ticker_histories: Dict[str, pd.DataFrame],
                              min_data_points: int = 100) -> Dict[str, Dict]:
        """Train models for all tickers in portfolio.
        
        Args:
            ticker_histories: Dict mapping ticker -> price DataFrame
            min_data_points: Minimum data points required for training
            
        Returns:
            Dictionary with training results for each ticker
        """
        results = {}
        
        for ticker, price_df in ticker_histories.items():
            if len(price_df) < min_data_points:
                print(f"  {ticker}: Insufficient data ({len(price_df)} points), skipping")
                continue
            
            try:
                print(f"  {ticker}: Training model...")
                result = train_ticker_model(ticker, price_df, self.model_dir)
                results[ticker] = result
                self.predictors[ticker] = result['predictor']
                print(f"  {ticker}: ✓ R²={result['metrics']['test_r2']:.3f}")
            except Exception as e:
                print(f"  {ticker}: Failed - {e}")
        
        return results
    
    def predict_portfolio(self, ticker_histories: Dict[str, pd.DataFrame],
                         holdings: Dict[str, float]) -> pd.DataFrame:
        """Generate predictions for all holdings.
        
        Args:
            ticker_histories: Dict mapping ticker -> price DataFrame
            holdings: Dict mapping ticker -> shares
            
        Returns:
            DataFrame with predictions
        """
        predictions = []
        
        for ticker, shares in holdings.items():
            if ticker not in self.predictors:
                # Try to train model if not available
                if ticker in ticker_histories:
                    try:
                        result = train_ticker_model(ticker, ticker_histories[ticker], self.model_dir)
                        self.predictors[ticker] = result['predictor']
                    except Exception:
                        continue
                else:
                    continue
            
            try:
                predictor = self.predictors[ticker]
                pred = predictor.predict_next_day(ticker_histories[ticker])
                
                predictions.append({
                    'ticker': ticker,
                    'shares': shares,
                    'current_price': pred['current_price'],
                    'predicted_price': pred['predicted_price'],
                    'predicted_return_%': pred['predicted_return'],
                    'direction': pred['direction'],
                    'confidence': pred['confidence'],
                })
            except Exception as e:
                print(f"Prediction failed for {ticker}: {e}")
        
        return pd.DataFrame(predictions)
    
    def get_portfolio_forecast(self, predictions_df: pd.DataFrame,
                              current_total_value: float) -> Dict[str, float]:
        """Calculate portfolio-level forecast.
        
        Args:
            predictions_df: DataFrame from predict_portfolio
            current_total_value: Current total portfolio value
            
        Returns:
            Dictionary with portfolio forecast
        """
        if predictions_df.empty:
            return {}
        
        # Calculate predicted values
        predictions_df['current_value'] = predictions_df['current_price'] * predictions_df['shares']
        predictions_df['predicted_value'] = predictions_df['predicted_price'] * predictions_df['shares']
        
        current_sum = predictions_df['current_value'].sum()
        predicted_sum = predictions_df['predicted_value'].sum()
        
        # Overall return
        portfolio_return = ((predicted_sum - current_sum) / current_sum * 100) if current_sum > 0 else 0
        
        # Count up/down predictions
        up_count = (predictions_df['direction'] == 'up').sum()
        down_count = (predictions_df['direction'] == 'down').sum()
        
        return {
            'current_value': current_sum,
            'predicted_value': predicted_sum,
            'predicted_return_%': portfolio_return,
            'up_stocks': int(up_count),
            'down_stocks': int(down_count),
            'total_stocks': len(predictions_df),
            'avg_confidence': float(predictions_df['confidence'].mean()),
        }
    
    def get_top_movers(self, predictions_df: pd.DataFrame, top_n: int = 5) -> Dict[str, pd.DataFrame]:
        """Get top predicted movers.
        
        Args:
            predictions_df: DataFrame from predict_portfolio
            top_n: Number of top movers to return
            
        Returns:
            Dictionary with 'gainers' and 'losers' DataFrames
        """
        if predictions_df.empty:
            return {'gainers': pd.DataFrame(), 'losers': pd.DataFrame()}
        
        sorted_df = predictions_df.sort_values('predicted_return_%', ascending=False)
        
        return {
            'gainers': sorted_df.head(top_n),
            'losers': sorted_df.tail(top_n)[::-1],
        }
