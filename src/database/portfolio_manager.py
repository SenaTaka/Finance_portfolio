"""Portfolio manager for handling multiple portfolios."""

from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd
import json
from .models import Portfolio, PortfolioHolding, PortfolioHistory, get_session


class PortfolioManager:
    """Manages multiple portfolios and their holdings."""
    
    def __init__(self):
        """Initialize the portfolio manager."""
        self.session = get_session()
    
    def create_portfolio(self, name: str, description: str = "") -> Portfolio:
        """Create a new portfolio.
        
        Args:
            name: Portfolio name
            description: Optional description
            
        Returns:
            Created Portfolio object
        """
        portfolio = Portfolio(
            name=name,
            description=description,
            is_active=True
        )
        self.session.add(portfolio)
        self.session.commit()
        print(f"Created portfolio: {name} (ID: {portfolio.id})")
        return portfolio
    
    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get a portfolio by ID.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            Portfolio object or None if not found
        """
        return self.session.query(Portfolio).filter_by(id=portfolio_id).first()
    
    def get_portfolio_by_name(self, name: str) -> Optional[Portfolio]:
        """Get a portfolio by name.
        
        Args:
            name: Portfolio name
            
        Returns:
            Portfolio object or None if not found
        """
        return self.session.query(Portfolio).filter_by(name=name).first()
    
    def list_portfolios(self, active_only: bool = True) -> List[Portfolio]:
        """List all portfolios.
        
        Args:
            active_only: If True, only return active portfolios
            
        Returns:
            List of Portfolio objects
        """
        query = self.session.query(Portfolio)
        if active_only:
            query = query.filter_by(is_active=True)
        return query.order_by(Portfolio.name).all()
    
    def update_portfolio(self, portfolio_id: int, name: str = None, 
                        description: str = None, is_active: bool = None) -> Optional[Portfolio]:
        """Update portfolio details.
        
        Args:
            portfolio_id: Portfolio ID
            name: New name (optional)
            description: New description (optional)
            is_active: Active status (optional)
            
        Returns:
            Updated Portfolio object or None if not found
        """
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio is None:
            return None
        
        if name is not None:
            portfolio.name = name
        if description is not None:
            portfolio.description = description
        if is_active is not None:
            portfolio.is_active = is_active
        
        portfolio.updated_at = datetime.now()
        self.session.commit()
        return portfolio
    
    def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            True if deleted, False if not found
        """
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio is None:
            return False
        
        self.session.delete(portfolio)
        self.session.commit()
        print(f"Deleted portfolio: {portfolio.name}")
        return True
    
    def set_holdings(self, portfolio_id: int, holdings: List[Dict[str, Any]]):
        """Set holdings for a portfolio (replaces existing holdings).
        
        Args:
            portfolio_id: Portfolio ID
            holdings: List of dicts with 'ticker' and 'shares' keys
        """
        portfolio = self.get_portfolio(portfolio_id)
        if portfolio is None:
            raise ValueError(f"Portfolio {portfolio_id} not found")
        
        # Clear existing holdings
        self.session.query(PortfolioHolding).filter_by(portfolio_id=portfolio_id).delete()
        
        # Add new holdings
        for holding in holdings:
            if holding.get('shares', 0) > 0:
                ph = PortfolioHolding(
                    portfolio_id=portfolio_id,
                    ticker=holding['ticker'],
                    shares=holding['shares']
                )
                self.session.add(ph)
        
        self.session.commit()
        print(f"Updated holdings for portfolio {portfolio.name}: {len(holdings)} holdings")
    
    def get_holdings(self, portfolio_id: int) -> pd.DataFrame:
        """Get current holdings for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            
        Returns:
            DataFrame with ticker and shares columns
        """
        holdings = self.session.query(PortfolioHolding).filter_by(portfolio_id=portfolio_id).all()
        
        if not holdings:
            return pd.DataFrame(columns=['ticker', 'shares'])
        
        data = [{'ticker': h.ticker, 'shares': h.shares} for h in holdings]
        return pd.DataFrame(data)
    
    def add_history_snapshot(self, portfolio_id: int, total_value_usd: float,
                           total_value_jpy: float, usd_jpy_rate: float,
                           holdings_snapshot: Dict[str, Any]):
        """Add a historical snapshot of portfolio value.
        
        Args:
            portfolio_id: Portfolio ID
            total_value_usd: Total portfolio value in USD
            total_value_jpy: Total portfolio value in JPY
            usd_jpy_rate: USD/JPY exchange rate
            holdings_snapshot: Detailed holdings data as dict
        """
        history = PortfolioHistory(
            portfolio_id=portfolio_id,
            total_value_usd=total_value_usd,
            total_value_jpy=total_value_jpy,
            usd_jpy_rate=usd_jpy_rate,
            holdings_snapshot=json.dumps(holdings_snapshot),
            snapshot_date=datetime.now()
        )
        self.session.add(history)
        self.session.commit()
    
    def get_history(self, portfolio_id: int, days: int = 30) -> pd.DataFrame:
        """Get historical snapshots for a portfolio.
        
        Args:
            portfolio_id: Portfolio ID
            days: Number of days of history to retrieve
            
        Returns:
            DataFrame with historical data
        """
        cutoff = datetime.now() - pd.Timedelta(days=days)
        
        history = self.session.query(PortfolioHistory).filter(
            PortfolioHistory.portfolio_id == portfolio_id,
            PortfolioHistory.snapshot_date >= cutoff
        ).order_by(PortfolioHistory.snapshot_date).all()
        
        if not history:
            return pd.DataFrame(columns=['snapshot_date', 'total_value_usd', 'total_value_jpy', 'usd_jpy_rate'])
        
        data = [{
            'snapshot_date': h.snapshot_date,
            'total_value_usd': h.total_value_usd,
            'total_value_jpy': h.total_value_jpy,
            'usd_jpy_rate': h.usd_jpy_rate
        } for h in history]
        
        return pd.DataFrame(data)
    
    def import_from_csv(self, csv_file: str, portfolio_name: str = None) -> Portfolio:
        """Import portfolio from CSV file.
        
        Args:
            csv_file: Path to CSV file with ticker and shares columns
            portfolio_name: Name for the portfolio (defaults to filename)
            
        Returns:
            Created Portfolio object
        """
        import os
        
        if portfolio_name is None:
            portfolio_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        # Check if portfolio exists
        portfolio = self.get_portfolio_by_name(portfolio_name)
        if portfolio is None:
            portfolio = self.create_portfolio(portfolio_name, f"Imported from {csv_file}")
        
        # Load CSV
        df = pd.read_csv(csv_file)
        if 'ticker' not in df.columns or 'shares' not in df.columns:
            raise ValueError("CSV must have 'ticker' and 'shares' columns")
        
        # Convert to holdings list
        holdings = df[['ticker', 'shares']].to_dict('records')
        self.set_holdings(portfolio.id, holdings)
        
        return portfolio
    
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
