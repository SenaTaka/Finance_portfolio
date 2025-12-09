"""Migration script to move JSON cache to database."""

import json
import os
from datetime import datetime
from .models import init_db, get_session, TickerCache


def migrate_json_cache_to_db(json_cache_file: str = "data/ticker_cache.json"):
    """Migrate existing JSON cache to database.
    
    Args:
        json_cache_file: Path to existing JSON cache file
    """
    # Initialize database
    init_db()
    session = get_session()
    
    # Load JSON cache
    if not os.path.exists(json_cache_file):
        print(f"No JSON cache file found at {json_cache_file}")
        return
    
    print(f"Loading JSON cache from {json_cache_file}...")
    with open(json_cache_file, 'r', encoding='utf-8') as f:
        json_cache = json.load(f)
    
    print(f"Found {len(json_cache)} tickers in JSON cache")
    
    # Migrate each ticker
    migrated = 0
    for ticker, data in json_cache.items():
        try:
            # Check if ticker already exists
            cache_entry = session.query(TickerCache).filter_by(ticker=ticker).first()
            
            if cache_entry is None:
                cache_entry = TickerCache(ticker=ticker)
                session.add(cache_entry)
            
            # Migrate price data
            if 'price' in data:
                cache_entry.price = data['price']
            if 'price_updated' in data:
                cache_entry.price_updated = _parse_datetime(data['price_updated'])
            
            # Migrate metadata
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
                cache_entry.metadata_updated = _parse_datetime(data['metadata_updated'])
            
            # Migrate volatility data
            if 'sigma' in data:
                cache_entry.sigma = data['sigma']
            if 'sharpe' in data:
                cache_entry.sharpe = data['sharpe']
            if 'volatility_updated' in data:
                cache_entry.volatility_updated = _parse_datetime(data['volatility_updated'])
            
            # Migrate additional metrics
            if 'PER' in data:
                cache_entry.per = data['PER']
            if 'dividend_yield' in data:
                cache_entry.dividend_yield = data['dividend_yield']
            
            # Migrate historical data
            if 'history' in data:
                cache_entry.history = json.dumps(data['history'])
            if 'history_index' in data:
                cache_entry.history_index = json.dumps(data['history_index'])
            if 'history' in data or 'history_index' in data:
                cache_entry.history_updated = datetime.now()
            
            migrated += 1
            
            if migrated % 10 == 0:
                print(f"Migrated {migrated} tickers...")
                session.commit()
        
        except Exception as e:
            print(f"Error migrating ticker {ticker}: {e}")
            session.rollback()
    
    # Final commit
    try:
        session.commit()
        print(f"\nMigration complete! Successfully migrated {migrated} tickers to database.")
    except Exception as e:
        print(f"Error committing final changes: {e}")
        session.rollback()
    finally:
        session.close()
    
    # Optionally backup the JSON file
    backup_file = json_cache_file + ".backup"
    if os.path.exists(json_cache_file):
        import shutil
        shutil.copy2(json_cache_file, backup_file)
        print(f"JSON cache backed up to {backup_file}")


def _parse_datetime(dt_str):
    """Parse datetime string to datetime object."""
    if not dt_str:
        return None
    try:
        if isinstance(dt_str, datetime):
            return dt_str
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    migrate_json_cache_to_db()
