import streamlit as st
import pandas as pd
import glob
import os
import plotly.express as px
try:
    from portfolio_calculator import PortfolioCalculator
except ImportError:
    pass

st.set_page_config(page_title="Sena Investment", layout="wide")

st.title("⭐️Sena Investment")

# Sidebar for file selection
st.sidebar.header("Settings")

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
        
    if 'value_jp' in df.columns:
        total_value_jp = df['value_jp'].sum()
        st.metric("Total Portfolio Value (JPY)", f"¥{total_value_jp:,.0f}")

    if 'usd_jpy_rate' in df.columns:
        rate = df['usd_jpy_rate'].iloc[0]
        st.caption(f"Exchange Rate: 1 USD = {rate:.2f} JPY")
    
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
        st.subheader("Metrics Analysis")
        if 'sharpe' in df.columns and 'ticker' in df.columns:
            # Drop NAs for plotting
            plot_df = df.dropna(subset=['sharpe'])
            if not plot_df.empty:
                fig_bar = px.bar(plot_df, x='ticker', y='sharpe', title='Sharpe Ratio by Ticker', color='ticker')
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.write("No Sharpe Ratio data available.")

    # Data Table
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
    }
    
    st.dataframe(df, use_container_width=True, column_config=column_config, hide_index=True)
