"""Database models for portfolio management system."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean,
    ForeignKey, create_engine, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
import os

Base = declarative_base()

# Database configuration
DB_DIR = "data"
DB_FILE = os.path.join(DB_DIR, "portfolio.db")
DB_URL = f"sqlite:///{DB_FILE}"


class TickerCache(Base):
    """Cache for ticker data to reduce API calls."""
    __tablename__ = 'ticker_cache'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    
    # Price data
    price = Column(Float)
    price_updated = Column(DateTime)
    
    # Metadata (name, sector, etc.)
    name = Column(String(200))
    sector = Column(String(100))
    industry = Column(String(100))
    country = Column(String(100))
    currency = Column(String(10))
    metadata_updated = Column(DateTime)
    
    # Volatility and Sharpe ratio
    sigma = Column(Float)  # Annualized volatility (%)
    sharpe = Column(Float)  # Sharpe ratio
    volatility_updated = Column(DateTime)
    
    # Additional metrics
    per = Column(Float)  # Price to Earnings Ratio
    dividend_yield = Column(Float)
    
    # Historical price data (stored as JSON string)
    history = Column(Text)  # JSON array of prices
    history_index = Column(Text)  # JSON array of dates
    history_updated = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def __repr__(self):
        return f"<TickerCache(ticker='{self.ticker}', price={self.price})>"


class Portfolio(Base):
    """Portfolio entity for managing multiple portfolios."""
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    history = relationship("PortfolioHistory", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(id={self.id}, name='{self.name}')>"


class PortfolioHolding(Base):
    """Current holdings in a portfolio."""
    __tablename__ = 'portfolio_holdings'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    ticker = Column(String(20), nullable=False)
    shares = Column(Float, nullable=False)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    
    # Index for faster lookups
    __table_args__ = (
        Index('idx_portfolio_ticker', 'portfolio_id', 'ticker'),
    )
    
    def __repr__(self):
        return f"<PortfolioHolding(portfolio_id={self.portfolio_id}, ticker='{self.ticker}', shares={self.shares})>"


class PortfolioHistory(Base):
    """Historical snapshots of portfolio values."""
    __tablename__ = 'portfolio_history'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    
    # Portfolio metrics at snapshot time
    total_value_usd = Column(Float)
    total_value_jpy = Column(Float)
    usd_jpy_rate = Column(Float)
    
    # Detailed snapshot data (stored as JSON string)
    holdings_snapshot = Column(Text)  # JSON representation of holdings at this time
    
    snapshot_date = Column(DateTime, default=datetime.now, index=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="history")
    
    # Index for faster time-series queries
    __table_args__ = (
        Index('idx_portfolio_date', 'portfolio_id', 'snapshot_date'),
    )
    
    def __repr__(self):
        return f"<PortfolioHistory(portfolio_id={self.portfolio_id}, value_jpy={self.total_value_jpy}, date={self.snapshot_date})>"


# Database session management
_engine = None
_SessionLocal = None


def init_db():
    """Initialize the database."""
    global _engine, _SessionLocal
    
    # Create data directory if it doesn't exist
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
    
    # Create engine
    _engine = create_engine(DB_URL, echo=False)
    
    # Create all tables
    Base.metadata.create_all(_engine)
    
    # Create session factory
    _SessionLocal = sessionmaker(bind=_engine)
    
    print(f"Database initialized at: {DB_FILE}")
    return _engine


def get_session():
    """Get a new database session."""
    global _SessionLocal
    
    if _SessionLocal is None:
        init_db()
    
    return _SessionLocal()


def get_engine():
    """Get the database engine."""
    global _engine
    
    if _engine is None:
        init_db()
    
    return _engine
