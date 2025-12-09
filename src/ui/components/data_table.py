"""Data table component for displaying detailed portfolio data."""

import streamlit as st
import pandas as pd


class DetailedDataTable:
    """Component for displaying detailed portfolio data."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render detailed data table.
        
        Args:
            df: Portfolio DataFrame
        """
        st.subheader("Detailed Data")
        
        # Column configuration for better display
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
