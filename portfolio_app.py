import streamlit as st
import pandas as pd
import glob
import os
import re
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import yfinance as yf

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None
try:
    from portfolio_calculator import PortfolioCalculator
except ImportError:
    pass
try:
    from efficient_frontier import (
        calculate_efficient_frontier,
        generate_random_portfolios,
        get_portfolio_suggestions,
        prepare_data_for_frontier,
        find_optimal_portfolio,
        find_min_volatility_portfolio,
    )
    EFFICIENT_FRONTIER_AVAILABLE = True
except ImportError:
    EFFICIENT_FRONTIER_AVAILABLE = False

st.set_page_config(page_title="Sena Investment", layout="wide")

# Mobile optimization CSS
st.markdown("""
<style>
/* モバイル向けレスポンシブCSS */
@media (max-width: 768px) {
    /* サイドバーのボタンを大きくしてタッチ操作しやすく */
    .stButton > button {
        min-height: 48px;
        font-size: 16px;
    }
    
    /* メトリクスのフォントサイズ調整 */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* データフレームのスクロール対応 */
    .stDataFrame {
        overflow-x: auto;
    }
    
    /* カラムの縦並び対応 */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    
    /* タブのフォントサイズ調整 */
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 10px 16px;
    }
    
    /* スライダーの操作領域を大きく */
    .stSlider > div > div {
        padding: 10px 0;
    }
    
    /* セレクトボックスの高さ調整 */
    .stSelectbox > div > div {
        min-height: 44px;
    }
    
    /* チャートの余白調整 */
    .js-plotly-plot {
        margin-bottom: 20px;
    }
}

/* タッチデバイス向け: ホバー状態の無効化とタッチ領域拡大 */
@media (hover: none) and (pointer: coarse) {
    .stButton > button {
        min-height: 48px;
        min-width: 48px;
    }
    
    /* サイドバーの入力要素を大きく */
    .stSidebar .stNumberInput input,
    .stSidebar .stTextInput input {
        font-size: 16px;
        min-height: 44px;
    }
}

/* タッチデバイス向けのスクロール動作を最適化: 水平・垂直方向のパン操作を許可 */
[data-testid="stAppViewContainer"] {
    touch-action: pan-x pan-y;
}
</style>
""", unsafe_allow_html=True)

st.title("Sena Investment")

# Placeholder for data update timestamp (will be populated after loading files)
data_timestamp_placeholder = st.empty()

# Mobile-friendly chart layout constants
MOBILE_TICK_ANGLE = -45


def extract_timestamp_from_filename(filename: str) -> str | None:
    """Extract and format the timestamp from a result file name.
    
    Args:
        filename: The filename containing a timestamp in format YYYYMMDD_HHMMSS
        
    Returns:
        Formatted timestamp string or None if not found
    """
    match = re.search(r'_result_(\d{8})_(\d{6})\.csv', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except ValueError:
            return None
    return None


def apply_mobile_layout(fig, show_legend=True):
    """Apply mobile-friendly layout settings to a Plotly figure."""
    layout_config = dict(margin=dict(l=10, r=10, t=40, b=100))
    if show_legend:
        layout_config["legend"] = dict(
            orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
            font=dict(size=11),
            itemsizing="constant"
        )
    fig.update_layout(**layout_config)
    return fig


def get_region(country: str) -> str:
    if not isinstance(country, str):
        return "Unknown"

    north_america = {"United States", "Canada"}
    europe = {
        "United Kingdom",
        "Germany",
        "France",
        "Switzerland",
        "Netherlands",
        "Sweden",
        "Spain",
        "Italy",
        "Ireland",
    }
    asia = {"Japan", "China", "Hong Kong", "India", "South Korea", "Taiwan", "Singapore"}

    if country in north_america:
        return "North America"
    if country in europe:
        return "Europe"
    if country in asia:
        return "Asia"
    return "Other"

# Sidebar for file selection
st.sidebar.header("Settings")

auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=False)
refresh_minutes = st.sidebar.slider("Refresh interval (minutes)", 1, 60, 5)

