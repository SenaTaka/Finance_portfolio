"""Tests for the caching functionality in portfolio_calculator."""
import os
import json
import tempfile
from datetime import datetime, timedelta
import unittest
from unittest import mock

# Test the cache functions directly
from portfolio_calculator import (
    load_cache,
    save_cache,
    is_cache_valid,
    CACHE_TTL_METADATA,
    CACHE_TTL_VOLATILITY,
    CACHE_TTL_PRICE,
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

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @mock.patch('portfolio_calculator.CACHE_FILE')
    def test_load_empty_cache(self, mock_cache_file):
        """Test loading cache when file doesn't exist."""
        mock_cache_file.__str__ = lambda x: os.path.join(self.temp_dir, "nonexistent.json")
        # Re-import to get fresh function with patched value
        import portfolio_calculator
        with mock.patch.object(portfolio_calculator, 'CACHE_FILE', 
                               os.path.join(self.temp_dir, "nonexistent.json")):
            cache = portfolio_calculator.load_cache()
            self.assertEqual(cache, {})

    @mock.patch('portfolio_calculator.CACHE_DIR')
    @mock.patch('portfolio_calculator.CACHE_FILE')
    def test_save_and_load_cache(self, mock_cache_file, mock_cache_dir):
        """Test saving and loading cache data."""
        import portfolio_calculator
        
        cache_file = os.path.join(self.temp_dir, "test_cache.json")
        
        with mock.patch.object(portfolio_calculator, 'CACHE_DIR', self.temp_dir):
            with mock.patch.object(portfolio_calculator, 'CACHE_FILE', cache_file):
                test_data = {
                    "AAPL": {
                        "price": 150.0,
                        "name": "Apple Inc.",
                        "price_updated": datetime.now().isoformat()
                    }
                }
                
                portfolio_calculator.save_cache(test_data)
                loaded = portfolio_calculator.load_cache()
                
                self.assertEqual(loaded["AAPL"]["price"], 150.0)
                self.assertEqual(loaded["AAPL"]["name"], "Apple Inc.")


if __name__ == "__main__":
    unittest.main()
