"""
Portfolio Calculator - Backward Compatible Entry Point

This module provides backward compatibility with the original portfolio_calculator.py
while using the new modular architecture.
"""

import argparse
import sys
import os

# Add src to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

from src.core.portfolio_calculator import PortfolioCalculator
from src.data.cache_manager import CacheManager


def load_cache():
    """Load cache from file - backward compatible function."""
    cache_manager = CacheManager()
    return cache_manager.cache


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Calculate portfolio valuations and metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python portfolio_calculator.py                    # Use portfolio.csv
  python portfolio_calculator.py portfolio_jp.csv  # Use Japan stocks portfolio
  python portfolio_calculator.py --force-refresh   # Ignore cache and full refresh
"""
    )
    parser.add_argument(
        "csv_file",
        nargs="?",
        default="portfolio.csv",
        help="Input CSV file (default: portfolio.csv)"
    )
    parser.add_argument(
        "-f", "--force-refresh",
        action="store_true",
        help="Ignore cache and fetch all data from API"
    )
    
    args = parser.parse_args()
    calculator = PortfolioCalculator(args.csv_file, force_refresh=args.force_refresh)
    calculator.run()
