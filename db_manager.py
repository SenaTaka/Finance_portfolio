#!/usr/bin/env python
"""Database management CLI tool."""

import argparse
import sys
from src.database import (
    init_db, get_session,
    PortfolioManager, DatabaseCacheManager,
    TickerCache, Portfolio
)
from src.database.migrate_json_to_db import migrate_json_cache_to_db


def cmd_init(args):
    """Initialize the database."""
    init_db()
    print("✓ Database initialized successfully")


def cmd_migrate(args):
    """Migrate JSON cache to database."""
    migrate_json_cache_to_db(args.json_file)


def cmd_list_portfolios(args):
    """List all portfolios."""
    mgr = PortfolioManager()
    portfolios = mgr.list_portfolios(active_only=not args.all)
    
    if not portfolios:
        print("No portfolios found")
        return
    
    print(f"\n{'ID':<5} {'Name':<30} {'Active':<8} {'Holdings':<10} {'History':<10}")
    print("-" * 75)
    
    for p in portfolios:
        holdings = mgr.get_holdings(p.id)
        history = mgr.get_history(p.id, days=365)
        active = "✓" if p.is_active else "✗"
        print(f"{p.id:<5} {p.name:<30} {active:<8} {len(holdings):<10} {len(history):<10}")
    
    mgr.close()


def cmd_show_portfolio(args):
    """Show details of a portfolio."""
    mgr = PortfolioManager()
    portfolio = mgr.get_portfolio(args.id)
    
    if portfolio is None:
        print(f"Portfolio {args.id} not found")
        mgr.close()
        return
    
    print(f"\nPortfolio: {portfolio.name}")
    print(f"Description: {portfolio.description}")
    print(f"Active: {'Yes' if portfolio.is_active else 'No'}")
    print(f"Created: {portfolio.created_at}")
    print(f"Updated: {portfolio.updated_at}")
    
    # Show holdings
    holdings = mgr.get_holdings(portfolio.id)
    if not holdings.empty:
        print(f"\nHoldings ({len(holdings)}):")
        print(holdings.to_string(index=False))
    else:
        print("\nNo holdings")
    
    # Show recent history
    history = mgr.get_history(portfolio.id, days=30)
    if not history.empty:
        print(f"\nRecent History (last {len(history)} snapshots):")
        print(history[['snapshot_date', 'total_value_jpy']].tail().to_string(index=False))
    else:
        print("\nNo history")
    
    mgr.close()


def cmd_create_portfolio(args):
    """Create a new portfolio."""
    mgr = PortfolioManager()
    portfolio = mgr.create_portfolio(args.name, args.description or "")
    print(f"✓ Created portfolio '{portfolio.name}' (ID: {portfolio.id})")
    mgr.close()


def cmd_import_portfolio(args):
    """Import portfolio from CSV."""
    mgr = PortfolioManager()
    portfolio = mgr.import_from_csv(args.csv_file, args.name)
    holdings = mgr.get_holdings(portfolio.id)
    print(f"✓ Imported portfolio '{portfolio.name}' (ID: {portfolio.id})")
    print(f"  Holdings: {len(holdings)}")
    mgr.close()


def cmd_delete_portfolio(args):
    """Delete a portfolio."""
    mgr = PortfolioManager()
    
    if not args.force:
        confirm = input(f"Delete portfolio {args.id}? This cannot be undone. (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            mgr.close()
            return
    
    if mgr.delete_portfolio(args.id):
        print(f"✓ Deleted portfolio {args.id}")
    else:
        print(f"Portfolio {args.id} not found")
    
    mgr.close()


def cmd_cache_stats(args):
    """Show cache statistics."""
    session = get_session()
    
    total = session.query(TickerCache).count()
    with_price = session.query(TickerCache).filter(TickerCache.price.isnot(None)).count()
    with_volatility = session.query(TickerCache).filter(TickerCache.sigma.isnot(None)).count()
    with_history = session.query(TickerCache).filter(TickerCache.history.isnot(None)).count()
    
    print(f"\nCache Statistics:")
    print(f"  Total tickers: {total}")
    print(f"  With price: {with_price}")
    print(f"  With volatility: {with_volatility}")
    print(f"  With history: {with_history}")
    
    if args.list:
        print(f"\nCached Tickers:")
        tickers = session.query(TickerCache).order_by(TickerCache.ticker).all()
        for t in tickers:
            print(f"  {t.ticker:<10} {t.name or 'N/A':<40} Price: ${t.price or 0:.2f}")
    
    session.close()


def cmd_clear_cache(args):
    """Clear cache data."""
    if not args.force:
        confirm = input("Clear all cache data? This cannot be undone. (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
    
    session = get_session()
    deleted = session.query(TickerCache).delete()
    session.commit()
    session.close()
    
    print(f"✓ Cleared {deleted} cache entries")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='Portfolio Database Manager')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # init command
    init_parser = subparsers.add_parser('init', help='Initialize database')
    init_parser.set_defaults(func=cmd_init)
    
    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate JSON cache to database')
    migrate_parser.add_argument('--json-file', default='data/ticker_cache.json',
                               help='Path to JSON cache file')
    migrate_parser.set_defaults(func=cmd_migrate)
    
    # list command
    list_parser = subparsers.add_parser('list', help='List portfolios')
    list_parser.add_argument('--all', action='store_true',
                            help='Include inactive portfolios')
    list_parser.set_defaults(func=cmd_list_portfolios)
    
    # show command
    show_parser = subparsers.add_parser('show', help='Show portfolio details')
    show_parser.add_argument('id', type=int, help='Portfolio ID')
    show_parser.set_defaults(func=cmd_show_portfolio)
    
    # create command
    create_parser = subparsers.add_parser('create', help='Create new portfolio')
    create_parser.add_argument('name', help='Portfolio name')
    create_parser.add_argument('--description', help='Portfolio description')
    create_parser.set_defaults(func=cmd_create_portfolio)
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import portfolio from CSV')
    import_parser.add_argument('csv_file', help='CSV file path')
    import_parser.add_argument('--name', help='Portfolio name (defaults to filename)')
    import_parser.set_defaults(func=cmd_import_portfolio)
    
    # delete command
    delete_parser = subparsers.add_parser('delete', help='Delete portfolio')
    delete_parser.add_argument('id', type=int, help='Portfolio ID')
    delete_parser.add_argument('--force', action='store_true',
                              help='Skip confirmation')
    delete_parser.set_defaults(func=cmd_delete_portfolio)
    
    # cache command
    cache_parser = subparsers.add_parser('cache', help='Show cache statistics')
    cache_parser.add_argument('--list', action='store_true',
                             help='List all cached tickers')
    cache_parser.set_defaults(func=cmd_cache_stats)
    
    # clear-cache command
    clear_parser = subparsers.add_parser('clear-cache', help='Clear all cache data')
    clear_parser.add_argument('--force', action='store_true',
                             help='Skip confirmation')
    clear_parser.set_defaults(func=cmd_clear_cache)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        args.func(args)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
