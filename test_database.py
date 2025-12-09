"""Tests for database components."""

import unittest
import os
import tempfile
import shutil
from datetime import datetime
import pandas as pd

from src.database import (
    init_db, get_session,
    TickerCache, Portfolio, PortfolioHolding, PortfolioHistory,
    DatabaseCacheManager, PortfolioManager
)
from src.database.models import DB_DIR, DB_FILE


class TestDatabaseModels(unittest.TestCase):
    """Test database models and basic operations."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        # Use a temporary directory for tests
        cls.temp_dir = tempfile.mkdtemp()
        
        # Override DB paths
        import src.database.models as models
        models.DB_DIR = cls.temp_dir
        models.DB_FILE = os.path.join(cls.temp_dir, "test_portfolio.db")
        models.DB_URL = f"sqlite:///{models.DB_FILE}"
        
        # Initialize database
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_database_initialization(self):
        """Test that database is initialized correctly."""
        session = get_session()
        self.assertIsNotNone(session)
        session.close()
    
    def test_ticker_cache_creation(self):
        """Test creating ticker cache entries."""
        session = get_session()
        
        ticker = TickerCache(
            ticker="AAPL",
            price=150.0,
            name="Apple Inc.",
            sector="Technology",
            currency="USD"
        )
        session.add(ticker)
        session.commit()
        
        # Retrieve and verify
        retrieved = session.query(TickerCache).filter_by(ticker="AAPL").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.price, 150.0)
        self.assertEqual(retrieved.name, "Apple Inc.")
        
        session.close()
    
    def test_portfolio_creation(self):
        """Test creating portfolios."""
        session = get_session()
        
        portfolio = Portfolio(
            name="Test Portfolio",
            description="A test portfolio"
        )
        session.add(portfolio)
        session.commit()
        
        # Retrieve and verify
        retrieved = session.query(Portfolio).filter_by(name="Test Portfolio").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.description, "A test portfolio")
        
        session.close()


class TestDatabaseCacheManager(unittest.TestCase):
    """Test DatabaseCacheManager functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.temp_dir = tempfile.mkdtemp()
        
        import src.database.models as models
        models.DB_DIR = cls.temp_dir
        models.DB_FILE = os.path.join(cls.temp_dir, "test_cache.db")
        models.DB_URL = f"sqlite:///{models.DB_FILE}"
        
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_cache_get_set(self):
        """Test getting and setting cache data."""
        cache_mgr = DatabaseCacheManager()
        
        # Set data
        data = {
            'price': 175.0,
            'price_updated': datetime.now().isoformat(),
            'name': 'Microsoft Corporation',
            'sector': 'Technology',
            'sigma': 25.5,
            'sharpe': 1.2
        }
        cache_mgr.set_ticker('MSFT', data)
        
        # Get data
        retrieved = cache_mgr.get_ticker('MSFT')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['price'], 175.0)
        self.assertEqual(retrieved['name'], 'Microsoft Corporation')
        self.assertEqual(retrieved['sigma'], 25.5)
        
        cache_mgr.close()
    
    def test_cache_validity(self):
        """Test cache validity checking."""
        cache_mgr = DatabaseCacheManager()
        
        # Recent time should be valid
        recent_time = datetime.now().isoformat()
        self.assertTrue(cache_mgr.is_cache_valid(recent_time, 1.0))
        
        # Old time should be invalid
        old_time = (datetime.now() - pd.Timedelta(hours=2)).isoformat()
        self.assertFalse(cache_mgr.is_cache_valid(old_time, 1.0))
        
        # None should be invalid
        self.assertFalse(cache_mgr.is_cache_valid(None, 1.0))
        
        cache_mgr.close()


class TestPortfolioManager(unittest.TestCase):
    """Test PortfolioManager functionality."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database."""
        cls.temp_dir = tempfile.mkdtemp()
        
        import src.database.models as models
        models.DB_DIR = cls.temp_dir
        models.DB_FILE = os.path.join(cls.temp_dir, "test_portfolio_mgr.db")
        models.DB_URL = f"sqlite:///{models.DB_FILE}"
        
        init_db()
    
    @classmethod
    def tearDownClass(cls):
        """Clean up test database."""
        if os.path.exists(cls.temp_dir):
            shutil.rmtree(cls.temp_dir)
    
    def test_create_portfolio(self):
        """Test creating a portfolio."""
        mgr = PortfolioManager()
        
        portfolio = mgr.create_portfolio("Test Portfolio 1", "Description 1")
        self.assertIsNotNone(portfolio)
        self.assertEqual(portfolio.name, "Test Portfolio 1")
        self.assertTrue(portfolio.is_active)
        
        mgr.close()
    
    def test_list_portfolios(self):
        """Test listing portfolios."""
        mgr = PortfolioManager()
        
        # Create a few portfolios
        mgr.create_portfolio("Portfolio A")
        mgr.create_portfolio("Portfolio B")
        
        portfolios = mgr.list_portfolios()
        self.assertGreaterEqual(len(portfolios), 2)
        
        mgr.close()
    
    def test_set_get_holdings(self):
        """Test setting and getting portfolio holdings."""
        mgr = PortfolioManager()
        
        portfolio = mgr.create_portfolio("Holdings Test")
        
        holdings = [
            {'ticker': 'AAPL', 'shares': 10},
            {'ticker': 'GOOGL', 'shares': 5}
        ]
        mgr.set_holdings(portfolio.id, holdings)
        
        # Get holdings
        holdings_df = mgr.get_holdings(portfolio.id)
        self.assertEqual(len(holdings_df), 2)
        self.assertIn('AAPL', holdings_df['ticker'].values)
        
        mgr.close()
    
    def test_add_history_snapshot(self):
        """Test adding history snapshots."""
        mgr = PortfolioManager()
        
        portfolio = mgr.create_portfolio("History Test")
        
        mgr.add_history_snapshot(
            portfolio.id,
            total_value_usd=10000.0,
            total_value_jpy=1500000.0,
            usd_jpy_rate=150.0,
            holdings_snapshot={'test': 'data'}
        )
        
        # Get history
        history_df = mgr.get_history(portfolio.id, days=30)
        self.assertEqual(len(history_df), 1)
        self.assertEqual(history_df.iloc[0]['total_value_usd'], 10000.0)
        
        mgr.close()


if __name__ == "__main__":
    unittest.main()
