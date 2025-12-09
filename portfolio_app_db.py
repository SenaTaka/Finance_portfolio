"""Streamlit app with database integration for multiple portfolios."""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Import database components
from src.database import init_db, PortfolioManager, DatabaseCacheManager
from portfolio_calculator_db import PortfolioCalculatorDB

st.set_page_config(page_title="Sena Investment - Multi-Portfolio", layout="wide")

# Initialize database
init_db()

# Mobile optimization CSS (keep existing CSS)
st.markdown("""
<style>
@media (max-width: 768px) {
    .stButton > button { min-height: 48px; font-size: 16px; }
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    .stDataFrame { overflow-x: auto; }
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
}
</style>
""", unsafe_allow_html=True)

st.title("Sena Investment - Multi-Portfolio Manager")

# Sidebar for portfolio management
st.sidebar.header("Portfolio Management")

# Initialize portfolio manager
portfolio_mgr = PortfolioManager()

# Portfolio selection
portfolios = portfolio_mgr.list_portfolios()
if portfolios:
    portfolio_names = [p.name for p in portfolios]
    selected_portfolio_name = st.sidebar.selectbox(
        "Select Portfolio",
        portfolio_names,
        key="portfolio_selector"
    )
    selected_portfolio = next(p for p in portfolios if p.name == selected_portfolio_name)
else:
    st.sidebar.info("No portfolios found. Create one or import from CSV.")
    selected_portfolio = None
    selected_portfolio_name = None

# Portfolio actions
st.sidebar.subheader("Actions")

# Import portfolio from CSV
with st.sidebar.expander("📥 Import from CSV"):
    uploaded_file = st.file_uploader("Upload portfolio CSV", type="csv", key="import_csv")
    portfolio_name_input = st.text_input("Portfolio Name", key="import_name")
    
    if st.button("Import", key="import_btn"):
        if uploaded_file and portfolio_name_input:
            # Save uploaded file temporarily
            temp_path = f"/tmp/{uploaded_file.name}"
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            try:
                portfolio = portfolio_mgr.import_from_csv(temp_path, portfolio_name_input)
                st.sidebar.success(f"Imported portfolio: {portfolio.name}")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Import failed: {e}")
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            st.sidebar.warning("Please provide both file and name")

# Create new portfolio
with st.sidebar.expander("➕ Create New Portfolio"):
    new_name = st.text_input("Portfolio Name", key="new_name")
    new_desc = st.text_area("Description", key="new_desc")
    
    if st.button("Create", key="create_btn"):
        if new_name:
            try:
                portfolio = portfolio_mgr.create_portfolio(new_name, new_desc)
                st.sidebar.success(f"Created portfolio: {portfolio.name}")
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"Creation failed: {e}")
        else:
            st.sidebar.warning("Please provide a name")

# Update data button
if selected_portfolio:
    force_refresh = st.sidebar.checkbox("Force full refresh", value=False)
    
    if st.sidebar.button("🔄 Update Data", key="update_btn"):
        with st.spinner("Fetching latest data..."):
            try:
                # Get holdings
                holdings_df = portfolio_mgr.get_holdings(selected_portfolio.id)
                
                if holdings_df.empty:
                    st.sidebar.warning("No holdings in this portfolio")
                else:
                    # Create temporary CSV
                    temp_csv = f"/tmp/portfolio_{selected_portfolio.id}.csv"
                    holdings_df.to_csv(temp_csv, index=False)
                    
                    # Run calculator
                    calculator = PortfolioCalculatorDB(
                        temp_csv,
                        force_refresh=force_refresh,
                        portfolio_name=selected_portfolio.name
                    )
                    calculator.run()
                    calculator.close()
                    
                    # Clean up
                    if os.path.exists(temp_csv):
                        os.remove(temp_csv)
                    
                    st.sidebar.success("Data updated successfully!")
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"Update failed: {e}")

# Main content
if selected_portfolio is None:
    st.info("👈 Select or create a portfolio to get started")