if auto_refresh:
    if st_autorefresh:
        st_autorefresh(interval=refresh_minutes * 60 * 1000, key="portfolio_autorefresh")
    else:
        st.sidebar.warning("streamlit_autorefresh が未インストールのため、自動再読み込みは無効です。")

alert_threshold = st.sidebar.number_input("Alert threshold for total value change (%)", min_value=1, max_value=50, value=5)

# Force refresh option
force_refresh = st.sidebar.checkbox("Force full refresh (ignore cache)", value=False, 
    help="When checked, fetches all data from API ignoring cached values")

# Update Data Button
if st.sidebar.button("🔄 Update Data"):
    with st.spinner("Fetching latest data..."):
        target_files = ["portfolio.csv", "portfolio_jp.csv"]
        updated_count = 0
        
        for input_csv in target_files:
            if os.path.exists(input_csv):
                try:
                    # Redirect stdout to capture print output if needed, or just let it print to console
                    calculator = PortfolioCalculator(input_csv, force_refresh=force_refresh)
                    calculator.run()
                    updated_count += 1
                except Exception as e:
                    st.sidebar.error(f"Error updating {input_csv}: {e}")
            else:
                # Only warn if it's the main file, or maybe just ignore missing optional files
                if input_csv == "portfolio.csv":
                    st.sidebar.warning(f"{input_csv} not found.")

        if updated_count > 0:
            st.sidebar.success(f"Updated {updated_count} files successfully!")
            st.rerun()

# View Mode Selection
view_mode = st.sidebar.radio("View Mode", ["Combined (Latest)", "US History", "JP History"])

df = None
selected_file = None
loaded_file_names = []  # Track loaded files for timestamp display

if view_mode == "Combined (Latest)":
    # Find latest US and JP results
    us_files = glob.glob(os.path.join("output", "portfolio_result_*.csv"))
    jp_files = glob.glob(os.path.join("output", "portfolio_jp_result_*.csv"))
    
    dfs = []
    loaded_files = []
    
    if us_files:
        us_files.sort(key=os.path.getmtime, reverse=True)
        dfs.append(pd.read_csv(us_files[0]))
        loaded_files.append(os.path.basename(us_files[0]))
        
    if jp_files:
        jp_files.sort(key=os.path.getmtime, reverse=True)
        dfs.append(pd.read_csv(jp_files[0]))
        loaded_files.append(os.path.basename(jp_files[0]))
        
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        # Recalculate ratio for the combined portfolio based on JPY value
        total_val_jp = df['value_jp'].sum()
        if total_val_jp > 0:
            df['ratio'] = (df['value_jp'] / total_val_jp * 100).round(2)
        
        st.sidebar.info(f"Loaded: {', '.join(loaded_files)}")
        loaded_file_names = loaded_files
    else:
        st.info("No result files found to combine.")

else:
    # Individual File Selection
    if view_mode == "US History":
        file_pattern = "portfolio_result_*.csv"
    else:
        file_pattern = "portfolio_jp_result_*.csv"
        
    files = glob.glob(os.path.join("output", file_pattern))
    files.sort(key=os.path.getmtime, reverse=True)
    
    uploaded_file = st.sidebar.file_uploader("Upload a result CSV", type="csv", key=view_mode)
    selected_file = st.sidebar.selectbox(f"Select a {view_mode} file", [""] + files, key=f"select_{view_mode}")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        loaded_file_names = [uploaded_file.name]
    elif selected_file:
        df = pd.read_csv(selected_file)
        loaded_file_names = [os.path.basename(selected_file)]
    elif files:
        # Default to the latest file if nothing selected
        st.sidebar.info(f"Auto-loading latest file: {os.path.basename(files[0])}")
        df = pd.read_csv(files[0])
        loaded_file_names = [os.path.basename(files[0])]
    else:
        st.info(f"No {view_mode} files found. Please upload or run update.")

