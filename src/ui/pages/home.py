"""Home page - Portfolio overview."""

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh
from ..components import PortfolioMetrics, AllocationChart, SectorChart, DetailedDataTable, RealtimeUpdates


class HomePage:
    """Home page showing portfolio overview."""
    
    @staticmethod
    def render(df: pd.DataFrame, alert_threshold: float):
        """Render the home page.
        
        Args:
            df: Portfolio DataFrame
            alert_threshold: Alert threshold for value changes
        """
        st.title("Sena Investment")
        
        # Real-time auto-refresh (every 60 seconds)
        # Only refresh if user enables it
        enable_autorefresh = st.sidebar.checkbox("⚡ Enable Auto-Refresh", value=False, 
                                                  help="Automatically refresh prices every 60 seconds")
        
        if enable_autorefresh:
            # Auto-refresh every 60 seconds
            count = st_autorefresh(interval=60000, key="portfolio_refresh")
            if count > 0:
                st.sidebar.caption(f"Auto-refreshed {count} times")
        
        # Portfolio metrics
        PortfolioMetrics.render(df, alert_threshold)
        
        # Charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            AllocationChart.render(df)
        
        with col2:
            SectorChart.render(df)
        
        st.divider()
        
        # Real-time updates section
        with st.expander("⚡ Real-time Price Updates", expanded=False):
            RealtimeUpdates.render(df, update_interval=60)
        
        st.divider()
        
        # Detailed data table
        DetailedDataTable.render(df)
