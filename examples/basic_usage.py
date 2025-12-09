"""
Basic Usage Examples for the Modular Architecture

This script demonstrates how to use the new modular components.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core import PortfolioCalculator
from src.data import CacheManager, StockDataFetcher
from src.utils import Config, RegionClassifier, file_utils


def example_2_cache_management():
    """Example 2: Working with cache"""
    print("\n" + "=" * 60)
    print("Example 2: Cache Management")
    print("=" * 60)
    
    # Initialize cache manager
    cache = CacheManager()
    
    # Check cache status
    if cache.needs_price_update("AAPL"):
        print("✓ AAPL price needs update")
    else:
        print("✓ AAPL price is cached")
    
    # Get cached data
    aapl_data = cache.get("AAPL")
    if aapl_data:
        print(f"✓ Cached data for AAPL: {aapl_data.get('name', 'N/A')}")


def example_3_data_fetching():
    """Example 3: Fetching stock data"""
    print("\n" + "=" * 60)
    print("Example 3: Data Fetching")
    print("=" * 60)
    
    # Create data fetcher
    fetcher = StockDataFetcher()
    
    # Get risk-free rate
    rf_rate = fetcher.get_risk_free_rate()
    print(f"✓ Risk-free rate: {rf_rate:.2f}%")
    
    # Get exchange rate
    usd_jpy = fetcher.get_exchange_rate()
    print(f"✓ USD/JPY rate: {usd_jpy:.2f}")


def example_4_region_classification():
    """Example 4: Region classification"""
    print("\n" + "=" * 60)
    print("Example 4: Region Classification")
    print("=" * 60)
    
    # Classify countries
    countries = ["Japan", "United States", "Germany", "Brazil"]
    
    for country in countries:
        region = RegionClassifier.classify(country)
        print(f"✓ {country:20} -> {region}")
    
    # Get all regions
    regions = RegionClassifier.get_all_regions()
    print(f"\n✓ Available regions: {', '.join(regions)}")


def example_5_file_utilities():
    """Example 5: File utilities"""
    print("\n" + "=" * 60)
    print("Example 5: File Utilities")
    print("=" * 60)
    
    # Get latest result files
    us_files, jp_files = file_utils.get_portfolio_files()
    
    print(f"✓ US result files: {len(us_files)}")
    print(f"✓ JP result files: {len(jp_files)}")
    
    # Get latest US file
    if us_files:
        latest = us_files[0]
        timestamp = file_utils.extract_timestamp_from_filename(latest)
        print(f"✓ Latest US file: {os.path.basename(latest)}")
        print(f"✓ Timestamp: {timestamp}")


def example_6_configuration():
    """Example 6: Configuration access"""
    print("\n" + "=" * 60)
    print("Example 6: Configuration")
    print("=" * 60)
    
    # Access configuration
    print(f"✓ Data directory: {Config.DATA_DIR}")
    print(f"✓ Output directory: {Config.OUTPUT_DIR}")
    print(f"✓ Cache TTL (price): {Config.CACHE_TTL_PRICE} hours")
    print(f"✓ Trading days/year: {Config.TRADING_DAYS_PER_YEAR}")
    print(f"✓ Default risk-free rate: {Config.DEFAULT_RISK_FREE_RATE}%")
    
    # Ensure directories exist
    Config.ensure_directories()
    print("✓ Required directories checked/created")


def main():
    """Run all examples"""
    print("\n" + "=" * 60)
    print("Finance Portfolio - Modular Architecture Examples")
    print("=" * 60)
    
    try:
        example_2_cache_management()
        example_3_data_fetching()
        example_4_region_classification()
        example_5_file_utilities()
        example_6_configuration()
        
        print("\n" + "=" * 60)
        print("✓ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
