"""Real-time updates component for portfolio."""

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
from typing import Dict, List


class RealtimeUpdates:
    """Component for displaying real-time price updates."""
    
    @staticmethod
    def render(df: pd.DataFrame, update_interval: int = 60):
        """Render real-time updates component.
        
        Args:
            df: Portfolio DataFrame
            update_interval: Update interval in seconds (default: 60)
        """
        st.subheader("⚡ Real-time Price Updates")
        
        # Info message
        st.info(f"Prices are refreshed automatically every {update_interval} seconds.")
        
        # Create columns for controls
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        with col2:
            if st.button("🔄 Refresh Now", key="manual_refresh"):
                st.rerun()
        
        # Get latest prices
        tickers = df['ticker'].unique().tolist()
        
        try:
            # Fetch current prices
            price_updates = RealtimeUpdates._fetch_realtime_prices(tickers)
            
            if price_updates:
                # Calculate changes
                updates_df = RealtimeUpdates._calculate_changes(df, price_updates)
                
                # Display updates in a nice format
                RealtimeUpdates._display_price_updates(updates_df)
            else:
                st.warning("Could not fetch real-time price updates.")
        
        except Exception as e:
            st.error(f"Error fetching real-time prices: {str(e)}")
    
    @staticmethod
    def _fetch_realtime_prices(tickers: List[str]) -> Dict[str, Dict]:
        """Fetch real-time prices for tickers.
        
        Args:
            tickers: List of ticker symbols
            
        Returns:
            Dictionary mapping ticker to price data
        """
        price_updates = {}
        
        for ticker in tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                
                # Get current price (try multiple fields)
                current_price = (
                    info.get('currentPrice') or
                    info.get('regularMarketPrice') or
                    info.get('previousClose')
                )
                
                if current_price:
                    price_updates[ticker] = {
                        'current_price': current_price,
                        'previous_close': info.get('previousClose', current_price),
                        'day_high': info.get('dayHigh'),
                        'day_low': info.get('dayLow'),
                        'volume': info.get('volume', 0),
                    }
            
            except Exception as e:
                # Skip ticker if error
                continue
        
        return price_updates
    
    @staticmethod
    def _calculate_changes(df: pd.DataFrame, price_updates: Dict[str, Dict]) -> pd.DataFrame:
        """Calculate price changes.
        
        Args:
            df: Portfolio DataFrame
            price_updates: Real-time price data
            
        Returns:
            DataFrame with price changes
        """
        updates = []
        
        for ticker in df['ticker'].unique():
            if ticker not in price_updates:
                continue
            
            # Get ticker data from portfolio
            ticker_data = df[df['ticker'] == ticker].iloc[0]
            old_price = ticker_data.get('price', 0)
            
            # Get new price
            new_price = price_updates[ticker]['current_price']
            previous_close = price_updates[ticker]['previous_close']
            
            # Calculate changes
            price_change = new_price - old_price
            price_change_pct = (price_change / old_price * 100) if old_price > 0 else 0
            
            day_change = new_price - previous_close
            day_change_pct = (day_change / previous_close * 100) if previous_close > 0 else 0
            
            updates.append({
                'ticker': ticker,
                'name': ticker_data.get('name', ticker),
                'old_price': old_price,
                'new_price': new_price,
                'price_change': price_change,
                'price_change_pct': price_change_pct,
                'day_change': day_change,
                'day_change_pct': day_change_pct,
                'day_high': price_updates[ticker].get('day_high', 0),
                'day_low': price_updates[ticker].get('day_low', 0),
                'volume': price_updates[ticker].get('volume', 0),
            })
        
        return pd.DataFrame(updates)
    
    @staticmethod
    def _display_price_updates(updates_df: pd.DataFrame):
        """Display price updates in a nice format.
        
        Args:
            updates_df: DataFrame with price updates
        """
        if updates_df.empty:
            st.warning("No price updates available.")
            return
        
        # Sort by absolute day change
        updates_df = updates_df.sort_values('day_change_pct', ascending=False, key=abs)
        
        # Display as cards
        for _, row in updates_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    st.markdown(f"**{row['ticker']}**")
                    st.caption(row['name'])
                
                with col2:
                    st.metric(
                        "Current Price",
                        f"${row['new_price']:.2f}",
                        delta=f"{row['day_change']:.2f} ({row['day_change_pct']:.2f}%)",
                        delta_color="normal"
                    )
                
                with col3:
                    st.caption("Day High/Low")
                    st.text(f"${row['day_high']:.2f} / ${row['day_low']:.2f}")
                
                with col4:
                    # Format volume
                    volume = row['volume']
                    if volume >= 1e9:
                        volume_str = f"{volume/1e9:.2f}B"
                    elif volume >= 1e6:
                        volume_str = f"{volume/1e6:.2f}M"
                    elif volume >= 1e3:
                        volume_str = f"{volume/1e3:.2f}K"
                    else:
                        volume_str = f"{volume:.0f}"
                    
                    st.caption("Volume")
                    st.text(volume_str)
                
                st.divider()
        
        # Summary
        st.subheader("📊 Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            gainers = len(updates_df[updates_df['day_change_pct'] > 0])
            st.metric("Gainers", f"{gainers}/{len(updates_df)}")
        
        with col2:
            avg_change = updates_df['day_change_pct'].mean()
            st.metric("Avg Change", f"{avg_change:.2f}%")
        
        with col3:
            top_performer = updates_df.iloc[0]
            st.metric(
                "Top Performer",
                top_performer['ticker'],
                delta=f"{top_performer['day_change_pct']:.2f}%"
            )
