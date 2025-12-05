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

# Mobile-friendly chart layout constants
MOBILE_TICK_ANGLE = -45


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

# Update Data Button
if st.sidebar.button("🔄 Update Data"):
    with st.spinner("Fetching latest data..."):
        target_files = ["portfolio.csv", "portfolio_jp.csv"]
        updated_count = 0
        
        for input_csv in target_files:
            if os.path.exists(input_csv):
                try:
                    # Redirect stdout to capture print output if needed, or just let it print to console
                    calculator = PortfolioCalculator(input_csv)
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
    elif selected_file:
        df = pd.read_csv(selected_file)
    elif files:
        # Default to the latest file if nothing selected
        st.sidebar.info(f"Auto-loading latest file: {os.path.basename(files[0])}")
        df = pd.read_csv(files[0])
    else:
        st.info(f"No {view_mode} files found. Please upload or run update.")

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
            scatter_df = df.dropna(subset=['sigma', 'sharpe'])
            if not scatter_df.empty:
                # Create custom hover template for better mobile readability
                hover_template = (
                    "<b>%{customdata[0]}</b><br>" +
                    "Ticker: %{customdata[1]}<br>" +
                    "Volatility: %{x:.1f}%<br>" +
                    "Sharpe Ratio: %{y:.2f}<br>" +
                    "Value: ¥%{customdata[2]:,.0f}<extra></extra>"
                )
                
                # Prepare custom data for hover
                custom_data_cols = []
                if 'name' in scatter_df.columns:
                    custom_data_cols.append(scatter_df['name'].fillna(scatter_df['ticker']))
                else:
                    custom_data_cols.append(scatter_df['ticker'])
                custom_data_cols.append(scatter_df['ticker'])
                custom_data_cols.append(scatter_df['value_jp'] if 'value_jp' in scatter_df.columns else [0]*len(scatter_df))
                
                custom_data = np.column_stack(custom_data_cols)
                
                fig_scatter = px.scatter(
                    scatter_df, 
                    x='sigma', 
                    y='sharpe', 
                    size='value_jp', 
                    color='ticker',
                    title='Risk (Volatility) vs Efficiency (Sharpe Ratio)',
                    labels={'sigma': 'Volatility (Risk) [%]', 'sharpe': 'Sharpe Ratio'}
                )
                
                # Update traces to remove text labels and improve hover
                fig_scatter.update_traces(
                    customdata=custom_data,
                    hovertemplate=hover_template,
                    textposition=None
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
                # Get historical data for each ticker in the portfolio
                portfolio_hist = {}
                tickers_in_portfolio = df['ticker'].tolist()
                shares_dict = dict(zip(df['ticker'], df['shares']))
                
                for ticker in tickers_in_portfolio:
                    if shares_dict.get(ticker, 0) > 0:
                        try:
                            stock = yf.Ticker(ticker)
                            hist = stock.history(start=start_date, end=end_date)
                            if not hist.empty:
                                portfolio_hist[ticker] = hist['Close']
                        except Exception:
                            pass
                
                if portfolio_hist:
                    # Create a DataFrame with all ticker prices
                    price_df = pd.DataFrame(portfolio_hist)
                    
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
                    st.info("Unable to fetch historical data for portfolio tickers.")
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
        "dividend_yield": st.column_config.NumberColumn("Dividend Yield", format="%.2f%%"),
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
