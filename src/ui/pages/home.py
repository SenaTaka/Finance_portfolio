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
        
        # Real-time auto-refresh (configurable interval)
        # Only refresh if user enables it
        from ..constants import REALTIME_REFRESH_INTERVAL_MS, REALTIME_REFRESH_INTERVAL_SEC
        
        enable_autorefresh = st.sidebar.checkbox("⚡ Enable Auto-Refresh", value=False, 
                                                  help=f"Automatically refresh prices every {REALTIME_REFRESH_INTERVAL_SEC} seconds")
        
        if enable_autorefresh:
            # Auto-refresh at configured interval
            count = st_autorefresh(interval=REALTIME_REFRESH_INTERVAL_MS, key="portfolio_refresh")
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
        from ..constants import REALTIME_REFRESH_INTERVAL_SEC
        with st.expander("⚡ Real-time Price Updates", expanded=False):
            RealtimeUpdates.render(df, update_interval=REALTIME_REFRESH_INTERVAL_SEC)
        
        st.divider()
        
        # Detailed data table
        DetailedDataTable.render(df)