else:
    # Display portfolio info
    st.subheader(f"Portfolio: {selected_portfolio.name}")
    if selected_portfolio.description:
        st.caption(selected_portfolio.description)
    
    # Get current holdings
    holdings_df = portfolio_mgr.get_holdings(selected_portfolio.id)
    
    if holdings_df.empty:
        st.warning("No holdings in this portfolio. Import data or add holdings.")
    else:
        # Display holdings
        with st.expander("📋 Current Holdings", expanded=True):
            st.dataframe(holdings_df, hide_index=True, use_container_width=True)
        
        # Get historical data
        history_df = portfolio_mgr.get_history(selected_portfolio.id, days=365)
        
        if not history_df.empty:
            # Show latest snapshot
            latest = history_df.iloc[-1]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Total Value (USD)",
                    f"${latest['total_value_usd']:,.2f}"
                )
            with col2:
                st.metric(
                    "Total Value (JPY)",
                    f"¥{latest['total_value_jpy']:,.0f}"
                )
            with col3:
                st.metric(
                    "USD/JPY Rate",
                    f"{latest['usd_jpy_rate']:.2f}"
                )
            
            # Historical chart
            st.subheader("📈 Portfolio Value History")
            
            # Allow user to select time period
            period_options = {
                "1 Week": 7,
                "1 Month": 30,
                "3 Months": 90,
                "6 Months": 180,
                "1 Year": 365,
            }
            selected_period = st.selectbox(
                "Time Period",
                list(period_options.keys()),
                index=2,
                key="history_period"
            )
            
            days = period_options[selected_period]
            filtered_history = portfolio_mgr.get_history(selected_portfolio.id, days=days)
            
            if not filtered_history.empty:
                # Create figure with both USD and JPY
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=filtered_history['snapshot_date'],
                    y=filtered_history['total_value_jpy'],
                    mode='lines+markers',
                    name='JPY Value',
                    line=dict(color='#1f77b4', width=2),
                    yaxis='y1'
                ))
                
                fig.add_trace(go.Scatter(
                    x=filtered_history['snapshot_date'],
                    y=filtered_history['total_value_usd'],
                    mode='lines+markers',
                    name='USD Value',
                    line=dict(color='#ff7f0e', width=2),
                    yaxis='y2'
                ))
                
                fig.update_layout(
                    title=f'Portfolio Value Over Time ({selected_period})',
                    xaxis=dict(title='Date'),
                    yaxis=dict(
                        title='JPY Value',
                        titlefont=dict(color='#1f77b4'),
                        tickfont=dict(color='#1f77b4'),
                        tickformat=','
                    ),
                    yaxis2=dict(
                        title='USD Value',
                        titlefont=dict(color='#ff7f0e'),
                        tickfont=dict(color='#ff7f0e'),
                        overlaying='y',
                        side='right',
                        tickformat=','
                    ),
                    hovermode='x unified',
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show performance metrics
                if len(filtered_history) > 1:
                    first_val = filtered_history.iloc[0]['total_value_jpy']
                    last_val = filtered_history.iloc[-1]['total_value_jpy']
                    change = last_val - first_val
                    change_pct = (change / first_val * 100) if first_val > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(
                            f"Change ({selected_period})",
                            f"¥{change:,.0f}",
                            f"{change_pct:+.2f}%"
                        )
                    with col2:
                        st.metric(
                            "Starting Value",
                            f"¥{first_val:,.0f}"
                        )
                    with col3:
                        st.metric(
                            "Current Value",
                            f"¥{last_val:,.0f}"
                        )
            else:
                st.info(f"No history data for selected period ({selected_period})")
        else:
            st.info("No historical data available. Update data to start tracking.")

# Portfolio comparison section
if len(portfolios) > 1:
    st.divider()
    st.subheader("📊 Portfolio Comparison")
    
    # Multi-select for portfolios to compare
    compare_portfolios = st.multiselect(
        "Select portfolios to compare",
        portfolio_names,
        default=portfolio_names[:min(3, len(portfolio_names))],
        key="compare_select"
    )
    
    if len(compare_portfolios) >= 2:
        # Get latest values for each portfolio
        comparison_data = []
        for p_name in compare_portfolios:
            p = next((p for p in portfolios if p.name == p_name), None)
            if p:
                history = portfolio_mgr.get_history(p.id, days=1)
                if not history.empty:
                    latest = history.iloc[-1]
                    comparison_data.append({
                        'Portfolio': p_name,
                        'Value (JPY)': latest['total_value_jpy'],
                        'Value (USD)': latest['total_value_usd'],
                    })
        
        if comparison_data:
            comp_df = pd.DataFrame(comparison_data)
            
            # Create bar chart
            fig = px.bar(
                comp_df,
                x='Portfolio',
                y='Value (JPY)',
                title='Portfolio Values Comparison (JPY)',
                text='Value (JPY)'
            )
            fig.update_traces(texttemplate='¥%{text:,.0f}', textposition='outside')
            fig.update_layout(yaxis_tickformat=',')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show table
            st.dataframe(
                comp_df,
                hide_index=True,
                use_container_width=True,
                column_config={
                    'Value (JPY)': st.column_config.NumberColumn(format="¥%.0f"),
                    'Value (USD)': st.column_config.NumberColumn(format="$%.2f"),
                }
            )
        else:
            st.info("No data available for selected portfolios")

# Footer
st.divider()
st.caption("💾 Data stored in SQLite database: data/portfolio.db")

# Clean up
portfolio_mgr.close()
