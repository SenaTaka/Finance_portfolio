"""Real-time price updater that fetches and broadcasts prices."""

import asyncio
from datetime import datetime
from typing import List, Dict, Any
import yfinance as yf
import logging

logger = logging.getLogger(__name__)


class RealTimePriceUpdater:
    """Fetch real-time prices and update via WebSocket."""
    
    def __init__(self, websocket_server, update_interval: int = 60):
        """Initialize the updater.
        
        Args:
            websocket_server: PriceStreamServer instance
            update_interval: Update interval in seconds (default: 60)
        """
        self.server = websocket_server
        self.update_interval = update_interval
        self.running = False
    
    async def fetch_price(self, ticker: str) -> Dict[str, Any]:
        """Fetch current price for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with price data
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try to get real-time price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice')
            
            if current_price is None:
                # Fallback to recent history
                hist = stock.history(period='1d')
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
            
            if current_price is None:
                return None
            
            return {
                'price': float(current_price),
                'change': float(info.get('regularMarketChange', 0)),
                'change_percent': float(info.get('regularMarketChangePercent', 0)),
                'volume': int(info.get('regularMarketVolume', 0)),
                'high': float(info.get('dayHigh', current_price)),
                'low': float(info.get('dayLow', current_price)),
                'open': float(info.get('open', current_price)),
            }
        except Exception as e:
            logger.error(f"Error fetching price for {ticker}: {e}")
            return None
    
    async def update_prices(self, tickers: List[str]):
        """Fetch and broadcast prices for multiple tickers.
        
        Args:
            tickers: List of ticker symbols
        """
        for ticker in tickers:
            price_data = await self.fetch_price(ticker)
            if price_data:
                await self.server.broadcast_price_update(ticker, price_data)
    
    async def run_updates(self, tickers: List[str]):
        """Run continuous price updates.
        
        Args:
            tickers: List of ticker symbols to monitor
        """
        self.running = True
        logger.info(f"Starting price updates for {len(tickers)} tickers")
        
        while self.running:
            try:
                await self.update_prices(tickers)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in update loop: {e}")
                await asyncio.sleep(5)  # Short delay before retry
    
    def stop(self):
        """Stop the updater."""
        self.running = False
        logger.info("Price updater stopped")


async def start_price_streaming(tickers: List[str], host: str = "localhost",
                               port: int = 8765, update_interval: int = 60):
    """Start WebSocket server and price streaming.
    
    Args:
        tickers: List of ticker symbols to stream
        host: Server host
        port: Server port
        update_interval: Update interval in seconds
    """
    from .websocket_server import PriceStreamServer
    
    server = PriceStreamServer(host, port)
    updater = RealTimePriceUpdater(server, update_interval)
    
    # Run both server and updater
    await asyncio.gather(
        server.start(),
        updater.run_updates(tickers)
    )


def run_price_streaming(tickers: List[str], host: str = "localhost",
                       port: int = 8765, update_interval: int = 60):
    """Run price streaming (blocking call).
    
    Args:
        tickers: List of ticker symbols to stream
        host: Server host
        port: Server port
        update_interval: Update interval in seconds
    """
    asyncio.run(start_price_streaming(tickers, host, port, update_interval))
