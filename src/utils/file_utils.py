"""
File Utilities Module

Utilities for file operations related to portfolio management.
"""

import os
import glob
import re
from datetime import datetime
from typing import List, Optional, Tuple


def extract_timestamp_from_filename(filename: str) -> Optional[str]:
    """
    Extract and format the timestamp from a result file name.
    
    Args:
        filename: The filename containing a timestamp in format YYYYMMDD_HHMMSS
        
    Returns:
        Formatted timestamp string or None if not found
    """
    match = re.search(r'_result_(\d{8})_(\d{6})\.csv', filename)
    if match:
        date_str = match.group(1)
        time_str = match.group(2)
        try:
            dt = datetime.strptime(f"{date_str}_{time_str}", "%Y%m%d_%H%M%S")
            return dt.strftime("%Y/%m/%d %H:%M:%S")
        except ValueError:
            return None
    return None


def get_latest_result_file(pattern: str, directory: str = "output") -> Optional[str]:
    """
    Get the latest result file matching a pattern.
    
    Args:
        pattern: File pattern to match (e.g., "portfolio_result_*.csv")
        directory: Directory to search in
        
    Returns:
        Path to latest file or None
    """
    files = glob.glob(os.path.join(directory, pattern))
    if not files:
        return None
    
    files.sort(key=os.path.getmtime, reverse=True)
    return files[0]


def get_result_files(pattern: str, directory: str = "output") -> List[str]:
    """
    Get all result files matching a pattern, sorted by modification time.
    
    Args:
        pattern: File pattern to match
        directory: Directory to search in
        
    Returns:
        List of file paths sorted by modification time (newest first)
    """
    files = glob.glob(os.path.join(directory, pattern))
    files.sort(key=os.path.getmtime, reverse=True)
    return files


def find_correlation_file(result_file: str, directory: str = "output") -> Optional[str]:
    """
    Find the correlation matrix file corresponding to a result file.
    
    Args:
        result_file: Path to result file
        directory: Directory to search in
        
    Returns:
        Path to correlation file or None
    """
    match = re.search(r'_result_(\d{8}_\d{6})\.csv', result_file)
    if not match:
        return None
    
    timestamp = match.group(1)
    base_name = os.path.basename(result_file)
    
    # Determine prefix
    if "portfolio_jp" in base_name:
        prefix = "portfolio_jp"
    else:
        prefix = "portfolio"
    
    corr_file = os.path.join(directory, f"{prefix}_corr_{timestamp}.csv")
    
    if os.path.exists(corr_file):
        return corr_file
    
    return None


def get_portfolio_files() -> Tuple[List[str], List[str]]:
    """
    Get US and JP portfolio result files.
    
    Returns:
        Tuple of (us_files, jp_files) sorted by modification time
    """
    us_files = get_result_files("portfolio_result_*.csv")
    jp_files = get_result_files("portfolio_jp_result_*.csv")
    return us_files, jp_files


def ensure_directory(directory: str) -> None:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        directory: Directory path
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
