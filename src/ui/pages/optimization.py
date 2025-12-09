"""Optimization page - Efficient frontier and Sharpe optimization."""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import glob
import os
import re

try:
    from efficient_frontier import (
        calculate_efficient_frontier,
        generate_random_portfolios,
        get_portfolio_suggestions,
        prepare_data_for_frontier,
        backtest_portfolio,
    )
    EFFICIENT_FRONTIER_AVAILABLE = True
except ImportError:
    EFFICIENT_FRONTIER_AVAILABLE = False

try:
    from sharpe_optimized import (
        calculate_sharpe_scores,
        calculate_target_weights,
        calculate_trade_plan
    )
except ImportError:
    pass

try:
    from portfolio_calculator import load_cache
except ImportError:
    load_cache = None


class OptimizationPage:
    """Optimization page for portfolio optimization strategies."""
    
    @staticmethod
    def render(df: pd.DataFrame, selected_file: str = None, view_mode: str = None):
        """Render the optimization page.
        
        Args:
            df: Portfolio DataFrame
            selected_file: Selected file path (if any)
            view_mode: Current view mode
        """
        st.title("🎯 Portfolio Optimization")
        
        # Create tabs for different optimization strategies
        tab1, tab2 = st.tabs(["Efficient Frontier", "Sharpe Optimization"])
        
        with tab1:
            OptimizationPage._render_efficient_frontier(df)
        
        with tab2:
            OptimizationPage._render_sharpe_optimization(df, selected_file, view_mode)
    
    @staticmethod
    def _render_efficient_frontier(df: pd.DataFrame):
        """Render efficient frontier analysis."""
        st.subheader("📈 Efficient Frontier (Modern Portfolio Theory)")
        
        if not EFFICIENT_FRONTIER_AVAILABLE:
            st.warning("The scipy library is required to use the efficient frontier feature.")
            return
        
        if load_cache is None:
            st.warning("Portfolio calculator module not available.")
            return
        
        # Build price history from cache
        cache = load_cache()
        price_data = {}
        valid_tickers = []
        
        for _, row in df.iterrows():
            ticker = row['ticker']
            cached = cache.get(ticker, {})
            if cached.get('history') and cached.get('history_index'):
                try:
                    hist_series = pd.Series(
                        cached['history'],
                        index=pd.to_datetime(cached['history_index'])
                    )
                    if len(hist_series) > 20:
                        price_data[ticker] = hist_series
                        valid_tickers.append(ticker)
                except (ValueError, TypeError):
                    pass
        
        if len(valid_tickers) < 2:
            st.info("At least 2 stocks with price data are required. Please run 'Update Data' to fetch data.")
            return
        
        try:
            # Create aligned price DataFrame
            price_df = pd.DataFrame(price_data)
            price_df = price_df.ffill().bfill().dropna()
            
            if len(price_df) <= 20:
                st.info("More price history data is required to calculate the efficient frontier.")
                return
            
            # Prepare data for efficient frontier
            expected_returns, cov_matrix, tickers = prepare_data_for_frontier(price_df)
            
            # Get current weights from portfolio
            current_weights = None
            if 'value' in df.columns:
                total_val = df[df['ticker'].isin(valid_tickers)]['value'].sum()
                if total_val > 0:
                    weights_list = []
                    for t in tickers:
                        val = df[df['ticker'] == t]['value'].sum()
                        weights_list.append(val / total_val)
                    current_weights = np.array(weights_list)
            
            # Calculate efficient frontier
            frontier_df = calculate_efficient_frontier(
                expected_returns, cov_matrix, n_points=50
            )
            
            # Generate random portfolios for comparison
            random_df = generate_random_portfolios(
                expected_returns, cov_matrix, n_portfolios=500
            )
            
            # Get portfolio suggestions
            suggestions = get_portfolio_suggestions(
                tickers, expected_returns, cov_matrix, current_weights
            )
            
            # Render backtest comparison
            OptimizationPage._render_backtest(df, price_df, tickers, suggestions, current_weights)
            
            # Render efficient frontier chart
            OptimizationPage._render_frontier_chart(
                frontier_df, random_df, suggestions, tickers, expected_returns, cov_matrix
            )
            
            # Render rebalancing recommendation
            if 'value_jp' in df.columns:
                total_value_jp = df['value_jp'].sum()
                OptimizationPage._render_rebalancing_recommendation(
                    suggestions, tickers, total_value_jp
                )
            
        except Exception as e:
            st.warning(f"Error calculating efficient frontier: {e}")
    
    @staticmethod
    def _render_backtest(df, price_df, tickers, suggestions, current_weights):
        """Render backtest comparison."""
        st.markdown("##### パフォーマンス比較 (バックテスト)")
        
        period_options = {"3M": 63, "6M": 126, "1Y": 252, "All": None}
        selected_period = st.selectbox(
            "表示期間を選択",
            options=list(period_options.keys()),
            index=0,
            help="バックテストに使用する期間を選択します",
        )
        
        days = period_options[selected_period]
        price_df_filtered = price_df.copy()
        if days:
            cutoff = price_df.index.max() - pd.Timedelta(days=days)
            price_df_filtered = price_df[price_df.index >= cutoff]
        
        if len(price_df_filtered) < 20:
            st.warning("選択した期間では十分な価格データがありません。")
            return
        
        def _weights_to_array(weight_dict: dict) -> np.ndarray:
            return np.array([weight_dict.get(t, 0) for t in tickers], dtype=float)
        
        portfolio_candidates = {}
        
        if current_weights is not None and 'current' in suggestions:
            portfolio_candidates['現在のポートフォリオ'] = current_weights
        
        for key in ['max_sharpe', 'min_volatility']:
            if key in suggestions:
                portfolio_candidates[suggestions[key]['name_jp']] = _weights_to_array(suggestions[key]['weights'])
        
        portfolio_candidates['等金額ベンチマーク'] = np.array([1.0 / len(tickers)] * len(tickers))
        
        backtest_results = {}
        for name, weights_arr in portfolio_candidates.items():
            try:
                result = backtest_portfolio(weights_arr, price_df_filtered)
                backtest_results[name] = result
            except ValueError as e:
                st.warning(f"{name} のバックテストに失敗しました: {e}")
        
        if backtest_results:
            fig_perf = go.Figure()
            for name, result in backtest_results.items():
                fig_perf.add_trace(go.Scatter(
                    x=result['cumulative_returns'].index,
                    y=result['cumulative_returns'],
                    mode='lines',
                    name=name,
                    hovertemplate="%{x|%Y-%m-%d}<br>累積リターン: %{y:.2f}x<extra></extra>",
                ))
            fig_perf.update_layout(
                title="累積リターン比較",
                yaxis_title="累積リターン (倍率)",
                xaxis_title="日付",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(l=10, r=10, t=40, b=80),
            )
            st.plotly_chart(fig_perf, width="stretch")
            
            metric_cols = st.columns(min(4, len(backtest_results)))
            col_cycle = iter(metric_cols)
            for name, result in backtest_results.items():
                try:
                    col = next(col_cycle)
                except StopIteration:
                    metric_cols = st.columns(min(4, len(backtest_results)))
                    col_cycle = iter(metric_cols)
                    col = next(col_cycle)
                metrics = result['metrics']
                col.metric(
                    name,
                    f"{metrics['total_return']*100:.2f}%",
                    delta=f"年率 {metrics['annualized_return']*100:.2f}%"
                )
                col.caption(
                    f"Vol: {metrics['volatility']*100:.2f}% | Max DD: {metrics['max_drawdown']*100:.2f}%"
                )
    
    @staticmethod
    def _render_frontier_chart(frontier_df, random_df, suggestions, tickers, expected_returns, cov_matrix):
        """Render the efficient frontier chart."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_ef = go.Figure()
            
            # Add random portfolios
            fig_ef.add_trace(go.Scatter(
                x=random_df['volatility'] * 100,
                y=random_df['return'] * 100,
                mode='markers',
                marker=dict(
                    color=random_df['sharpe'],
                    colorscale='Viridis',
                    size=5,
                    opacity=0.5,
                    colorbar=dict(title='Sharpe')
                ),
                name='Random Portfolios',
                hovertemplate='Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>'
            ))
            
            # Add efficient frontier line
            if not frontier_df.empty:
                fig_ef.add_trace(go.Scatter(
                    x=frontier_df['volatility'] * 100,
                    y=frontier_df['return'] * 100,
                    mode='lines',
                    line=dict(color='red', width=3),
                    name='Efficient Frontier',
                    hovertemplate='Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>'
                ))
            
            # Add special portfolios
            if 'max_sharpe' in suggestions:
                max_sharpe_data = suggestions['max_sharpe']
                fig_ef.add_trace(go.Scatter(
                    x=[max_sharpe_data['volatility']],
                    y=[max_sharpe_data['expected_return']],
                    mode='markers+text',
                    marker=dict(color='gold', size=15, symbol='star'),
                    name='Max Sharpe',
                    text=['★ Max Sharpe'],
                    textposition='top right',
                    hovertemplate=f"Max Sharpe<br>Vol: {max_sharpe_data['volatility']:.1f}%<br>Return: {max_sharpe_data['expected_return']:.1f}%<extra></extra>"
                ))
            
            if 'min_volatility' in suggestions:
                min_vol_data = suggestions['min_volatility']
                fig_ef.add_trace(go.Scatter(
                    x=[min_vol_data['volatility']],
                    y=[min_vol_data['expected_return']],
                    mode='markers+text',
                    marker=dict(color='blue', size=15, symbol='diamond'),
                    name='Min Volatility',
                    text=['◆ Min Vol'],
                    textposition='top right',
                    hovertemplate=f"Min Volatility<br>Vol: {min_vol_data['volatility']:.1f}%<br>Return: {min_vol_data['expected_return']:.1f}%<extra></extra>"
                ))
            
            if 'current' in suggestions:
                current_data = suggestions['current']
                fig_ef.add_trace(go.Scatter(
                    x=[current_data['volatility']],
                    y=[current_data['expected_return']],
                    mode='markers+text',
                    marker=dict(color='green', size=15, symbol='circle'),
                    name='Current Portfolio',
                    text=['● Current'],
                    textposition='top right',
                    hovertemplate=f"Current<br>Vol: {current_data['volatility']:.1f}%<br>Return: {current_data['expected_return']:.1f}%<extra></extra>"
                ))
            
            # Add individual assets
            for i, ticker in enumerate(tickers):
                asset_return = expected_returns[i] * 100
                asset_vol = np.sqrt(cov_matrix[i, i]) * 100
                fig_ef.add_trace(go.Scatter(
                    x=[asset_vol],
                    y=[asset_return],
                    mode='markers',
                    marker=dict(color='gray', size=8, symbol='x'),
                    name=ticker,
                    hovertemplate=f"{ticker}<br>Vol: {asset_vol:.1f}%<br>Return: {asset_return:.1f}%<extra></extra>"
                ))
            
            fig_ef.update_layout(
                title='Efficient Frontier',
                xaxis_title='Volatility (Risk) [%]',
                yaxis_title='Expected Return [%]',
                legend=dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    font=dict(size=10)
                ),
                margin=dict(l=10, r=10, t=40, b=100),
                hovermode='closest'
            )
            
            st.plotly_chart(fig_ef, width="stretch")
        
        with col2:
            st.markdown("#### Portfolio Suggestions")
            
            for key, sug in suggestions.items():
                with st.expander(f"📊 {sug['name']}", expanded=(key == 'max_sharpe')):
                    st.markdown(f"**{sug['description']}**")
                    st.markdown(f"- Expected Return: **{sug['expected_return']:.1f}%**")
                    st.markdown(f"- Volatility: **{sug['volatility']:.1f}%**")
                    st.markdown(f"- Sharpe Ratio: **{sug['sharpe']:.2f}**")
                    
                    st.markdown("**Allocation Weights:**")
                    weights_df = pd.DataFrame([
                        {'Ticker': t, 'Weight': f"{w*100:.1f}%"}
                        for t, w in sug['weights'].items()
                        if w > 0.01
                    ])
                    if not weights_df.empty:
                        weights_df = weights_df.sort_values('Weight', ascending=False)
                        st.dataframe(weights_df, hide_index=True, width="stretch")
    
    @staticmethod
    def _render_rebalancing_recommendation(suggestions, tickers, total_value_jp):
        """Render rebalancing recommendations."""
        st.markdown("---")
        st.markdown("#### 🎯 Rebalancing Recommendation")
        
        if 'current' not in suggestions:
            st.info("Current portfolio allocation data not available.")
            return
        
        current = suggestions['current']
        max_sharpe = suggestions['max_sharpe']
        
        improvement_sharpe = max_sharpe['sharpe'] - current['sharpe']
        improvement_return = max_sharpe['expected_return'] - current['expected_return']
        risk_change = max_sharpe['volatility'] - current['volatility']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric(
                "Sharpe Ratio Improvement",
                f"{improvement_sharpe:+.2f}",
                delta=f"From {current['sharpe']:.2f} to {max_sharpe['sharpe']:.2f}"
            )
        with col2:
            st.metric(
                "Expected Return Change",
                f"{improvement_return:+.1f}%",
                delta="per year"
            )
        with col3:
            st.metric(
                "Volatility Change",
                f"{risk_change:+.1f}%",
                delta="risk adjustment"
            )
        
        # Calculate required trades
        st.markdown("##### Required Trades to Reach Max Sharpe Portfolio")
        trade_data = []
        for ticker in tickers:
            current_weight = current['weights'].get(ticker, 0)
            target_weight = max_sharpe['weights'].get(ticker, 0)
            weight_diff = target_weight - current_weight
            trade_amount = weight_diff * total_value_jp
            
            if abs(trade_amount) > 10000:
                trade_data.append({
                    'Ticker': ticker,
                    'Current %': f"{current_weight*100:.1f}%",
                    'Target %': f"{target_weight*100:.1f}%",
                    'Trade (JPY)': int(trade_amount),
                    'Action': 'Buy' if trade_amount > 0 else 'Sell'
                })
        
        if trade_data:
            trade_df = pd.DataFrame(trade_data)
            st.dataframe(
                trade_df,
                width="stretch",
                hide_index=True,
                column_config={
                    'Trade (JPY)': st.column_config.NumberColumn(format="¥%d")
                }
            )
        else:
            st.info("Your current portfolio is close to optimal allocation.")
    
    @staticmethod
    def _render_sharpe_optimization(df: pd.DataFrame, selected_file: str = None, view_mode: str = None):
        """Render Sharpe optimization analysis."""
        st.header("Sharpe Optimized Portfolio")
        st.write("Displays the proposed allocation and trade plan when optimizing the portfolio based on each stock's Sharpe ratio.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            param_a = st.slider("Sharpe Ratio Emphasis (a)", min_value=0.5, max_value=3.0, value=1.0, step=0.5, key="slider_sharpe_a")
        with col_b:
            param_b = st.slider("Volatility Emphasis (b)", min_value=0.5, max_value=3.0, value=1.0, step=0.5, key="slider_vol_b")
        
        if 'sharpe' not in df.columns or 'sigma' not in df.columns:
            st.info("Sharpe Ratio data not available.")
            return
        
        # Ensure numeric types
        df['sharpe'] = pd.to_numeric(df['sharpe'], errors='coerce')
        df['sigma'] = pd.to_numeric(df['sigma'], errors='coerce')
        
        # Calculate scores and weights
        scores = calculate_sharpe_scores(df, a=param_a, b=param_b)
        target_weights = calculate_target_weights(scores)
        
        # Calculate trade plan
        total_value_jp = df['value_jp'].sum() if 'value_jp' in df.columns else None
        if total_value_jp is None:
            st.info("JPY valuation required for trade plan.")
            return
        
        usd_jpy_rate = df['usd_jpy_rate'].iloc[0] if 'usd_jpy_rate' in df.columns else 100.0
        trade_plan_df = calculate_trade_plan(df, target_weights, total_value_jp, usd_jpy_rate)
        
        # Display Trade Plan
        st.subheader("Rebalancing Proposal")
        
        display_plan = trade_plan_df.copy()
        display_plan['Action'] = display_plan['diff_value_jp'].apply(lambda x: 'Buy' if x > 0 else 'Sell')
        display_plan['Trade Amount (JPY)'] = display_plan['diff_value_jp'].abs()
        display_plan['Trade Shares'] = display_plan['diff_shares'].apply(lambda x: int(x) if not pd.isna(x) else 0).abs()
        
        display_plan = display_plan[display_plan['Trade Amount (JPY)'] > 1000]
        
        st.dataframe(
            display_plan[['ticker', 'name', 'current_weight', 'target_weight', 'Action', 'Trade Amount (JPY)', 'Trade Shares']],
            width="stretch",
            hide_index=True,
            column_config={
                "current_weight": st.column_config.NumberColumn("Current %", format="%.2f%%"),
                "target_weight": st.column_config.NumberColumn("Target %", format="%.2f%%"),
                "Trade Amount (JPY)": st.column_config.NumberColumn("Amount (JPY)", format="¥%d"),
            }
        )
        
        # Sharpe Ratio comparison
        OptimizationPage._render_sharpe_comparison(df, target_weights, selected_file, view_mode)
    
    @staticmethod
    def _render_sharpe_comparison(df, target_weights, selected_file, view_mode):
        """Render Sharpe ratio comparison chart."""
        st.subheader("Sharpe Ratio (Current vs Optimized)")
        
        try:
            # Load correlation matrix
            corr_df = None
            if selected_file:
                match = re.search(r'_result_(\d{8}_\d{6})\.csv', selected_file)
            elif view_mode == "Combined (Latest)":
                corr_files = glob.glob(os.path.join("output", "*_corr_*.csv"))
                if corr_files:
                    corr_files.sort(key=os.path.getmtime, reverse=True)
                    match = re.search(r'_corr_(\d{8}_\d{6})\.csv', corr_files[0])
                else:
                    match = None
            else:
                match = None
            
            if match:
                timestamp = match.group(1)
                corr_file_us = os.path.join("output", f"portfolio_corr_{timestamp}.csv")
                corr_file_jp = os.path.join("output", f"portfolio_jp_corr_{timestamp}.csv")
                
                if os.path.exists(corr_file_us):
                    corr_df = pd.read_csv(corr_file_us, index_col=0)
                elif os.path.exists(corr_file_jp):
                    corr_df = pd.read_csv(corr_file_jp, index_col=0)
            
            if corr_df is not None:
                common_tickers = [t for t in df['ticker'] if t in corr_df.index]
                if common_tickers:
                    sub_df = df[df['ticker'].isin(common_tickers)].set_index('ticker')
                    sub_corr = corr_df.loc[common_tickers, common_tickers]
                    
                    w_current = sub_df['ratio'] / 100.0
                    w_current = w_current / w_current.sum()
                    
                    w_opt = pd.Series({t: target_weights.get(t, 0) for t in common_tickers})
                    w_opt = w_opt / w_opt.sum()
                    
                    sigmas = sub_df['sigma']
                    rf = 4.0
                    
                    cov_matrix = pd.DataFrame(index=common_tickers, columns=common_tickers, dtype=float)
                    for i in common_tickers:
                        for j in common_tickers:
                            cov_matrix.loc[i, j] = sub_corr.loc[i, j] * sigmas[i] * sigmas[j]
                    
                    def calc_port_stats(weights, cov_mat, individual_sharpes, individual_sigmas, rf):
                        vol = np.sqrt(np.dot(weights.T, np.dot(cov_mat, weights)))
                        r_i = individual_sharpes * individual_sigmas + rf
                        ret = np.dot(weights, r_i)
                        sharpe = (ret - rf) / vol if vol > 0 else 0
                        return sharpe
                    
                    sharpe_current = calc_port_stats(w_current, cov_matrix, sub_df['sharpe'], sigmas, rf)
                    sharpe_opt = calc_port_stats(w_opt, cov_matrix, sub_df['sharpe'], sigmas, rf)
                    
                    fig_sharpe = go.Figure()
                    fig_sharpe.add_trace(go.Bar(
                        name='Sharpe Ratio',
                        x=['Current Portfolio', 'Sharpe Optimized'],
                        y=[sharpe_current, sharpe_opt],
                        text=[f"{sharpe_current:.2f}", f"{sharpe_opt:.2f}"],
                        textposition='auto'
                    ))
                    fig_sharpe.add_hline(y=1, line_dash="dash", line_color="red", annotation_text="Sharpe=1.0")
                    fig_sharpe.update_layout(title="Sharpe Ratio (Before vs After)", yaxis_title="Sharpe Ratio")
                    st.plotly_chart(fig_sharpe, width="stretch")
                    
                    st.caption("* Approximate values based on correlation matrix and each stock's statistics.")
                else:
                    st.info("Correlation data does not match the stocks.")
            else:
                st.info("Correlation matrix data not found. Please run Update Data.")
        except Exception as e:
            st.warning(f"Error creating Sharpe Ratio comparison chart: {e}")
