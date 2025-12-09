"""Analysis page - Risk analysis and correlations."""

import streamlit as st
import pandas as pd
import plotly.express as px
import glob
import os
import re
from ..components import RiskReturnChart
from ..chart_utils import apply_mobile_layout


class AnalysisPage:
    """Analysis page for risk and correlation analysis."""
    
    @staticmethod
    def render(df: pd.DataFrame, view_mode: str, selected_file: str = None):
        """Render the analysis page.
        
        Args:
            df: Portfolio DataFrame
            view_mode: Current view mode
            selected_file: Selected file path (if any)
        """
        st.title("📊 Portfolio Analysis")
        
        # Create tabs for different analyses
        tab1, tab2, tab3 = st.tabs(["Risk vs Return", "Correlation Matrix", "Metrics"])
        
        with tab1:
            RiskReturnChart.render(df)
        
        with tab2:
            AnalysisPage._render_correlation_matrix(view_mode, selected_file)
        
        with tab3:
            AnalysisPage._render_metrics(df)
    
    @staticmethod
    def _render_correlation_matrix(view_mode: str, selected_file: str = None):
        """Render correlation matrix heatmaps."""
        # Identify files to show correlation for
        files_to_show = []
        if selected_file:
            files_to_show.append(selected_file)
        elif view_mode == "Combined (Latest)":
            # Find latest files again
            us = glob.glob(os.path.join("output", "portfolio_result_*.csv"))
            jp = glob.glob(os.path.join("output", "portfolio_jp_result_*.csv"))
            if us:
                files_to_show.append(sorted(us, key=os.path.getmtime, reverse=True)[0])
            if jp:
                files_to_show.append(sorted(jp, key=os.path.getmtime, reverse=True)[0])
        
        if files_to_show:
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
                        fig_corr = px.imshow(
                            corr_df, 
                            text_auto=True, 
                            title=f"Correlation Matrix {title_suffix}"
                        )
                        apply_mobile_layout(fig_corr, show_legend=False)
                        st.plotly_chart(fig_corr, width="stretch")
                    else:
                        st.info(f"Correlation data not found for {os.path.basename(f_path)}")
        else:
            st.info("Select a specific file to view correlation matrix.")
    
    @staticmethod
    def _render_metrics(df: pd.DataFrame):
        """Render metrics analysis."""
        st.subheader("Metrics Analysis")
        if 'sharpe' in df.columns and 'ticker' in df.columns:
            # Drop NAs for plotting
            plot_df = df.dropna(subset=['sharpe'])
            if not plot_df.empty:
                fig_bar = px.bar(
                    plot_df, 
                    x='ticker', 
                    y='sharpe', 
                    title='Sharpe Ratio by Ticker', 
                    color='ticker'
                )
                apply_mobile_layout(fig_bar)
                fig_bar.update_layout(xaxis_tickangle=-45)
                st.plotly_chart(fig_bar, width="stretch")
            else:
                st.write("No Sharpe Ratio data available.")
