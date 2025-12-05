import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None
try:
    from portfolio_calculator import PortfolioCalculator
except ImportError:
    pass

st.set_page_config(page_title="Sena Investment", layout="wide")

st.title("Sena Investment")


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
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("Sector Analysis")
        if 'sector' in df.columns and 'value_jp' in df.columns:
            # Group by sector
            sector_df = df.groupby('sector')['value_jp'].sum().reset_index()
            fig_sector = px.pie(sector_df, values='value_jp', names='sector', title='Portfolio Allocation by Sector', hole=0.4)
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
                fig_scatter = px.scatter(
                    scatter_df, 
                    x='sigma', 
                    y='sharpe', 
                    size='value_jp', 
                    color='sector' if 'sector' in df.columns else 'ticker',
                    hover_name='name' if 'name' in df.columns else 'ticker',
                    text='ticker',
                    title='Risk (Volatility) vs Efficiency (Sharpe Ratio)',
                    labels={'sigma': 'Volatility (Risk) [%]', 'sharpe': 'Sharpe Ratio'}
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
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
                st.plotly_chart(fig_region, use_container_width=True)
    else:
        st.info("Run update to capture sector and country metadata for factor views.")

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
