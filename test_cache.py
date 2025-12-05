"""Tests for the caching functionality in portfolio_calculator."""
import os
import json
import tempfile
from datetime import datetime, timedelta
import unittest

# Test the cache functions directly
from portfolio_calculator import (
    load_cache,
    save_cache,
    is_cache_valid,
    CACHE_TTL_METADATA,
    CACHE_TTL_VOLATILITY,
    CACHE_TTL_PRICE,
    CACHE_DIR,
    CACHE_FILE,
)


class TestCacheFunctions(unittest.TestCase):
    """Test cache utility functions."""

    def test_is_cache_valid_with_valid_time(self):
        """Test that recent cache is considered valid."""
        recent_time = datetime.now().isoformat()
        self.assertTrue(is_cache_valid(recent_time, 1.0))

    def test_is_cache_valid_with_expired_time(self):
        """Test that old cache is considered invalid."""
        old_time = (datetime.now() - timedelta(hours=2)).isoformat()
        self.assertFalse(is_cache_valid(old_time, 1.0))

    def test_is_cache_valid_with_none(self):
        """Test that None cache time is invalid."""
        self.assertFalse(is_cache_valid(None, 1.0))

    def test_is_cache_valid_with_invalid_string(self):
        """Test that invalid time string is handled."""
        self.assertFalse(is_cache_valid("invalid-time", 1.0))

    def test_ttl_values(self):
        """Test that TTL values are correctly set."""
        self.assertEqual(CACHE_TTL_METADATA, 24 * 7)  # 1 week
        self.assertEqual(CACHE_TTL_VOLATILITY, 24)  # 1 day
        self.assertEqual(CACHE_TTL_PRICE, 0.25)  # 15 minutes


class TestCachePersistence(unittest.TestCase):
    """Test cache load/save functions."""

    def setUp(self):
        """Set up test with temporary directory."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cache_dir = CACHE_DIR
        self.original_cache_file = CACHE_FILE

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_load_empty_cache(self):
        """Test loading cache when file doesn't exist."""
        import portfolio_calculator
        original_file = portfolio_calculator.CACHE_FILE
        portfolio_calculator.CACHE_FILE = os.path.join(self.temp_dir, "nonexistent.json")
        
        cache = load_cache()
        self.assertEqual(cache, {})
        
        portfolio_calculator.CACHE_FILE = original_file

    def test_save_and_load_cache(self):
        """Test saving and loading cache data."""
        import portfolio_calculator
        original_file = portfolio_calculator.CACHE_FILE
        original_dir = portfolio_calculator.CACHE_DIR
        
        portfolio_calculator.CACHE_DIR = self.temp_dir
        portfolio_calculator.CACHE_FILE = os.path.join(self.temp_dir, "test_cache.json")
        
        test_data = {
            "AAPL": {
                "price": 150.0,
                "name": "Apple Inc.",
                "price_updated": datetime.now().isoformat()
            }
        }
        
        save_cache(test_data)
        loaded = load_cache()
        
        self.assertEqual(loaded["AAPL"]["price"], 150.0)
        self.assertEqual(loaded["AAPL"]["name"], "Apple Inc.")
        
        portfolio_calculator.CACHE_FILE = original_file
        portfolio_calculator.CACHE_DIR = original_dir


if __name__ == "__main__":
    unittest.main()
