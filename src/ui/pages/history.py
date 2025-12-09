"""History page - Performance tracking and comparison."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import glob
import os
import re
from datetime import datetime, timedelta
import yfinance as yf
from ..constants import SP500_TICKERS, TREASURY_TICKER, DEFAULT_RISK_FREE_RATE


class HistoryPage:
    """History page for performance tracking and comparison."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render the history page.
        
        Args:
            df: Portfolio DataFrame
        """
        st.title("📈 Performance History")
        
        # Create tabs
        tab1, tab2 = st.tabs(["Portfolio Value History", "Performance vs S&P 500"])
        
        with tab1:
            HistoryPage._render_value_history()
        
        with tab2:
            HistoryPage._render_sp500_comparison(df)
    
    @staticmethod
    def _render_value_history():
        """Render portfolio value history chart."""
        st.subheader("📈 Portfolio Value History")
        
        # Collect historical total values from result files
        us_history_files = sorted(
            glob.glob(os.path.join("output", "portfolio_result_*.csv")), 
            key=os.path.getmtime
        )
        jp_history_files = sorted(
            glob.glob(os.path.join("output", "portfolio_jp_result_*.csv")), 
            key=os.path.getmtime
        )
        
        history_data = []
        
        for f_path in us_history_files + jp_history_files:
            try:
                match = re.search(r'_result_(\d{8})_(\d{6})\.csv', f_path)
                if match:
                    date_str = match.group(1)
                    time_str = match.group(2)
                    dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
                    
                    hist_df = pd.read_csv(f_path)
                    if 'value_jp' in hist_df.columns:
                        total = hist_df['value_jp'].sum()
                        source = "US" if "portfolio_result_" in f_path else "JP"
                        history_data.append({
                            'datetime': dt,
                            'date': dt.date(),
                            'total_value_jp': total,
                            'source': source
                        })
            except Exception:
                pass
        
        if history_data:
            history_df = pd.DataFrame(history_data)
            # Group by date and source, take latest value per day per source
            history_df = history_df.sort_values('datetime').groupby(['date', 'source']).last().reset_index()
            
            # Pivot to combine US and JP values by date
            pivot_df = history_df.pivot(index='date', columns='source', values='total_value_jp').reset_index()
            pivot_df = pivot_df.ffill().fillna(0)
            
            # Calculate combined total
            cols_to_sum = [c for c in ['US', 'JP'] if c in pivot_df.columns]
            if cols_to_sum:
                pivot_df['Combined'] = pivot_df[cols_to_sum].sum(axis=1)
                
                fig_history = px.line(
                    pivot_df, 
                    x='date', 
                    y='Combined',
                    title='Portfolio Value Over Time (JPY)',
                    labels={'date': 'Date', 'Combined': 'Total Value (JPY)'},
                    markers=True
                )
                fig_history.update_layout(
                    margin=dict(l=10, r=10, t=40, b=40),
                    showlegend=False,
                    yaxis=dict(tickformat=","),
                )
                st.plotly_chart(fig_history, width="stretch")
                
                # Show summary stats
                if len(pivot_df) > 1:
                    latest = pivot_df['Combined'].iloc[-1]
                    first = pivot_df['Combined'].iloc[0]
                    change = latest - first
                    change_pct = (change / first * 100) if first > 0 else 0
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Change", f"¥{change:,.0f}", f"{change_pct:+.1f}%")
                    with col2:
                        st.metric("Data Points", len(pivot_df))
        else:
            st.info("No historical data available yet. Run 'Update Data' to start tracking.")
    
    @staticmethod
    def _render_sp500_comparison(df: pd.DataFrame):
        """Render portfolio performance comparison with S&P 500."""
        st.subheader("📊 Performance & Sharpe Ratio vs S&P 500")
        
        # Period selection
        period_options = {
            "1 Month": 30,
            "3 Months": 90,
            "6 Months": 180,
            "1 Year": 365,
            "YTD": "ytd",
            "3 Years": 365 * 3
        }
        selected_period_label = st.selectbox("Select Period", list(period_options.keys()))
        
        # Calculate dates
        end_date = datetime.now()
        if selected_period_label == "YTD":
            start_date = datetime(end_date.year, 1, 1)
        else:
            days = period_options[selected_period_label]
            start_date = end_date - timedelta(days=days)
        
        st.caption(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Calculate portfolio performance vs S&P 500
        if 'ticker' not in df.columns or 'shares' not in df.columns:
            st.info("Portfolio data not available for performance comparison.")
            return
        
        try:
            # Get S&P 500 data - try multiple tickers
            sp500_hist = None
            for ticker in SP500_TICKERS:
                try:
                    sp500 = yf.Ticker(ticker)
                    sp500_hist = sp500.history(start=start_date, end=end_date)
                    if not sp500_hist.empty:
                        break
                except Exception:
                    continue
            
            # Get Risk Free Rate
            tnx = yf.Ticker(TREASURY_TICKER)
            tnx_hist = tnx.history(period="1d")
            if not tnx_hist.empty:
                rf_rate = tnx_hist['Close'].iloc[-1] / 100.0
            else:
                rf_rate = DEFAULT_RISK_FREE_RATE
            
            if sp500_hist.empty:
                st.info("Unable to fetch S&P 500 data.")
                return
            
            # Ensure timezone naive
            if sp500_hist.index.tz is not None:
                sp500_hist.index = sp500_hist.index.tz_localize(None)
            
            # Filter to USD stocks for fair comparison
            if 'currency' in df.columns:
                usd_df = df[df['currency'] == 'USD']
            else:
                usd_df = df
            
            tickers_in_portfolio = usd_df['ticker'].tolist()
            shares_dict = dict(zip(usd_df['ticker'], usd_df['shares']))
            
            active_tickers = [t for t in tickers_in_portfolio if shares_dict.get(t, 0) > 0]
            
            if not active_tickers:
                st.info("No active USD holdings found in portfolio.")
                return
            
            # Batch download
            portfolio_data = yf.download(
                active_tickers,
                start=start_date,
                end=end_date,
                progress=False,
                group_by='ticker',
                auto_adjust=True
            )
            
            # Extract close prices
            portfolio_hist = {}
            for ticker in active_tickers:
                try:
                    if len(active_tickers) == 1:
                        if 'Close' in portfolio_data.columns:
                            close_data = portfolio_data['Close']
                            if not close_data.empty:
                                if close_data.index.tz is not None:
                                    close_data.index = close_data.index.tz_localize(None)
                                portfolio_hist[ticker] = close_data
                    else:
                        if ticker in portfolio_data.columns.get_level_values(0):
                            close_data = portfolio_data[ticker]['Close']
                            if not close_data.empty and close_data.notna().sum() > 0:
                                if close_data.index.tz is not None:
                                    close_data.index = close_data.index.tz_localize(None)
                                portfolio_hist[ticker] = close_data
                except (KeyError, TypeError):
                    continue
            
            if not portfolio_hist:
                st.info("Unable to fetch historical data for portfolio tickers.")
                return
            
            # Create price DataFrame
            price_df = pd.DataFrame(portfolio_hist)
            
            # Validate data coverage
            min_data_points = len(sp500_hist) * 0.5
            valid_columns = [col for col in price_df.columns 
                           if price_df[col].notna().sum() >= min_data_points]
            
            if not valid_columns:
                st.info("Insufficient data coverage for portfolio tickers.")
                return
            
            price_df = price_df[valid_columns]
            price_df = price_df.ffill().bfill().dropna()
            
            if price_df.empty:
                st.info("Insufficient price data to calculate performance comparison.")
                return
            
            # Calculate portfolio value over time
            portfolio_value = pd.Series(0.0, index=price_df.index)
            for ticker in price_df.columns:
                portfolio_value += price_df[ticker] * shares_dict.get(ticker, 0)
            
            # Normalize to percentage returns
            portfolio_return_series = (portfolio_value / portfolio_value.iloc[0] - 1) * 100
            
            # Align S&P 500 data
            sp500_aligned = sp500_hist['Close'].reindex(price_df.index).ffill().bfill()
            sp500_return_series = (sp500_aligned / sp500_aligned.iloc[0] - 1) * 100
            
            # Calculate Sharpe Ratios
            port_daily_ret = portfolio_value.pct_change().dropna()
            sp500_daily_ret = sp500_aligned.pct_change().dropna()
            
            port_ann_ret = port_daily_ret.mean() * 252
            port_ann_vol = port_daily_ret.std() * np.sqrt(252)
            port_sharpe = (port_ann_ret - rf_rate) / port_ann_vol if port_ann_vol > 0 else 0
            
            sp500_ann_ret = sp500_daily_ret.mean() * 252
            sp500_ann_vol = sp500_daily_ret.std() * np.sqrt(252)
            sp500_sharpe = (sp500_ann_ret - rf_rate) / sp500_ann_vol if sp500_ann_vol > 0 else 0
            
            # Create comparison chart
            comparison_df = pd.DataFrame({
                'Date': price_df.index,
                'Portfolio': portfolio_return_series.values,
                'S&P 500': sp500_return_series.values
            })
            
            fig_comparison = go.Figure()
            
            fig_comparison.add_trace(go.Scatter(
                x=comparison_df['Date'],
                y=comparison_df['Portfolio'],
                mode='lines',
                name='Portfolio',
                line=dict(color='#1f77b4', width=2)
            ))
            
            fig_comparison.add_trace(go.Scatter(
                x=comparison_df['Date'],
                y=comparison_df['S&P 500'],
                mode='lines',
                name='S&P 500',
                line=dict(color='#ff7f0e', width=2)
            ))
            
            fig_comparison.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
            
            fig_comparison.update_layout(
                title=f'Portfolio vs S&P 500 Performance ({selected_period_label})',
                xaxis_title='Date',
                yaxis_title='Return (%)',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(l=10, r=10, t=40, b=80),
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_comparison, width="stretch")
            
            # Show performance summary
            portfolio_total_return = portfolio_return_series.iloc[-1]
            sp500_total_return = sp500_return_series.iloc[-1]
            outperformance = portfolio_total_return - sp500_total_return
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Portfolio Return", f"{portfolio_total_return:+.2f}%", delta=None)
                st.metric("Portfolio Sharpe", f"{port_sharpe:.2f}")
            with col2:
                st.metric("S&P 500 Return", f"{sp500_total_return:+.2f}%", delta=None)
                st.metric("S&P 500 Sharpe", f"{sp500_sharpe:.2f}")
            with col3:
                delta_color = "normal" if outperformance >= 0 else "inverse"
                st.metric(
                    "Outperformance",
                    f"{outperformance:+.2f}%",
                    delta=f"{'Beat' if outperformance >= 0 else 'Underperformed'} S&P 500",
                    delta_color=delta_color
                )
                st.metric("Risk Free Rate", f"{rf_rate*100:.2f}%")
        
        except Exception as e:
            st.warning(f"Could not calculate performance comparison: {e}")
