"""ML Predictions page - Machine learning stock predictions."""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf
from typing import Dict, Optional

try:
    from src.ml import StockPredictor, FeatureEngineer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False


class MLPredictionsPage:
    """ML predictions page showing stock price forecasts."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render the ML predictions page.
        
        Args:
            df: Portfolio DataFrame
        """
        st.title("🤖 Machine Learning Predictions")
        
        if not ML_AVAILABLE:
            st.error("Machine learning module not available. Please install scikit-learn.")
            return
        
        st.markdown("""
        This page uses machine learning models to predict future stock prices based on:
        - Technical indicators (RSI, MACD, Bollinger Bands)
        - Historical price patterns
        - Volume trends
        """)
        
        # Stock selector
        tickers = df['ticker'].unique().tolist()
        selected_ticker = st.selectbox("Select Stock for Prediction", tickers)
        
        if selected_ticker:
            MLPredictionsPage._render_stock_prediction(selected_ticker)
        
        # Portfolio-level predictions
        st.divider()
        st.subheader("📈 Portfolio Overview Predictions")
        
        if st.button("Generate Predictions for All Stocks"):
            MLPredictionsPage._render_portfolio_predictions(df)
    
    @staticmethod
    def _render_stock_prediction(ticker: str):
        """Render prediction for a single stock.
        
        Args:
            ticker: Stock ticker symbol
        """
        with st.spinner(f"Fetching data and training model for {ticker}..."):
            try:
                # Fetch historical data (1 year)
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                stock = yf.Ticker(ticker)
                history = stock.history(start=start_date, end=end_date)
                
                if history.empty or len(history) < 100:
                    st.warning(f"Insufficient data for {ticker}. Need at least 100 days of history.")
                    return
                
                # Train model
                predictor = StockPredictor(model_type='random_forest')
                metrics = predictor.train(history, test_size=0.2)
                
                # Display model performance
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("R² Score (Test)", f"{metrics['test_r2']:.3f}")
                with col2:
                    st.metric("MAE (Test)", f"${metrics['test_mae']:.2f}")
                with col3:
                    st.metric("Training Size", f"{metrics['train_size']} days")
                
                # Next day prediction
                st.subheader("📊 Next Day Prediction")
                prediction = predictor.predict_next_day(history)
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Current Price", f"${prediction['current_price']:.2f}")
                with col2:
                    direction_emoji = "📈" if prediction['direction'] == 'up' else "📉"
                    st.metric(
                        "Predicted Price",
                        f"${prediction['predicted_price']:.2f}",
                        delta=f"{prediction['predicted_return']:.2f}%"
                    )
                with col3:
                    st.metric("Direction", f"{direction_emoji} {prediction['direction'].upper()}")
                
                # Multi-day forecast
                st.subheader("📅 5-Day Forecast")
                forecast = predictor.predict_multi_day(history, days=5)
                
                # Create forecast chart
                fig = go.Figure()
                
                # Historical prices (last 30 days)
                recent_history = history.tail(30)
                fig.add_trace(go.Scatter(
                    x=recent_history.index,
                    y=recent_history['Close'],
                    mode='lines',
                    name='Historical',
                    line=dict(color='blue', width=2)
                ))
                
                # Predictions
                fig.add_trace(go.Scatter(
                    x=forecast['date'],
                    y=forecast['predicted_price'],
                    mode='lines+markers',
                    name='Forecast',
                    line=dict(color='red', width=2, dash='dash')
                ))
                
                fig.update_layout(
                    title=f"{ticker} Price Forecast",
                    xaxis_title="Date",
                    yaxis_title="Price (USD)",
                    hovermode='x unified',
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display forecast table
                st.dataframe(
                    forecast[['day', 'predicted_price', 'predicted_return']].style.format({
                        'predicted_price': '${:.2f}',
                        'predicted_return': '{:.2f}%'
                    }),
                    use_container_width=True
                )
                
                # Feature importance
                with st.expander("🔍 Feature Importance"):
                    importance = predictor.get_feature_importance()
                    if not importance.empty:
                        # Show top 15 features
                        top_features = importance.head(15)
                        
                        fig_importance = px.bar(
                            top_features,
                            x='importance',
                            y='feature',
                            orientation='h',
                            title='Top 15 Most Important Features'
                        )
                        fig_importance.update_layout(height=500)
                        st.plotly_chart(fig_importance, use_container_width=True)
                    else:
                        st.info("Feature importance not available for this model.")
                
            except Exception as e:
                st.error(f"Error generating prediction: {str(e)}")
                st.exception(e)
    
    @staticmethod
    def _render_portfolio_predictions(df: pd.DataFrame):
        """Render predictions for all stocks in portfolio.
        
        Args:
            df: Portfolio DataFrame
        """
        tickers = df['ticker'].unique().tolist()
        results = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, ticker in enumerate(tickers):
            status_text.text(f"Processing {ticker}... ({i+1}/{len(tickers)})")
            
            try:
                # Fetch data
                end_date = datetime.now()
                start_date = end_date - timedelta(days=365)
                
                stock = yf.Ticker(ticker)
                history = stock.history(start=start_date, end=end_date)
                
                if len(history) < 100:
                    continue
                
                # Train and predict
                predictor = StockPredictor(model_type='random_forest')
                predictor.train(history, test_size=0.2)
                prediction = predictor.predict_next_day(history)
                
                results.append({
                    'ticker': ticker,
                    'current_price': prediction['current_price'],
                    'predicted_price': prediction['predicted_price'],
                    'predicted_return': prediction['predicted_return'],
                    'direction': prediction['direction']
                })
                
            except Exception as e:
                st.warning(f"Could not generate prediction for {ticker}: {str(e)}")
            
            progress_bar.progress((i + 1) / len(tickers))
        
        status_text.empty()
        progress_bar.empty()
        
        if results:
            # Create DataFrame
            predictions_df = pd.DataFrame(results)
            predictions_df = predictions_df.sort_values('predicted_return', ascending=False)
            
            # Display summary metrics
            st.subheader("📊 Predictions Summary")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                bullish = len(predictions_df[predictions_df['direction'] == 'up'])
                st.metric("Bullish Signals", f"{bullish}/{len(predictions_df)}")
            
            with col2:
                avg_return = predictions_df['predicted_return'].mean()
                st.metric("Average Predicted Return", f"{avg_return:.2f}%")
            
            with col3:
                max_return = predictions_df['predicted_return'].max()
                top_stock = predictions_df.iloc[0]['ticker']
                st.metric("Top Performer", f"{top_stock} ({max_return:.2f}%)")
            
            # Display table
            st.dataframe(
                predictions_df.style.format({
                    'current_price': '${:.2f}',
                    'predicted_price': '${:.2f}',
                    'predicted_return': '{:.2f}%'
                }).background_gradient(subset=['predicted_return'], cmap='RdYlGn'),
                use_container_width=True
            )
            
            # Chart
            fig = px.bar(
                predictions_df,
                x='ticker',
                y='predicted_return',
                color='direction',
                color_discrete_map={'up': 'green', 'down': 'red'},
                title='Predicted Returns by Stock'
            )
            fig.update_layout(xaxis_title="Stock", yaxis_title="Predicted Return (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No predictions could be generated for the portfolio.")
