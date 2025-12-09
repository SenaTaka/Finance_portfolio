#!/usr/bin/env python
"""Real-time price streaming server."""

import argparse
import logging
from src.realtime.price_updater import run_price_streaming
from src.database import PortfolioManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Real-time Price Streaming Server')
    parser.add_argument('--host', default='localhost', help='Server host')
    parser.add_argument('--port', type=int, default=8765, help='Server port')
    parser.add_argument('--interval', type=int, default=60,
                       help='Update interval in seconds (default: 60)')
    parser.add_argument('--portfolio-id', type=int,
                       help='Portfolio ID to stream (streams all holdings)')
    parser.add_argument('--tickers', nargs='+',
                       help='Specific tickers to stream (space-separated)')
    
    args = parser.parse_args()
    
    # Determine which tickers to stream
    tickers = []
    
    if args.portfolio_id:
        # Get tickers from portfolio
        logger.info(f"Loading tickers from portfolio {args.portfolio_id}")
        mgr = PortfolioManager()
        holdings = mgr.get_holdings(args.portfolio_id)
        mgr.close()
        
        if holdings.empty:
            logger.error(f"No holdings found in portfolio {args.portfolio_id}")
            return 1
        
        tickers = holdings['ticker'].tolist()
        logger.info(f"Streaming {len(tickers)} tickers from portfolio")
    
    elif args.tickers:
        tickers = args.tickers
        logger.info(f"Streaming {len(tickers)} specified tickers")
    
    else:
        logger.error("Must specify either --portfolio-id or --tickers")
        return 1
    
    # Start server
    logger.info(f"Starting WebSocket server on ws://{args.host}:{args.port}")
    logger.info(f"Update interval: {args.interval} seconds")
    logger.info(f"Tickers: {', '.join(tickers)}")
    
    try:
        run_price_streaming(tickers, args.host, args.port, args.interval)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"Server error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
