"""Settings sidebar component."""

import streamlit as st
import os

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    st_autorefresh = None

try:
    from portfolio_calculator import PortfolioCalculator
except ImportError:
    PortfolioCalculator = None


class SettingsSidebar:
    """Component for the settings sidebar."""
    
    @staticmethod
    def render():
        """Render the settings sidebar and return selected options.
        
        Returns:
            dict: Dictionary containing sidebar settings
        """
        st.sidebar.header("Settings")
        
        # Auto-refresh settings
        auto_refresh = st.sidebar.checkbox("Enable auto-refresh", value=False)
        refresh_minutes = st.sidebar.slider("Refresh interval (minutes)", 1, 60, 5)
        
        if auto_refresh:
            if st_autorefresh:
                st_autorefresh(interval=refresh_minutes * 60 * 1000, key="portfolio_autorefresh")
            else:
                st.sidebar.warning("streamlit_autorefresh is not installed. Auto-refresh is disabled.")
        
        alert_threshold = st.sidebar.number_input(
            "Alert threshold for total value change (%)", 
            min_value=1, 
            max_value=50, 
            value=5
        )
        
        # Force refresh option
        force_refresh = st.sidebar.checkbox(
            "Force full refresh (ignore cache)", 
            value=False,
            help="When checked, fetches all data from API ignoring cached values"
        )
        
        # Update Data Button
        if st.sidebar.button("🔄 Update Data"):
            SettingsSidebar._update_data(force_refresh)
        
        # View Mode Selection
        view_mode = st.sidebar.radio("View Mode", ["Combined (Latest)", "US History", "JP History"])
        
        return {
            'auto_refresh': auto_refresh,
            'refresh_minutes': refresh_minutes,
            'alert_threshold': alert_threshold,
            'force_refresh': force_refresh,
            'view_mode': view_mode
        }
    
    @staticmethod
    def _update_data(force_refresh: bool):
        """Update portfolio data."""
        with st.spinner("Fetching latest data..."):
            target_files = ["portfolio.csv", "portfolio_jp.csv"]
            updated_count = 0
            
            for input_csv in target_files:
                if os.path.exists(input_csv):
                    try:
                        if PortfolioCalculator is not None:
                            calculator = PortfolioCalculator(input_csv, force_refresh=force_refresh)
                            calculator.run()
                            updated_count += 1
                    except Exception as e:
                        st.sidebar.error(f"Error updating {input_csv}: {e}")
                else:
                    if input_csv == "portfolio.csv":
                        st.sidebar.warning(f"{input_csv} not found.")

            if updated_count > 0:
                st.sidebar.success(f"Updated {updated_count} files successfully!")
                st.rerun()