# Display data update timestamp near the title
if loaded_file_names:
    timestamps = []
    for fname in loaded_file_names:
        ts = extract_timestamp_from_filename(fname)
        if ts:
            # Add source indicator for combined view
            if "portfolio_jp" in fname:
                timestamps.append(f"JP: {ts}")
            elif "portfolio_result" in fname:
                timestamps.append(f"US: {ts}")
            else:
                timestamps.append(ts)
    if timestamps:
        data_timestamp_placeholder.caption(f"📅 データ更新日時: {' / '.join(timestamps)}")

if df is not None:
    # Basic stats
    if 'value' in df.columns:
        total_value = df['value'].sum()
        st.metric("Total Portfolio Value (USD)", f"${total_value:,.2f}")

    total_value_jp = None
    if 'value_jp' in df.columns:
        total_value_jp = df['value_jp'].sum()
        st.metric("Total Portfolio Value (JPY)", f"¥{total_value_jp:,.0f}")

    if 'usd_jpy_rate' in df.columns:
        rate = df['usd_jpy_rate'].iloc[0]
        st.caption(f"Exchange Rate: 1 USD = {rate:.2f} JPY")

    if total_value_jp is not None:
        prev_total = st.session_state.get("prev_total_value_jp")
        if prev_total:
            change_pct = (total_value_jp - prev_total) / prev_total * 100
            if abs(change_pct) >= alert_threshold:
                st.sidebar.error(f"Portfolio moved {change_pct:.2f}% since last load")
        st.session_state["prev_total_value_jp"] = total_value_jp
        st.session_state["last_update_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        if 'value_jp' in df.columns and 'ticker' in df.columns:
            st.subheader("Portfolio Allocation (JPY)")

            # Prepare labels: "Name (Ticker)"
            plot_df = df.copy()
            if 'name' in plot_df.columns:
                plot_df['label'] = plot_df.apply(lambda x: f"{x['name']} ({x['ticker']})" if pd.notnull(x['name']) else x['ticker'], axis=1)
                names_col = 'label'
            else:
                names_col = 'ticker'

            fig_pie = px.pie(plot_df, values='value_jp', names=names_col, title='Portfolio Allocation by Value (JPY)', hole=0.4)
            fig_pie.update_traces(textposition='none', hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>')
            apply_mobile_layout(fig_pie)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Sector Analysis")
        if 'sector' in df.columns and 'value_jp' in df.columns:
            # Group by sector
            sector_df = df.groupby('sector')['value_jp'].sum().reset_index()
            fig_sector = px.pie(sector_df, values='value_jp', names='sector', title='Portfolio Allocation by Sector', hole=0.4)
            fig_sector.update_traces(textposition='none', hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>')
            apply_mobile_layout(fig_sector)
            st.plotly_chart(fig_sector, use_container_width=True)
        else:
            st.info("Sector data not available. Please update data.")

    # Advanced Analysis Tabs
    st.subheader("Advanced Analysis")
    tab1, tab2, tab3 = st.tabs(["Risk vs Return", "Correlation Matrix", "Metrics"])
    
    with tab1:
        if 'sigma' in df.columns and 'sharpe' in df.columns:
            # Risk (Sigma) vs Return (derived from Sharpe * Sigma + RiskFree)
            # Or just Risk vs Sharpe
            # Let's do Risk (Volatility) vs Sharpe Ratio for now as it's available
            scatter_df = df.dropna(subset=['sigma', 'sharpe']).copy()
            if not scatter_df.empty:
                # Create label column for display (Name if available, otherwise Ticker)
                if 'name' in scatter_df.columns:
                    scatter_df['display_name'] = scatter_df['name'].fillna(scatter_df['ticker'])
                else:
                    scatter_df['display_name'] = scatter_df['ticker']
                
                # Ensure value_jp exists for hover
                if 'value_jp' not in scatter_df.columns:
                    scatter_df['value_jp'] = 0
                
                fig_scatter = px.scatter(
                    scatter_df, 
                    x='sigma', 
                    y='sharpe', 
                    size='value_jp', 
                    color='display_name',
                    hover_data={
                        'display_name': True,
                        'ticker': True,
                        'sigma': ':.1f',
                        'sharpe': ':.2f',
                        'value_jp': ':,.0f'
                    },
                    title='Risk (Volatility) vs Efficiency (Sharpe Ratio)',
                    labels={
                        'sigma': 'Volatility (Risk) [%]', 
                        'sharpe': 'Sharpe Ratio',
                        'display_name': 'Name',
                        'value_jp': 'Value (JPY)'
                    }
                )
                
                # Apply mobile-optimized layout: hide legend and increase chart area
                fig_scatter.update_layout(
                    margin=dict(l=10, r=10, t=40, b=40),
                    showlegend=False,
                    xaxis=dict(title=dict(font=dict(size=12))),
                    yaxis=dict(title=dict(font=dict(size=12))),
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                st.caption("💡 タップして銘柄の詳細を表示")
            else:
                st.write("Insufficient data for Risk analysis.")
    
    with tab2:
        # Identify files to show correlation for
        files_to_show = []
        if selected_file:
            files_to_show.append(selected_file)
        elif view_mode == "Combined (Latest)":
            # Find latest files again
            us = glob.glob(os.path.join("output", "portfolio_result_*.csv"))
            jp = glob.glob(os.path.join("output", "portfolio_jp_result_*.csv"))
            if us: files_to_show.append(sorted(us, key=os.path.getmtime, reverse=True)[0])
            if jp: files_to_show.append(sorted(jp, key=os.path.getmtime, reverse=True)[0])
            
        if files_to_show:
            import re
            for f_path in files_to_show:
                match = re.search(r'_result_(\d{8}_\d{6})\.csv', f_path)
                if match:
                    timestamp = match.group(1)
                    # Determine prefix
                    if "portfolio_jp" in f_path:
                        prefix = "portfolio_jp"
                        title_suffix = "(Japan)"
                    else:
                        prefix = "portfolio"
                        title_suffix = "(US)"
                    
                    corr_file = os.path.join("output", f"{prefix}_corr_{timestamp}.csv")
                    
                    if os.path.exists(corr_file):
                        corr_df = pd.read_csv(corr_file, index_col=0)
                        fig_corr = px.imshow(corr_df, text_auto=True, title=f"Correlation Matrix {title_suffix}")
                        apply_mobile_layout(fig_corr, show_legend=False)
                        st.plotly_chart(fig_corr, use_container_width=True)
                    else:
                        st.info(f"Correlation data not found for {os.path.basename(f_path)}")
        else:
            st.info("Select a specific file to view correlation matrix.")

    with tab3:
        st.subheader("Metrics Analysis")
        if 'sharpe' in df.columns and 'ticker' in df.columns:
            # Drop NAs for plotting
            plot_df = df.dropna(subset=['sharpe'])
            if not plot_df.empty:
                fig_bar = px.bar(plot_df, x='ticker', y='sharpe', title='Sharpe Ratio by Ticker', color='ticker')
                apply_mobile_layout(fig_bar)
                fig_bar.update_layout(xaxis_tickangle=MOBILE_TICK_ANGLE)
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("No Sharpe Ratio data available.")

    st.divider()
    st.subheader("📈 Efficient Frontier (Modern Portfolio Theory)")
    
    if EFFICIENT_FRONTIER_AVAILABLE:
        # Build price history from cache for efficient frontier calculation
        from portfolio_calculator import load_cache
        cache = load_cache()
        
        # Collect historical data for tickers in current portfolio
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
                    if len(hist_series) > 20:  # Require at least 20 data points
                        price_data[ticker] = hist_series
                        valid_tickers.append(ticker)
                except (ValueError, TypeError):
                    pass
        
        if len(valid_tickers) >= 2:
            try:
                # Create aligned price DataFrame
                price_df = pd.DataFrame(price_data)
                price_df = price_df.ffill().bfill().dropna()
                
                if len(price_df) > 20:
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
                    
                    # Create efficient frontier visualization
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        fig_ef = go.Figure()
                        
                        # Add random portfolios as scatter
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
                        
                        # Add Max Sharpe portfolio
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
                        
                        # Add Min Volatility portfolio
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
                        
                        # Add current portfolio if available
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
                            title='Efficient Frontier (効率的フロンティア)',
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
                        
                        st.plotly_chart(fig_ef, use_container_width=True)
                    
                    with col2:
                        st.markdown("#### Portfolio Suggestions")
                        st.markdown("##### ポートフォリオ提案")
                        
                        # Display suggestions as cards
                        for key, sug in suggestions.items():
                            with st.expander(f"📊 {sug['name_jp']}", expanded=(key == 'max_sharpe')):
                                st.markdown(f"**{sug['description_jp']}**")
                                st.markdown(f"- 期待リターン: **{sug['expected_return']:.1f}%**")
                                st.markdown(f"- ボラティリティ: **{sug['volatility']:.1f}%**")
                                st.markdown(f"- シャープレシオ: **{sug['sharpe']:.2f}**")
                                
                                # Show weights
                                st.markdown("**配分比率:**")
                                weights_df = pd.DataFrame([
                                    {'Ticker': t, 'Weight': f"{w*100:.1f}%"}
                                    for t, w in sug['weights'].items()
                                    if w > 0.01  # Only show weights > 1%
                                ])
                                if not weights_df.empty:
                                    weights_df = weights_df.sort_values('Weight', ascending=False)
                                    st.dataframe(weights_df, hide_index=True, use_container_width=True)
                    
                    # Add rebalancing recommendation
                    st.markdown("---")
                    st.markdown("#### 🎯 Rebalancing Recommendation (リバランス推奨)")
                    
                    if 'current' in suggestions:
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
                        
                        # Calculate and display required trades
                        if total_value_jp:
                            st.markdown("##### Required Trades to Reach Max Sharpe Portfolio")
                            trade_data = []
                            for ticker in tickers:
                                current_weight = current['weights'].get(ticker, 0)
                                target_weight = max_sharpe['weights'].get(ticker, 0)
                                weight_diff = target_weight - current_weight
                                trade_amount = weight_diff * total_value_jp
                                
                                if abs(trade_amount) > 10000:  # Only show significant trades
                                    trade_data.append({
                                        'Ticker': ticker,
                                        'Current %': f"{current_weight*100:.1f}%",
                                        'Target %': f"{target_weight*100:.1f}%",
                                        'Trade (JPY)': int(trade_amount),
                                        'Action': '買い' if trade_amount > 0 else '売り'
                                    })
                            
                            if trade_data:
                                trade_df = pd.DataFrame(trade_data)
                                st.dataframe(
                                    trade_df,
                                    use_container_width=True,
                                    hide_index=True,
                                    column_config={
                                        'Trade (JPY)': st.column_config.NumberColumn(format="¥%d")
                                    }
                                )
                            else:
                                st.info("現在のポートフォリオは最適配分に近いです。")
                    else:
                        st.info("現在のポートフォリオの配分データがありません。")
                else:
                    st.info("効率的フロンティアの計算には、より多くの価格履歴データが必要です。")
            except Exception as e:
                st.warning(f"効率的フロンティアの計算中にエラーが発生しました: {e}")
        else:
            st.info("効率的フロンティアの計算には、少なくとも2銘柄の価格データが必要です。「Update Data」を実行してデータを取得してください。")
    else:
        st.warning("効率的フロンティア機能を使用するには、scipy ライブラリが必要です。")

    st.divider()
    st.subheader("Rebalance Suggestions")

    profile = st.selectbox("Risk profile", ["Conservative", "Balanced", "Aggressive"], index=1)
    min_ticket_threshold = st.slider("Ignore differences smaller than (JPY)", 0, 500000, 50000, step=10000)

    risk_power = {"Conservative": 1.5, "Balanced": 1.0, "Aggressive": 0.5}[profile]

    if 'sigma' in df.columns and df['sigma'].notna().any():
        vol = df['sigma'].fillna(df['sigma'].median())
        inv_risk = (1 / vol) ** risk_power
        target_weights = inv_risk / inv_risk.sum()
    else:
        target_weights = pd.Series(1, index=df.index)
        target_weights = target_weights / target_weights.sum()

    df['target_ratio'] = (target_weights * 100).round(2)

    if total_value_jp:
        df['target_value_jp'] = (target_weights * total_value_jp).round(0)
        df['delta_value_jp'] = df['target_value_jp'] - df['value_jp']
        suggestion_df = df[['ticker', 'name', 'ratio', 'target_ratio', 'value_jp', 'target_value_jp', 'delta_value_jp']]
        suggestion_df = suggestion_df[abs(suggestion_df['delta_value_jp']) >= min_ticket_threshold]

        if suggestion_df.empty:
            st.info("Portfolio is within threshold of target weights.")
        else:
            st.dataframe(
                suggestion_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "ratio": st.column_config.NumberColumn("Current %", format="%.2f%%"),
                    "target_ratio": st.column_config.NumberColumn("Target %", format="%.2f%%"),
                    "value_jp": st.column_config.NumberColumn("Current (JPY)", format="¥%.0f"),
                    "target_value_jp": st.column_config.NumberColumn("Target (JPY)", format="¥%.0f"),
                    "delta_value_jp": st.column_config.NumberColumn("Buy (+) / Sell (-)", format="¥%.0f"),
                },
            )
    else:
        st.info("JPY valuation is required to generate rebalance suggestions.")

    st.divider()
    st.subheader("Scenario analysis & stress test")

    shock_price = st.slider("Equity price shock (%)", -50, 50, -10)
    shock_fx = st.slider("USD/JPY shock (%)", -20, 20, 0)
    vol_multiplier = st.slider("Volatility multiplier", 0.5, 2.0, 1.2, step=0.1)

    scenario_df = df.copy()
    if 'value_jp' in scenario_df.columns:
        # 1. Apply Equity Price Shock to ALL assets
        scenario_df['value_jp_scenario'] = scenario_df['value_jp'] * (1 + shock_price / 100)
        
        # 2. Apply FX Shock to Foreign Assets (non-JPY)
        if 'currency' in scenario_df.columns:
            # If currency is NOT 'JPY', the value in JPY is affected by the exchange rate change.
            is_foreign = scenario_df['currency'] != 'JPY'
            scenario_df.loc[is_foreign, 'value_jp_scenario'] *= (1 + shock_fx / 100)

    if 'usd_jpy_rate' in scenario_df.columns:
        scenario_df['usd_jpy_rate'] = scenario_df['usd_jpy_rate'] * (1 + shock_fx / 100)
    if 'sigma' in scenario_df.columns:
        scenario_df['sigma_scenario'] = scenario_df['sigma'] * vol_multiplier

    scenario_total = scenario_df.get('value_jp_scenario', pd.Series()).sum()
    if total_value_jp:
        change_vs_now = scenario_total - total_value_jp
        st.metric("Scenario Portfolio Value (JPY)", f"¥{scenario_total:,.0f}", delta=f"{change_vs_now:,.0f}")
    if 'sigma_scenario' in scenario_df:
        st.caption("Volatility after shock (annualized, %)")
        st.dataframe(scenario_df[['ticker', 'sigma', 'sigma_scenario']].dropna(), hide_index=True)

    st.divider()
    st.subheader("Risk factor breakdown")

    if 'country' in df.columns:
        df['region'] = df['country'].apply(get_region)

    factor_cols = []
    if 'sector' in df.columns:
        factor_cols.append('sector')
    if 'region' in df.columns:
        factor_cols.append('region')

    if total_value_jp and factor_cols:
        factor_tab1, factor_tab2 = st.tabs(["Sector", "Region"])

        if 'sector' in factor_cols:
            sector_data = (
                df.groupby('sector')['value_jp']
                .sum()
                .reset_index()
                .assign(ratio=lambda x: (x['value_jp'] / total_value_jp * 100))
            )
            with factor_tab1:
                st.write("Sector exposure")
                st.dataframe(sector_data, hide_index=True)
                fig_sector = px.bar(sector_data, x='sector', y='ratio', title='Sector Weight (%)', color='sector')
                apply_mobile_layout(fig_sector)
                fig_sector.update_layout(xaxis_tickangle=MOBILE_TICK_ANGLE)
                st.plotly_chart(fig_sector, use_container_width=True)

        if 'region' in factor_cols:
            region_data = (
                df.groupby('region')['value_jp']
                .sum()
                .reset_index()
                .assign(ratio=lambda x: (x['value_jp'] / total_value_jp * 100))
            )
            with factor_tab2:
                st.write("Regional exposure")
                st.dataframe(region_data, hide_index=True)
                fig_region = px.pie(region_data, values='value_jp', names='region', title='Region Allocation', hole=0.3)
                fig_region.update_traces(textposition='none', hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>')
                apply_mobile_layout(fig_region)
                st.plotly_chart(fig_region, use_container_width=True)
    else:
        st.info("Run update to capture sector and country metadata for factor views.")

    st.divider()
    st.subheader("📈 Portfolio Value History")
    
    # Collect historical total values from result files
    us_history_files = sorted(glob.glob(os.path.join("output", "portfolio_result_*.csv")), key=os.path.getmtime)
    jp_history_files = sorted(glob.glob(os.path.join("output", "portfolio_jp_result_*.csv")), key=os.path.getmtime)
    
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
            st.plotly_chart(fig_history, use_container_width=True)
            
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

    st.divider()
    st.subheader("📊 Performance vs S&P 500 (1 Year)")
    
    # Calculate portfolio performance vs S&P 500 over the past year
    if 'ticker' in df.columns and 'shares' in df.columns:
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            # Get S&P 500 data
            sp500 = yf.Ticker("^GSPC")
            sp500_hist = sp500.history(start=start_date, end=end_date)
            
            if not sp500_hist.empty:
                # Get historical data for portfolio tickers using batch download
                # Filter to USD-only stocks for fair comparison with S&P 500 (a US market index)
                if 'currency' in df.columns:
                    usd_df = df[df['currency'] == 'USD']
                else:
                    usd_df = df
                
                tickers_in_portfolio = usd_df['ticker'].tolist()
                shares_dict = dict(zip(usd_df['ticker'], usd_df['shares']))
                
                # Filter tickers with positive shares
                active_tickers = [t for t in tickers_in_portfolio if shares_dict.get(t, 0) > 0]
                
                if active_tickers:
                    # Use batch download for efficiency
                    portfolio_data = yf.download(
                        active_tickers,
                        start=start_date,
                        end=end_date,
                        progress=False,
                        group_by='ticker'
                    )
                    
                    # Extract close prices for each ticker
                    portfolio_hist = {}
                    for ticker in active_tickers:
                        try:
                            if len(active_tickers) == 1:
                                # Single ticker case: data structure is different
                                if 'Close' in portfolio_data.columns:
                                    close_data = portfolio_data['Close']
                                    if not close_data.empty:
                                        portfolio_hist[ticker] = close_data
                            else:
                                # Multiple tickers case
                                if ticker in portfolio_data.columns.get_level_values(0):
                                    close_data = portfolio_data[ticker]['Close']
                                    if not close_data.empty and close_data.notna().sum() > 0:
                                        portfolio_hist[ticker] = close_data
                        except (KeyError, TypeError):
                            continue
                    
                    if portfolio_hist:
                        # Create a DataFrame with all ticker prices
                        price_df = pd.DataFrame(portfolio_hist)
                        
                        # Validate data coverage: require at least 50% of trading days
                        min_data_points = len(sp500_hist) * 0.5
                        valid_columns = [col for col in price_df.columns 
                                       if price_df[col].notna().sum() >= min_data_points]
                        
                        if valid_columns:
                            price_df = price_df[valid_columns]
                            # Forward fill missing values and drop any remaining NaN rows
                            price_df = price_df.ffill().bfill().dropna()
                            
                            if not price_df.empty:
                                # Calculate portfolio value over time
                                portfolio_value = pd.Series(0.0, index=price_df.index)
                                for ticker in price_df.columns:
                                    portfolio_value += price_df[ticker] * shares_dict.get(ticker, 0)
                                
                                # Normalize both to percentage returns from the start
                                portfolio_return = (portfolio_value / portfolio_value.iloc[0] - 1) * 100
                                
                                # Align S&P 500 data with portfolio data
                                sp500_aligned = sp500_hist['Close'].reindex(price_df.index).ffill().bfill()
                                sp500_return = (sp500_aligned / sp500_aligned.iloc[0] - 1) * 100
                                
                                # Create comparison DataFrame
                                comparison_df = pd.DataFrame({
                                    'Date': price_df.index,
                                    'Portfolio': portfolio_return.values,
                                    'S&P 500': sp500_return.values
                                })
                                
                                # Create the comparison chart
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
                                
                                # Add a zero line for reference
                                fig_comparison.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
                                
                                fig_comparison.update_layout(
                                    title='Portfolio vs S&P 500 Performance (1 Year)',
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
                                
                                st.plotly_chart(fig_comparison, use_container_width=True)
                                
                                # Show performance summary
                                portfolio_total_return = portfolio_return.iloc[-1]
                                sp500_total_return = sp500_return.iloc[-1]
                                outperformance = portfolio_total_return - sp500_total_return
                                
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric(
                                        "Portfolio Return",
                                        f"{portfolio_total_return:+.2f}%",
                                        delta=None
                                    )
                                with col2:
                                    st.metric(
                                        "S&P 500 Return",
                                        f"{sp500_total_return:+.2f}%",
                                        delta=None
                                    )
                                with col3:
                                    delta_color = "normal" if outperformance >= 0 else "inverse"
                                    st.metric(
                                        "Outperformance",
                                        f"{outperformance:+.2f}%",
                                        delta=f"{'Beat' if outperformance >= 0 else 'Underperformed'} S&P 500",
                                        delta_color=delta_color
                                    )
                            else:
                                st.info("Insufficient price data to calculate performance comparison.")
                        else:
                            st.info("Insufficient data coverage for portfolio tickers.")
                    else:
                        st.info("Unable to fetch historical data for portfolio tickers.")
                else:
                    st.info("No active USD holdings found in portfolio. S&P 500 comparison requires USD-denominated stocks.")
            else:
                st.info("Unable to fetch S&P 500 data.")
        except Exception as e:
            st.warning(f"Could not calculate performance comparison: {e}")
    else:
        st.info("Portfolio data not available for performance comparison.")

    st.divider()
    st.subheader("Detailed Data")

    # Display dataframe with formatting
    # We use st.dataframe with column configuration for better display
    column_config = {
        "ticker": "Ticker",
        "name": "Company Name",
        "shares": st.column_config.NumberColumn("Shares", format="%d"),
        "currency": "Currency",
        "price": st.column_config.NumberColumn("Price", format="%.2f"),
        "PER": st.column_config.NumberColumn("PER", format="%.2f"),
        "sigma": st.column_config.NumberColumn("Volatility (σ)", format="%.2f%%"),
        "sharpe": st.column_config.NumberColumn("Sharpe Ratio", format="%.2f"),
        "dividend_yield": st.column_config.NumberColumn("Dividend Yield", format="%.2f"),
        "value": st.column_config.NumberColumn("Value (USD)", format="$%.2f"),
        "value_jp": st.column_config.NumberColumn("Value (JPY)", format="¥%.0f"),
        "ratio": st.column_config.NumberColumn("Ratio", format="%.2f%%"),
        "usd_jpy_rate": st.column_config.NumberColumn("USD/JPY", format="%.2f"),
        "sector": "Sector",
        "industry": "Industry",
        "country": "Country",
        "target_ratio": st.column_config.NumberColumn("Target %", format="%.2f%%"),
        "target_value_jp": st.column_config.NumberColumn("Target (JPY)", format="¥%.0f"),
        "delta_value_jp": st.column_config.NumberColumn("Rebalance (JPY)", format="¥%.0f"),
    }

    st.dataframe(df, use_container_width=True, column_config=column_config, hide_index=True)
