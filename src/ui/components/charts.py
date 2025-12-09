"""Chart components for portfolio visualization."""

import streamlit as st
import pandas as pd
import plotly.express as px
from ..chart_utils import apply_mobile_layout


class AllocationChart:
    """Component for portfolio allocation pie chart."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render portfolio allocation chart.
        
        Args:
            df: Portfolio DataFrame
        """
        if 'value_jp' in df.columns and 'ticker' in df.columns:
            st.subheader("Portfolio Allocation (JPY)")

            # Prepare labels: "Name (Ticker)"
            plot_df = df.copy()
            if 'name' in plot_df.columns:
                plot_df['label'] = plot_df.apply(
                    lambda x: f"{x['name']} ({x['ticker']})" if pd.notnull(x['name']) else x['ticker'], 
                    axis=1
                )
                names_col = 'label'
            else:
                names_col = 'ticker'

            fig_pie = px.pie(
                plot_df, 
                values='value_jp', 
                names=names_col, 
                title='Portfolio Allocation by Value (JPY)', 
                hole=0.4
            )
            fig_pie.update_traces(
                textposition='none', 
                hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>'
            )
            apply_mobile_layout(fig_pie)
            st.plotly_chart(fig_pie, width="stretch")


class SectorChart:
    """Component for sector analysis chart."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render sector analysis chart.
        
        Args:
            df: Portfolio DataFrame
        """
        st.subheader("Sector Analysis")
        if 'sector' in df.columns and 'value_jp' in df.columns:
            # Group by sector
            sector_df = df.groupby('sector')['value_jp'].sum().reset_index()
            fig_sector = px.pie(
                sector_df, 
                values='value_jp', 
                names='sector', 
                title='Portfolio Allocation by Sector', 
                hole=0.4
            )
            fig_sector.update_traces(
                textposition='none', 
                hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>'
            )
            apply_mobile_layout(fig_sector)
            st.plotly_chart(fig_sector, width="stretch")
        else:
            st.info("Sector data not available. Please update data.")


class RiskReturnChart:
    """Component for risk vs return scatter plot."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render risk vs return scatter plot.
        
        Args:
            df: Portfolio DataFrame
        """
        if 'sigma' in df.columns and 'sharpe' in df.columns:
            scatter_df = df.dropna(subset=['sigma', 'sharpe']).copy()
            if not scatter_df.empty:
                # Create label column for display
                if 'name' in scatter_df.columns:
                    scatter_df['display_name'] = scatter_df['name'].fillna(scatter_df['ticker'])
                else:
                    scatter_df['display_name'] = scatter_df['ticker']
                
                # Ensure value_jp exists for hover
                if 'value_jp' not in scatter_df.columns:
                    scatter_df['value_jp'] = 0
                
                fig_scatter = px.scatter(
                    scatter_df, 
                    x='sigma', 
                    y='sharpe', 
                    size='value_jp', 
                    color='display_name',
                    hover_data={
                        'display_name': True,
                        'ticker': True,
                        'sigma': ':.1f',
                        'sharpe': ':.2f',
                        'value_jp': ':,.0f'
                    },
                    title='Risk (Volatility) vs Efficiency (Sharpe Ratio)',
                    labels={
                        'sigma': 'Volatility (Risk) [%]', 
                        'sharpe': 'Sharpe Ratio',
                        'display_name': 'Name',
                        'value_jp': 'Value (JPY)'
                    }
                )
                
                # Apply mobile-optimized layout
                fig_scatter.update_layout(
                    margin=dict(l=10, r=10, t=40, b=40),
                    showlegend=False,
                    xaxis=dict(title=dict(font=dict(size=12))),
                    yaxis=dict(title=dict(font=dict(size=12))),
                )
                
                st.plotly_chart(fig_scatter, width="stretch")
                st.caption("💡 Tap to view stock details")
            else:
                st.write("Insufficient data for Risk analysis.")
