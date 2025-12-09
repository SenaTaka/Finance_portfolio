"""
Data Loader Module for UI

Handles loading and combining portfolio data for the UI.
"""

import pandas as pd
import os
from typing import Optional, List, Tuple

from ..utils.file_utils import get_latest_result_file, get_result_files


class DataLoader:
    """Loads and manages portfolio data for the UI."""
    
    @staticmethod
    def load_combined_latest() -> Tuple[Optional[pd.DataFrame], List[str]]:
        """
        Load and combine the latest US and JP portfolio results.
        
        Returns:
            Tuple of (combined DataFrame, list of loaded filenames)
        """
        us_file = get_latest_result_file("portfolio_result_*.csv")
        jp_file = get_latest_result_file("portfolio_jp_result_*.csv")
        
        dfs = []
        loaded_files = []
        
        if us_file:
            dfs.append(pd.read_csv(us_file))
            loaded_files.append(os.path.basename(us_file))
        
        if jp_file:
            dfs.append(pd.read_csv(jp_file))
            loaded_files.append(os.path.basename(jp_file))
        
        if not dfs:
            return None, []
        
        # Combine DataFrames
        df = pd.concat(dfs, ignore_index=True)
        
        # Recalculate ratio for combined portfolio
        total_val_jp = df['value_jp'].sum()
        if total_val_jp > 0:
            df['ratio'] = (df['value_jp'] / total_val_jp * 100).round(2)
        
        return df, loaded_files
    
    @staticmethod
    def load_file(file_path: str) -> Optional[pd.DataFrame]:
        """
        Load a single portfolio result file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            DataFrame or None
        """
        if not file_path or not os.path.exists(file_path):
            return None
        
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            print(f"Error loading file {file_path}: {e}")
            return None
    
    @staticmethod
    def get_available_files(pattern: str) -> List[str]:
        """
        Get list of available files matching pattern.
        
        Args:
            pattern: File pattern to match
            
        Returns:
            List of file paths
        """
        return get_result_files(pattern)
    
    @staticmethod
    def load_correlation_matrix(result_file: str) -> Optional[pd.DataFrame]:
        """
        Load correlation matrix corresponding to a result file.
        
        Args:
            result_file: Path to result file
            
        Returns:
            Correlation matrix DataFrame or None
        """
        from ..utils.file_utils import find_correlation_file
        
        corr_file = find_correlation_file(result_file)
        if corr_file:
            try:
                return pd.read_csv(corr_file, index_col=0)
            except Exception as e:
                print(f"Error loading correlation file: {e}")
        
        return None
