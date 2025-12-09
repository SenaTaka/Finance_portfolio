"""State management for the Streamlit application."""

import streamlit as st
import pandas as pd
from typing import Optional, Dict, Any


class AppState:
    """Manages application state using Streamlit session state."""
    
    @staticmethod
    def initialize():
        """Initialize default session state values."""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.prev_total_value_jp = None
            st.session_state.last_update_ts = None
            st.session_state.current_df = None
            st.session_state.loaded_file_names = []
    
    @staticmethod
    def get_portfolio_df() -> Optional[pd.DataFrame]:
        """Get the current portfolio DataFrame.
        
        Returns:
            Current portfolio DataFrame or None
        """
        return st.session_state.get('current_df')
    
    @staticmethod
    def set_portfolio_df(df: pd.DataFrame, file_names: list = None):
        """Set the current portfolio DataFrame.
        
        Args:
            df: Portfolio DataFrame to store
            file_names: List of loaded file names
        """
        st.session_state.current_df = df
        if file_names is not None:
            st.session_state.loaded_file_names = file_names
    
    @staticmethod
    def get_loaded_files() -> list:
        """Get list of loaded file names.
        
        Returns:
            List of loaded file names
        """
        return st.session_state.get('loaded_file_names', [])
    
    @staticmethod
    def get(key: str, default: Any = None) -> Any:
        """Get a value from session state.
        
        Args:
            key: Session state key
            default: Default value if key doesn't exist
            
        Returns:
            Value from session state or default
        """
        return st.session_state.get(key, default)
    
    @staticmethod
    def set(key: str, value: Any):
        """Set a value in session state.
        
        Args:
            key: Session state key
            value: Value to store
        """
        st.session_state[key] = value
    
    @staticmethod
    def clear():
        """Clear all session state."""
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        AppState.initialize()
