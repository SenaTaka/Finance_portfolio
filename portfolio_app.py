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

st.set_page_config(page_title="Sena Investment", layout="wide")

# Mobile optimization CSS
st.markdown("""
<style>
/* Mobile responsive CSS */
@media (max-width: 768px) {
    /* Make sidebar buttons larger for easier touch operation */
    .stButton > button {
        min-height: 48px;
        font-size: 16px;
    }
    
    /* Adjust metrics font size */
    [data-testid="stMetricValue"] {
        font-size: 1.5rem !important;
    }
    
    /* Enable horizontal scroll for data frames */
    .stDataFrame {
        overflow-x: auto;
    }
    
    /* Stack columns vertically */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
    }
    
    /* Adjust tab font size */
    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 10px 16px;
    }
    
    /* Increase slider touch area */
    .stSlider > div > div {
        padding: 10px 0;
    }
    
    /* Adjust select box height */
    .stSelectbox > div > div {
        min-height: 44px;
    }
    
    /* Adjust chart margins */
    .js-plotly-plot {
        margin-bottom: 20px;
    }
}

/* Touch device: disable hover state and increase touch area */
@media (hover: none) and (pointer: coarse) {
    .stButton > button {
        min-height: 48px;
        min-width: 48px;
    }
    
    /* Increase sidebar input element size */
    .stSidebar .stNumberInput input,
    .stSidebar .stTextInput input {
        font-size: 16px;
        min-height: 44px;
    }
}

/* Optimize scroll behavior for touch devices: allow horizontal and vertical panning */
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
        st.sidebar.warning("streamlit_autorefresh is not installed. Auto-refresh is disabled.")

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
        data_timestamp_placeholder.caption(f"📅 Data Updated: {' / '.join(timestamps)}")

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
            st.plotly_chart(fig_pie, width="stretch")

    with col2:
        st.subheader("Sector Analysis")
        if 'sector' in df.columns and 'value_jp' in df.columns:
            # Group by sector
            sector_df = df.groupby('sector')['value_jp'].sum().reset_index()
            fig_sector = px.pie(sector_df, values='value_jp', names='sector', title='Portfolio Allocation by Sector', hole=0.4)
            fig_sector.update_traces(textposition='none', hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>')
            apply_mobile_layout(fig_sector)
            st.plotly_chart(fig_sector, width="stretch")
        else:
            st.info("Sector data not available. Please update data.")

    # Advanced Analysis Tabs
    st.subheader("Advanced Analysis")
    tab1, tab2, tab3, tab4 = st.tabs(["Risk vs Return", "Correlation Matrix", "Metrics", "Sharpe Optimized"])
    
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
                
                st.plotly_chart(fig_scatter, width="stretch")
                st.caption("💡 Tap to view stock details")
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
                        st.plotly_chart(fig_corr, width="stretch")
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
                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.write("No Sharpe Ratio data available.")

    with tab4:
        st.header("Sharpe Optimized Portfolio")
        st.write("Displays the proposed allocation and trade plan when optimizing the portfolio based on each stock's Sharpe ratio.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            param_a = st.slider("Sharpe Ratio Emphasis (a)", min_value=0.5, max_value=3.0, value=1.0, step=0.5, key="slider_sharpe_a")
        with col_b:
            param_b = st.slider("Volatility Emphasis (b)", min_value=0.5, max_value=3.0, value=1.0, step=0.5, key="slider_vol_b")
            
        if 'sharpe' in df.columns and 'sigma' in df.columns:
            # Ensure numeric types for calculation
            df['sharpe'] = pd.to_numeric(df['sharpe'], errors='coerce')
            df['sigma'] = pd.to_numeric(df['sigma'], errors='coerce')
            
            # Calculate scores and weights
            scores = calculate_sharpe_scores(df, a=param_a, b=param_b)
            target_weights = calculate_target_weights(scores)
            
            # Calculate trade plan
            usd_jpy_rate = df['usd_jpy_rate'].iloc[0] if 'usd_jpy_rate' in df.columns else 100.0
            trade_plan_df = calculate_trade_plan(df, target_weights, total_value_jp, usd_jpy_rate)
            
            # Display Trade Plan
            st.subheader("Rebalancing Proposal")
            
            # Format for display
            display_plan = trade_plan_df.copy()
            display_plan['Action'] = display_plan['diff_value_jp'].apply(lambda x: 'Buy' if x > 0 else 'Sell')
            display_plan['Trade Amount (JPY)'] = display_plan['diff_value_jp'].abs()
            display_plan['Trade Shares'] = display_plan['diff_shares'].apply(lambda x: int(x) if not pd.isna(x) else 0).abs()
            
            # Filter small trades
            display_plan = display_plan[display_plan['Trade Amount (JPY)'] > 1000] # Filter small amounts
            
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
            
            # Sharpe Ratio Comparison Graph
            st.subheader("Sharpe Ratio (Current vs Optimized)")
            
            # Try to calculate Sharpe Ratios
            try:
                # Load correlation matrix
                corr_df = None
                if selected_file:
                    match = re.search(r'_result_(\d{8}_\d{6})\.csv', selected_file)
                elif view_mode == "Combined (Latest)":
                    # Use the first loaded file timestamp for simplicity or try to find latest corr
                    # This is a bit tricky for combined view. Let's try to find latest corr file.
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
                    # Try both prefixes
                    corr_file_us = os.path.join("output", f"portfolio_corr_{timestamp}.csv")
                    corr_file_jp = os.path.join("output", f"portfolio_jp_corr_{timestamp}.csv")
                    
                    if os.path.exists(corr_file_us):
                        corr_df = pd.read_csv(corr_file_us, index_col=0)
                    elif os.path.exists(corr_file_jp):
                        corr_df = pd.read_csv(corr_file_jp, index_col=0)
                
                if corr_df is not None:
                    # Align tickers
                    common_tickers = [t for t in df['ticker'] if t in corr_df.index]
                    if common_tickers:
                        sub_df = df[df['ticker'].isin(common_tickers)].set_index('ticker')
                        sub_corr = corr_df.loc[common_tickers, common_tickers]
                        
                        # Get weights
                        w_current = sub_df['ratio'] / 100.0
                        w_current = w_current / w_current.sum() # Normalize
                        
                        w_opt = pd.Series({t: target_weights.get(t, 0) for t in common_tickers})
                        w_opt = w_opt / w_opt.sum() # Normalize
                        
                        # Get Sigma (annualized %)
                        sigmas = sub_df['sigma']
                        
                        # Get Expected Return (annualized %)
                        # We can back-calculate from Sharpe if we know Rf, or use mean return if available.
                        # Sharpe = (R - Rf) / Sigma  => R = Sharpe * Sigma + Rf
                        # We need Rf. Let's assume 4.0% or try to get it.
                        # Ideally we should store Rf in the result CSV. I added it to portfolio_calculator.py but old files won't have it.
                        # Let's assume 4.0 if not found.
                        rf = 4.0
                        
                        # Calculate Portfolio Volatility
                        # Vol = sqrt(w.T * Cov * w)
                        # Cov_ij = Corr_ij * Sigma_i * Sigma_j
                        
                        # Construct Covariance Matrix
                        cov_matrix = pd.DataFrame(index=common_tickers, columns=common_tickers, dtype=float)
                        for i in common_tickers:
                            for j in common_tickers:
                                cov_matrix.loc[i, j] = sub_corr.loc[i, j] * sigmas[i] * sigmas[j]
                        
                        def calc_port_stats(weights, cov_mat, individual_sharpes, individual_sigmas, rf):
                            vol = np.sqrt(np.dot(weights.T, np.dot(cov_mat, weights)))
                            # Expected Return of Portfolio = Sum(w_i * R_i)
                            # R_i = Sharpe_i * Sigma_i + Rf
                            r_i = individual_sharpes * individual_sigmas + rf
                            ret = np.dot(weights, r_i)
                            sharpe = (ret - rf) / vol if vol > 0 else 0
                            return sharpe
                        
                        sharpe_current = calc_port_stats(w_current, cov_matrix, sub_df['sharpe'], sigmas, rf)
                        sharpe_opt = calc_port_stats(w_opt, cov_matrix, sub_df['sharpe'], sigmas, rf)
                        
                        # Plot
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
                
        else:
            st.info("Sharpe Ratio data not available.")

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

                    st.markdown("##### パフォーマンス比較 (バックテスト)")

                    period_options = {
                        "3M": 63,
                        "6M": 126,
                        "1Y": 252,
                        "All": None,
                    }
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
                        st.warning("選択した期間では十分な価格データがありません。より長い期間を選択してください。")
                    else:
                        def _weights_to_array(weight_dict: dict) -> np.ndarray:
                            return np.array([weight_dict.get(t, 0) for t in tickers], dtype=float)

                        portfolio_candidates = {}

                        # Current portfolio
                        if current_weights is not None and 'current' in suggestions:
                            portfolio_candidates['現在のポートフォリオ'] = current_weights

                        # Suggested portfolios
                        for key in ['max_sharpe', 'min_volatility']:
                            if key in suggestions:
                                portfolio_candidates[suggestions[key]['name_jp']] = _weights_to_array(suggestions[key]['weights'])

                        # Equal weight benchmark
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
                        else:
                            st.info("バックテスト結果を表示できませんでした。入力データやウェイトを確認してください。")
                    
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
                        # Note: hovertemplate uses f-string to embed values at definition time,
                        # which is correct here since we want to display the calculated values
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
                        
                        # Display suggestions as cards
                        for key, sug in suggestions.items():
                            with st.expander(f"📊 {sug['name']}", expanded=(key == 'max_sharpe')):
                                st.markdown(f"**{sug['description']}**")
                                st.markdown(f"- Expected Return: **{sug['expected_return']:.1f}%**")
                                st.markdown(f"- Volatility: **{sug['volatility']:.1f}%**")
                                st.markdown(f"- Sharpe Ratio: **{sug['sharpe']:.2f}**")
                                
                                # Show weights
                                st.markdown("**Allocation Weights:**")
                                weights_df = pd.DataFrame([
                                    {'Ticker': t, 'Weight': f"{w*100:.1f}%"}
                                    for t, w in sug['weights'].items()
                                    if w > 0.01  # Only show weights > 1%
                                ])
                                if not weights_df.empty:
                                    weights_df = weights_df.sort_values('Weight', ascending=False)
                                    st.dataframe(weights_df, hide_index=True, width="stretch")
                    
                    # Add rebalancing recommendation
                    st.markdown("---")
                    st.markdown("#### 🎯 Rebalancing Recommendation")
                    
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
                    else:
                        st.info("Current portfolio allocation data not available.")
                else:
                    st.info("More price history data is required to calculate the efficient frontier.")
            except Exception as e:
                st.warning(f"Error calculating efficient frontier: {e}")
        else:
            st.info("At least 2 stocks with price data are required to calculate the efficient frontier. Please run 'Update Data' to fetch data.")
    else:
        st.warning("The scipy library is required to use the efficient frontier feature.")

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
                width="stretch",
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
                st.plotly_chart(fig_sector, width="stretch")

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
                st.plotly_chart(fig_region, width="stretch")
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

    st.divider()
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
    if 'ticker' in df.columns and 'shares' in df.columns:
        try:
            # Get S&P 500 data
            sp500 = yf.Ticker("^SPX")
            sp500_hist = sp500.history(start=start_date, end=end_date)
            
            if sp500_hist.empty:
                # Fallback to ^GSPC if ^SPX fails
                sp500 = yf.Ticker("^GSPC")
                sp500_hist = sp500.history(start=start_date, end=end_date)
            
            # Get Risk Free Rate (10 Year Treasury)
            tnx = yf.Ticker("^TNX")
            tnx_hist = tnx.history(period="1d")
            if not tnx_hist.empty:
                rf_rate = tnx_hist['Close'].iloc[-1] / 100.0
            else:
                rf_rate = 0.04 # Default 4%
            
            if not sp500_hist.empty:
                # Ensure timezone naive for comparison to avoid mismatch
                if sp500_hist.index.tz is not None:
                    sp500_hist.index = sp500_hist.index.tz_localize(None)

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
                        group_by='ticker',
                        auto_adjust=True
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
                                        if close_data.index.tz is not None:
                                            close_data.index = close_data.index.tz_localize(None)
                                        portfolio_hist[ticker] = close_data
                            else:
                                # Multiple tickers case
                                if ticker in portfolio_data.columns.get_level_values(0):
                                    close_data = portfolio_data[ticker]['Close']
                                    if not close_data.empty and close_data.notna().sum() > 0:
                                        if close_data.index.tz is not None:
                                            close_data.index = close_data.index.tz_localize(None)
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
                                portfolio_return_series = (portfolio_value / portfolio_value.iloc[0] - 1) * 100
                                
                                # Align S&P 500 data with portfolio data
                                sp500_aligned = sp500_hist['Close'].reindex(price_df.index).ffill().bfill()
                                sp500_return_series = (sp500_aligned / sp500_aligned.iloc[0] - 1) * 100
                                
                                # Calculate Sharpe Ratios
                                # Daily returns
                                port_daily_ret = portfolio_value.pct_change().dropna()
                                sp500_daily_ret = sp500_aligned.pct_change().dropna()
                                
                                # Annualized metrics
                                port_ann_ret = port_daily_ret.mean() * 252
                                port_ann_vol = port_daily_ret.std() * np.sqrt(252)
                                port_sharpe = (port_ann_ret - rf_rate) / port_ann_vol if port_ann_vol > 0 else 0
                                
                                sp500_ann_ret = sp500_daily_ret.mean() * 252
                                sp500_ann_vol = sp500_daily_ret.std() * np.sqrt(252)
                                sp500_sharpe = (sp500_ann_ret - rf_rate) / sp500_ann_vol if sp500_ann_vol > 0 else 0
                                
                                # Create comparison DataFrame
                                comparison_df = pd.DataFrame({
                                    'Date': price_df.index,
                                    'Portfolio': portfolio_return_series.values,
                                    'S&P 500': sp500_return_series.values
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
                                    st.metric(
                                        "Portfolio Return",
                                        f"{portfolio_total_return:+.2f}%",
                                        delta=None
                                    )
                                    st.metric("Portfolio Sharpe", f"{port_sharpe:.2f}")
                                with col2:
                                    st.metric(
                                        "S&P 500 Return",
                                        f"{sp500_total_return:+.2f}%",
                                        delta=None
                                    )
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

    st.dataframe(df, width="stretch", column_config=column_config, hide_index=True)
