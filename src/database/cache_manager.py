"""Database cache manager to replace JSON file cache."""

from datetime import datetime, timedelta
from typing import Dict, Optional, Any
import json
from .models import TickerCache, get_session


class DatabaseCacheManager:
    """Manages ticker cache using database instead of JSON files."""
    
    # Cache TTL settings (in hours)
    CACHE_TTL_METADATA = 24 * 7  # 1 week for sector, industry, country, name
    CACHE_TTL_VOLATILITY = 24  # 1 day for volatility/sharpe calculations
    CACHE_TTL_PRICE = 0.25  # 15 minutes for price data
    
    def __init__(self):
        """Initialize the cache manager."""
        self.session = get_session()
    
    def get_ticker(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with cached data or None if not found
        """
        cache_entry = self.session.query(TickerCache).filter_by(ticker=ticker).first()
        
        if cache_entry is None:
            return None
        
        # Convert to dictionary format compatible with old JSON cache
        result = {
            'price': cache_entry.price,
            'price_updated': cache_entry.price_updated.isoformat() if cache_entry.price_updated else None,
            'name': cache_entry.name,
            'sector': cache_entry.sector,
            'industry': cache_entry.industry,
            'country': cache_entry.country,
            'currency': cache_entry.currency,
            'metadata_updated': cache_entry.metadata_updated.isoformat() if cache_entry.metadata_updated else None,
            'sigma': cache_entry.sigma,
            'sharpe': cache_entry.sharpe,
            'volatility_updated': cache_entry.volatility_updated.isoformat() if cache_entry.volatility_updated else None,
            'PER': cache_entry.per,
            'dividend_yield': cache_entry.dividend_yield,
        }
        
        # Add historical data if available
        if cache_entry.history:
            try:
                result['history'] = json.loads(cache_entry.history)
                result['history_index'] = json.loads(cache_entry.history_index)
            except json.JSONDecodeError:
                pass
        
        return result
    
    def set_ticker(self, ticker: str, data: Dict[str, Any]):
        """Set or update cached data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            data: Dictionary with ticker data to cache
        """
        cache_entry = self.session.query(TickerCache).filter_by(ticker=ticker).first()
        
        if cache_entry is None:
            cache_entry = TickerCache(ticker=ticker)
            self.session.add(cache_entry)
        
        # Update price data
        if 'price' in data:
            cache_entry.price = data['price']
        if 'price_updated' in data:
            cache_entry.price_updated = self._parse_datetime(data['price_updated'])
        
        # Update metadata
        if 'name' in data:
            cache_entry.name = data['name']
        if 'sector' in data:
            cache_entry.sector = data['sector']
        if 'industry' in data:
            cache_entry.industry = data['industry']
        if 'country' in data:
            cache_entry.country = data['country']
        if 'currency' in data:
            cache_entry.currency = data['currency']
        if 'metadata_updated' in data:
            cache_entry.metadata_updated = self._parse_datetime(data['metadata_updated'])
        
        # Update volatility data
        if 'sigma' in data:
            cache_entry.sigma = data['sigma']
        if 'sharpe' in data:
            cache_entry.sharpe = data['sharpe']
        if 'volatility_updated' in data:
            cache_entry.volatility_updated = self._parse_datetime(data['volatility_updated'])
        
        # Update additional metrics
        if 'PER' in data:
            cache_entry.per = data['PER']
        if 'dividend_yield' in data:
            cache_entry.dividend_yield = data['dividend_yield']
        
        # Update historical data
        if 'history' in data:
            cache_entry.history = json.dumps(data['history'])
        if 'history_index' in data:
            cache_entry.history_index = json.dumps(data['history_index'])
        if 'history' in data or 'history_index' in data:
            cache_entry.history_updated = datetime.now()
        
        cache_entry.updated_at = datetime.now()
        
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e
    
    def is_cache_valid(self, cached_time_str: Optional[str], ttl_hours: float) -> bool:
        """Check if cached data is still valid based on TTL.
        
        Args:
            cached_time_str: ISO format timestamp string
            ttl_hours: Time to live in hours
            
        Returns:
            True if cache is still valid, False otherwise
        """
        if not cached_time_str:
            return False
        try:
            cached_time = datetime.fromisoformat(cached_time_str)
            return datetime.now() - cached_time < timedelta(hours=ttl_hours)
        except (ValueError, TypeError):
            return False
    
    def get_all_tickers(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached tickers.
        
        Returns:
            Dictionary mapping ticker symbols to their cached data
        """
        result = {}
        cache_entries = self.session.query(TickerCache).all()
        
        for entry in cache_entries:
            result[entry.ticker] = self.get_ticker(entry.ticker)
        
        return result
    
    def clear_expired(self):
        """Remove expired cache entries."""
        now = datetime.now()
        
        # Clear old price data
        price_cutoff = now - timedelta(hours=self.CACHE_TTL_PRICE * 10)  # Keep 10x TTL
        self.session.query(TickerCache).filter(
            TickerCache.price_updated < price_cutoff
        ).update({'price': None, 'price_updated': None})
        
        self.session.commit()
    
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string to datetime object.
        
        Args:
            dt_str: ISO format datetime string
            
        Returns:
            datetime object or None if parsing fails
        """
        if not dt_str:
            return None
        try:
            if isinstance(dt_str, datetime):
                return dt_str
            return datetime.fromisoformat(dt_str)
        except (ValueError, TypeError):
            return None
    
    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
