"""Alpaca API client wrapper with 1Password credential management."""
import subprocess
import json
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide, TimeInForce, QueryOrderStatus
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from .models import AccountInfo, Position


class AlpacaClient:
    """Wrapper around Alpaca SDK with credential management."""
    
    def __init__(self, paper: bool = False):
        self.api_key, self.api_secret = self._load_credentials()
        self.trading_client = TradingClient(
            self.api_key, 
            self.api_secret,
            paper=paper
        )
        self.data_client = StockHistoricalDataClient(self.api_key, self.api_secret)
    
    def _load_credentials(self) -> tuple[str, str]:
        """Load API credentials from environment or 1Password."""
        import os
        
        # First try environment variables
        api_key = os.environ.get("ALPACA_API_KEY")
        api_secret = os.environ.get("ALPACA_API_SECRET")
        
        if api_key and api_secret:
            return api_key, api_secret
        
        # Fall back to 1Password
        try:
            result = subprocess.run(
                ["op", "item", "get", "Alpaca", "--fields", "API Key,API Secret", "--reveal"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            parts = result.stdout.strip().split(",")
            if len(parts) != 2:
                raise ValueError(f"Expected 2 credentials, got {len(parts)}")
            return parts[0], parts[1]
        except subprocess.TimeoutExpired:
            raise RuntimeError("1Password CLI timed out - ensure the desktop app is unlocked")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to load credentials from 1Password: {e.stderr}")
    
    def get_account(self) -> AccountInfo:
        """Get current account information."""
        account = self.trading_client.get_account()
        return AccountInfo(
            portfolio_value=float(account.portfolio_value),
            cash=float(account.cash),
            buying_power=float(account.buying_power),
            equity=float(account.equity),
            daily_pnl=float(account.equity) - float(account.last_equity),
            daily_pnl_pct=((float(account.equity) - float(account.last_equity)) / float(account.last_equity)) * 100
        )
    
    def get_positions(self) -> list[Position]:
        """Get all current positions."""
        positions = self.trading_client.get_all_positions()
        return [
            Position(
                symbol=p.symbol,
                qty=float(p.qty),
                avg_entry_price=float(p.avg_entry_price),
                current_price=float(p.current_price),
                unrealized_pnl=float(p.unrealized_pl),
                unrealized_pnl_pct=float(p.unrealized_plpc) * 100
            )
            for p in positions
        ]
    
    def get_bars(self, symbol: str, timeframe: str = "1Min", limit: int = 100) -> pd.DataFrame:
        """Get historical bar data for a symbol."""
        tf_map = {
            "1Min": TimeFrame.Minute,
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "1Hour": TimeFrame.Hour,
            "1Day": TimeFrame.Day,
        }
        
        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf_map.get(timeframe, TimeFrame.Minute),
            start=datetime.now() - timedelta(days=5),
            limit=limit
        )
        
        bars = self.data_client.get_stock_bars(request)
        df = bars.df
        if isinstance(df.index, pd.MultiIndex):
            df = df.xs(symbol, level='symbol')
        return df.reset_index()
    
    def submit_market_order(
        self, 
        symbol: str, 
        qty: float, 
        side: str,
        time_in_force: str = "day"
    ) -> dict:
        """Submit a market order."""
        order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL
        tif = TimeInForce.DAY if time_in_force.lower() == "day" else TimeInForce.GTC
        
        order_request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=tif
        )
        
        order = self.trading_client.submit_order(order_request)
        return {
            "id": str(order.id),
            "symbol": order.symbol,
            "qty": float(order.qty),
            "side": order.side.value if hasattr(order.side, 'value') else order.side,
            "status": order.status.value if hasattr(order.status, 'value') else order.status,
            "submitted_at": str(order.submitted_at)
        }
    
    def close_position(self, symbol: str) -> dict:
        """Close a position by symbol."""
        order = self.trading_client.close_position(symbol)
        return {
            "id": str(order.id),
            "symbol": order.symbol,
            "side": order.side.value if hasattr(order.side, 'value') else order.side,
            "status": order.status.value if hasattr(order.status, 'value') else order.status
        }
    
    def close_all_positions(self) -> list[dict]:
        """Close all positions."""
        results = self.trading_client.close_all_positions()
        return [{"symbol": r.symbol, "status": "closed"} for r in results]
    
    def get_clock(self) -> dict:
        """Get market clock status."""
        clock = self.trading_client.get_clock()
        return {
            "is_open": clock.is_open,
            "next_open": str(clock.next_open),
            "next_close": str(clock.next_close)
        }
    
    def is_market_open(self) -> bool:
        """Check if market is currently open."""
        return self.trading_client.get_clock().is_open


if __name__ == "__main__":
    # Quick test
    client = AlpacaClient()
    print("Account:", client.get_account())
    print("Market open:", client.is_market_open())
    print("Positions:", len(client.get_positions()))
