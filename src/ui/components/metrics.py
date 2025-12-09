"""Portfolio metrics component."""

import streamlit as st
import pandas as pd
from datetime import datetime


class PortfolioMetrics:
    """Component for displaying portfolio metrics."""
    
    @staticmethod
    def render(df: pd.DataFrame, alert_threshold: float = 5.0):
        """Render portfolio metrics.
        
        Args:
            df: Portfolio DataFrame
            alert_threshold: Threshold for alerting on value changes (%)
        """
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

        # Alert on significant changes
        if total_value_jp is not None:
            prev_total = st.session_state.get("prev_total_value_jp")
            if prev_total:
                change_pct = (total_value_jp - prev_total) / prev_total * 100
                if abs(change_pct) >= alert_threshold:
                    st.sidebar.error(f"Portfolio moved {change_pct:.2f}% since last load")
            st.session_state["prev_total_value_jp"] = total_value_jp
            st.session_state["last_update_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
