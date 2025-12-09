"""
Configuration Module

Central configuration management for the application.
"""

import os
from typing import Any, Dict


class Config:
    """Application configuration settings."""
    
    # Directory paths
    DATA_DIR = "data"
    OUTPUT_DIR = "output"
    CACHE_DIR = "data"
    
    # Cache settings (in hours)
    CACHE_TTL_METADATA = 24 * 7  # 1 week for sector, industry, country, name
    CACHE_TTL_VOLATILITY = 24  # 1 day for volatility/sharpe calculations
    CACHE_TTL_PRICE = 0.25  # 15 minutes for price data
    
    # Cache file
    CACHE_FILE = "ticker_cache.json"
    
    # Default values
    DEFAULT_USD_JPY_RATE = 100.0
    DEFAULT_RISK_FREE_RATE = 4.0  # 4%
    
    # API settings
    YAHOO_FINANCE_TIMEOUT = 5
    
    # Portfolio calculation settings
    TRADING_DAYS_PER_YEAR = 252
    
    # Efficient frontier settings
    EFFICIENT_FRONTIER_POINTS = 50
    RANDOM_PORTFOLIOS_COUNT = 500
    MAX_ANNUAL_MULTIPLIER = 11.0  # Cap for annualized returns (1000%)
    
    # UI settings
    DEFAULT_PAGE_TITLE = "Sena Investment"
    DEFAULT_LAYOUT = "wide"
    MOBILE_TICK_ANGLE = -45
    
    # Alert thresholds
    DEFAULT_ALERT_THRESHOLD = 5  # 5% change
    
    # File patterns
    US_PORTFOLIO_FILE = "portfolio.csv"
    JP_PORTFOLIO_FILE = "portfolio_jp.csv"
    US_RESULT_PATTERN = "portfolio_result_*.csv"
    JP_RESULT_PATTERN = "portfolio_jp_result_*.csv"
    CORR_PATTERN = "*_corr_*.csv"
    
    @classmethod
    def get_cache_path(cls) -> str:
        """Get full path to cache file."""
        return os.path.join(cls.CACHE_DIR, cls.CACHE_FILE)
    
    @classmethod
    def ensure_directories(cls) -> None:
        """Ensure required directories exist."""
        for directory in [cls.DATA_DIR, cls.OUTPUT_DIR, cls.CACHE_DIR]:
            if not os.path.exists(directory):
                os.makedirs(directory)
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            key: value
            for key, value in vars(cls).items()
            if not key.startswith('_') and not callable(value)
        }


# Convenience singleton instance for default configuration
# For testing or custom configurations, instantiate Config() directly
config = Config()
