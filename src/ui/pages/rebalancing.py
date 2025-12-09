"""Rebalancing page - Rebalance suggestions and scenario analysis."""

import streamlit as st
import pandas as pd
import plotly.express as px
from ..chart_utils import apply_mobile_layout


def get_region(country: str) -> str:
    """Get region from country name."""
    if not isinstance(country, str):
        return "Unknown"
    
    north_america = {"United States", "Canada"}
    europe = {
        "United Kingdom", "Germany", "France", "Switzerland", "Netherlands",
        "Sweden", "Spain", "Italy", "Ireland",
    }
    asia = {"Japan", "China", "Hong Kong", "India", "South Korea", "Taiwan", "Singapore"}
    
    if country in north_america:
        return "North America"
    if country in europe:
        return "Europe"
    if country in asia:
        return "Asia"
    return "Other"


class RebalancingPage:
    """Rebalancing page for portfolio rebalancing and scenario analysis."""
    
    @staticmethod
    def render(df: pd.DataFrame):
        """Render the rebalancing page.
        
        Args:
            df: Portfolio DataFrame
        """
        st.title("⚖️ Rebalancing & Scenario Analysis")
        
        # Create tabs
        tab1, tab2, tab3 = st.tabs(["Rebalance Suggestions", "Scenario Analysis", "Risk Factors"])
        
        with tab1:
            RebalancingPage._render_rebalance_suggestions(df)
        
        with tab2:
            RebalancingPage._render_scenario_analysis(df)
        
        with tab3:
            RebalancingPage._render_risk_factors(df)
    
    @staticmethod
    def _render_rebalance_suggestions(df: pd.DataFrame):
        """Render rebalancing suggestions."""
        st.subheader("Rebalance Suggestions")
        
        profile = st.selectbox("Risk profile", ["Conservative", "Balanced", "Aggressive"], index=1)
        min_ticket_threshold = st.slider("Ignore differences smaller than (JPY)", 0, 500000, 50000, step=10000)
        
        risk_power = {"Conservative": 1.5, "Balanced": 1.0, "Aggressive": 0.5}[profile]
        
        total_value_jp = df['value_jp'].sum() if 'value_jp' in df.columns else None
        
        if 'sigma' in df.columns and df['sigma'].notna().any():
            vol = df['sigma'].fillna(df['sigma'].median())
            inv_risk = (1 / vol) ** risk_power
            target_weights = inv_risk / inv_risk.sum()
        else:
            target_weights = pd.Series(1, index=df.index)
            target_weights = target_weights / target_weights.sum()
        
        df['target_ratio'] = (target_weights * 100).round(2)
        
        if total_value_jp:
            df['target_value_jp'] = (target_weights * total_value_jp).round(0)
            df['delta_value_jp'] = df['target_value_jp'] - df['value_jp']
            suggestion_df = df[['ticker', 'name', 'ratio', 'target_ratio', 'value_jp', 'target_value_jp', 'delta_value_jp']]
            suggestion_df = suggestion_df[abs(suggestion_df['delta_value_jp']) >= min_ticket_threshold]
            
            if suggestion_df.empty:
                st.info("Portfolio is within threshold of target weights.")
            else:
                st.dataframe(
                    suggestion_df,
                    width="stretch",
                    hide_index=True,
                    column_config={
                        "ratio": st.column_config.NumberColumn("Current %", format="%.2f%%"),
                        "target_ratio": st.column_config.NumberColumn("Target %", format="%.2f%%"),
                        "value_jp": st.column_config.NumberColumn("Current (JPY)", format="¥%.0f"),
                        "target_value_jp": st.column_config.NumberColumn("Target (JPY)", format="¥%.0f"),
                        "delta_value_jp": st.column_config.NumberColumn("Buy (+) / Sell (-)", format="¥%.0f"),
                    },
                )
        else:
            st.info("JPY valuation is required to generate rebalance suggestions.")
    
    @staticmethod
    def _render_scenario_analysis(df: pd.DataFrame):
        """Render scenario analysis and stress testing."""
        st.subheader("Scenario analysis & stress test")
        
        shock_price = st.slider("Equity price shock (%)", -50, 50, -10)
        shock_fx = st.slider("USD/JPY shock (%)", -20, 20, 0)
        vol_multiplier = st.slider("Volatility multiplier", 0.5, 2.0, 1.2, step=0.1)
        
        scenario_df = df.copy()
        total_value_jp = df['value_jp'].sum() if 'value_jp' in df.columns else None
        
        if 'value_jp' in scenario_df.columns:
            # Apply equity price shock
            scenario_df['value_jp_scenario'] = scenario_df['value_jp'] * (1 + shock_price / 100)
            
            # Apply FX shock to foreign assets
            if 'currency' in scenario_df.columns:
                is_foreign = scenario_df['currency'] != 'JPY'
                scenario_df.loc[is_foreign, 'value_jp_scenario'] *= (1 + shock_fx / 100)
        
        if 'usd_jpy_rate' in scenario_df.columns:
            scenario_df['usd_jpy_rate'] = scenario_df['usd_jpy_rate'] * (1 + shock_fx / 100)
        if 'sigma' in scenario_df.columns:
            scenario_df['sigma_scenario'] = scenario_df['sigma'] * vol_multiplier
        
        scenario_total = scenario_df.get('value_jp_scenario', pd.Series()).sum()
        if total_value_jp:
            change_vs_now = scenario_total - total_value_jp
            st.metric("Scenario Portfolio Value (JPY)", f"¥{scenario_total:,.0f}", delta=f"{change_vs_now:,.0f}")
        if 'sigma_scenario' in scenario_df:
            st.caption("Volatility after shock (annualized, %)")
            st.dataframe(scenario_df[['ticker', 'sigma', 'sigma_scenario']].dropna(), hide_index=True)
    
    @staticmethod
    def _render_risk_factors(df: pd.DataFrame):
        """Render risk factor breakdown."""
        st.subheader("Risk factor breakdown")
        
        if 'country' in df.columns:
            df['region'] = df['country'].apply(get_region)
        
        factor_cols = []
        if 'sector' in df.columns:
            factor_cols.append('sector')
        if 'region' in df.columns:
            factor_cols.append('region')
        
        total_value_jp = df['value_jp'].sum() if 'value_jp' in df.columns else None
        
        if total_value_jp and factor_cols:
            factor_tab1, factor_tab2 = st.tabs(["Sector", "Region"])
            
            if 'sector' in factor_cols:
                sector_data = (
                    df.groupby('sector')['value_jp']
                    .sum()
                    .reset_index()
                    .assign(ratio=lambda x: (x['value_jp'] / total_value_jp * 100))
                )
                with factor_tab1:
                    st.write("Sector exposure")
                    st.dataframe(sector_data, hide_index=True)
                    fig_sector = px.bar(sector_data, x='sector', y='ratio', title='Sector Weight (%)', color='sector')
                    apply_mobile_layout(fig_sector)
                    fig_sector.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig_sector, width="stretch")
            
            if 'region' in factor_cols:
                region_data = (
                    df.groupby('region')['value_jp']
                    .sum()
                    .reset_index()
                    .assign(ratio=lambda x: (x['value_jp'] / total_value_jp * 100))
                )
                with factor_tab2:
                    st.write("Regional exposure")
                    st.dataframe(region_data, hide_index=True)
                    fig_region = px.pie(region_data, values='value_jp', names='region', title='Region Allocation', hole=0.3)
                    fig_region.update_traces(textposition='none', hovertemplate='%{label}<br>%{value:,.0f} JPY<br>%{percent}<extra></extra>')
                    apply_mobile_layout(fig_region)
                    st.plotly_chart(fig_region, width="stretch")
        else:
            st.info("Run update to capture sector and country metadata for factor views.")
