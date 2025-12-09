"""Home page - Portfolio overview."""

import streamlit as st
import pandas as pd
from ..components import PortfolioMetrics, AllocationChart, SectorChart, DetailedDataTable


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
        
        # Portfolio metrics
        PortfolioMetrics.render(df, alert_threshold)
        
        # Charts side by side
        col1, col2 = st.columns(2)
        
        with col1:
            AllocationChart.render(df)
        
        with col2:
            SectorChart.render(df)
        
        st.divider()
        
        # Detailed data table
        DetailedDataTable.render(df)
