"""Sena Investment Portfolio Application - Modular Version.

This is the refactored version of portfolio_app.py using a modular, page-based structure.
It provides the same functionality with improved organization and maintainability.
"""

import streamlit as st
import pandas as pd
import glob
import os
import re
from datetime import datetime

# Import UI components and pages
from src.ui.state import AppState
from src.ui.components import SettingsSidebar
from src.ui.pages import (
    HomePage, AnalysisPage, OptimizationPage, RebalancingPage, HistoryPage,
    MLPredictionsPage, NewsSentimentPage
)
from src.utils.file_utils import extract_timestamp_from_filename
from src.ui.constants import MOBILE_CSS, UI_TEXT, DEFAULT_LANGUAGE

# Configure page
st.set_page_config(page_title="Sena Investment", layout="wide")

# Mobile optimization CSS
st.markdown(MOBILE_CSS, unsafe_allow_html=True)

# Initialize state
AppState.initialize()

# Placeholder for data update timestamp
data_timestamp_placeholder = st.empty()

# Render sidebar and get settings
settings = SettingsSidebar.render()

# Load data based on view mode
df = None
selected_file = None
loaded_file_names = []

if settings['view_mode'] == "Combined (Latest)":
    # Find latest US and JP results
    us_files = glob.glob(os.path.join("output", "portfolio_result_*.csv"))
    jp_files = glob.glob(os.path.join("output", "portfolio_jp_result_*.csv"))
    
    dfs = []
    loaded_files = []
    
    if us_files:
        us_files.sort(key=os.path.getmtime, reverse=True)
        dfs.append(pd.read_csv(us_files[0]))
        loaded_files.append(os.path.basename(us_files[0]))
        
    if jp_files:
        jp_files.sort(key=os.path.getmtime, reverse=True)
        dfs.append(pd.read_csv(jp_files[0]))
        loaded_files.append(os.path.basename(jp_files[0]))
        
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
        # Recalculate ratio for the combined portfolio
        total_val_jp = df['value_jp'].sum()
        if total_val_jp > 0:
            df['ratio'] = (df['value_jp'] / total_val_jp * 100).round(2)
        
        st.sidebar.info(f"Loaded: {', '.join(loaded_files)}")
        loaded_file_names = loaded_files
    else:
        st.info("No result files found to combine.")

else:
    # Individual File Selection
    if settings['view_mode'] == "US History":
        file_pattern = "portfolio_result_*.csv"
    else:
        file_pattern = "portfolio_jp_result_*.csv"
        
    files = glob.glob(os.path.join("output", file_pattern))
    files.sort(key=os.path.getmtime, reverse=True)
    
    uploaded_file = st.sidebar.file_uploader("Upload a result CSV", type="csv", key=settings['view_mode'])
    selected_file = st.sidebar.selectbox(f"Select a {settings['view_mode']} file", [""] + files, key=f"select_{settings['view_mode']}")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        loaded_file_names = [uploaded_file.name]
    elif selected_file:
        df = pd.read_csv(selected_file)
        loaded_file_names = [os.path.basename(selected_file)]
    elif files:
        st.sidebar.info(f"Auto-loading latest file: {os.path.basename(files[0])}")
        df = pd.read_csv(files[0])
        loaded_file_names = [os.path.basename(files[0])]
    else:
        st.info(f"No {settings['view_mode']} files found. Please upload or run update.")

# Store data in state
if df is not None:
    AppState.set_portfolio_df(df, loaded_file_names)

# Display data update timestamp
if loaded_file_names:
    timestamps = []
    for fname in loaded_file_names:
        ts = extract_timestamp_from_filename(fname)
        if ts:
            if "portfolio_jp" in fname:
                timestamps.append(f"JP: {ts}")
            elif "portfolio_result" in fname:
                timestamps.append(f"US: {ts}")
            else:
                timestamps.append(ts)
    if timestamps:
        data_timestamp_placeholder.caption(f"📅 Data Updated: {' / '.join(timestamps)}")

# Main content - Page routing
if df is not None:
    # Navigation - use constants for i18n support
    text = UI_TEXT[DEFAULT_LANGUAGE]
    page = st.sidebar.radio(
        text['navigation'],
        [text['home'], text['analysis'], text['optimization'], text['rebalancing'], 
         text['history'], text['ml_predictions'], text['news_sentiment']],
        label_visibility="collapsed"
    )
    
    # Route to appropriate page
    if page == text['home']:
        HomePage.render(df, settings['alert_threshold'])
    elif page == text['analysis']:
        AnalysisPage.render(df, settings['view_mode'], selected_file)
    elif page == text['optimization']:
        OptimizationPage.render(df, selected_file, settings['view_mode'])
    elif page == text['rebalancing']:
        RebalancingPage.render(df)
    elif page == text['history']:
        HistoryPage.render(df)
    elif page == text['ml_predictions']:
        MLPredictionsPage.render(df)
    elif page == text['news_sentiment']:
        NewsSentimentPage.render(df)
else:
    st.info("Please load portfolio data using the sidebar or run 'Update Data'.")
