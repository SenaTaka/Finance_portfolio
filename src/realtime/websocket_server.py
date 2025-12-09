"""WebSocket server for real-time price streaming."""

import asyncio
import json
from datetime import datetime
from typing import Set, Dict, Any
import logging

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False

logger = logging.getLogger(__name__)


class PriceStreamServer:
    """WebSocket server for streaming price updates."""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        """Initialize the server.
        
        Args:
            host: Host address
            port: Port number
        """
        if not WEBSOCKETS_AVAILABLE:
            raise ImportError("websockets library required. Install with: pip install websockets")
        
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.subscriptions: Dict[WebSocketServerProtocol, Set[str]] = {}
        self.running = False
    
    async def register(self, websocket: WebSocketServerProtocol):
        """Register a new client.
        
        Args:
            websocket: Client websocket connection
        """
        self.clients.add(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
    
    async def unregister(self, websocket: WebSocketServerProtocol):
        """Unregister a client.
        
        Args:
            websocket: Client websocket connection
        """
        self.clients.discard(websocket)
        self.subscriptions.pop(websocket, None)
        logger.info(f"Client disconnected. Total clients: {len(self.clients)}")
    
    async def handle_message(self, websocket: WebSocketServerProtocol, message: str):
        """Handle incoming messages from clients.
        
        Args:
            websocket: Client websocket connection
            message: Message from client (JSON string)
        """
        try:
            data = json.loads(message)
            action = data.get('action')
            
            if action == 'subscribe':
                tickers = data.get('tickers', [])
                self.subscriptions[websocket].update(tickers)
                await websocket.send(json.dumps({
                    'type': 'subscribed',
                    'tickers': list(self.subscriptions[websocket])
                }))
                logger.info(f"Client subscribed to: {tickers}")
            
            elif action == 'unsubscribe':
                tickers = data.get('tickers', [])
                self.subscriptions[websocket].difference_update(tickers)
                await websocket.send(json.dumps({
                    'type': 'unsubscribed',
                    'tickers': tickers
                }))
                logger.info(f"Client unsubscribed from: {tickers}")
            
            elif action == 'ping':
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message: {message}")
            await websocket.send(json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    async def handler(self, websocket: WebSocketServerProtocol, path: str):
        """Main handler for client connections.
        
        Args:
            websocket: Client websocket connection
            path: Connection path
        """
        await self.register(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister(websocket)
    
    async def broadcast_price_update(self, ticker: str, price_data: Dict[str, Any]):
        """Broadcast price update to subscribed clients.
        
        Args:
            ticker: Stock ticker symbol
            price_data: Price data dictionary
        """
        message = json.dumps({
            'type': 'price_update',
            'ticker': ticker,
            'data': price_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to clients subscribed to this ticker
        for websocket, tickers in self.subscriptions.items():
            if ticker in tickers:
                try:
                    await websocket.send(message)
                except websockets.exceptions.ConnectionClosed:
                    pass
    
    async def broadcast_portfolio_update(self, portfolio_data: Dict[str, Any]):
        """Broadcast portfolio-level update to all clients.
        
        Args:
            portfolio_data: Portfolio data dictionary
        """
        message = json.dumps({
            'type': 'portfolio_update',
            'data': portfolio_data,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all clients
        if self.clients:
            await asyncio.gather(
                *[client.send(message) for client in self.clients],
                return_exceptions=True
            )
    
    async def start(self):
        """Start the WebSocket server."""
        self.running = True
        logger.info(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        
        async with websockets.serve(self.handler, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    def run(self):
        """Run the server (blocking call)."""
        asyncio.run(self.start())
