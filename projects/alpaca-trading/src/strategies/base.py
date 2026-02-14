"""Base strategy interface."""
from abc import ABC, abstractmethod
from typing import Optional

import pandas as pd

from ..models import TradeSignal


class Strategy(ABC):
    """Abstract base class for trading strategies."""
    
    name: str = "base"
    enabled: bool = True
    
    def __init__(self, params: dict | None = None):
        self.params = params or {}
    
    @abstractmethod
    def analyze(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """
        Analyze price data and generate a trade signal if conditions are met.
        
        Args:
            symbol: Stock symbol
            bars: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        
        Returns:
            TradeSignal if conditions are met, None otherwise
        """
        pass
    
    @abstractmethod
    def get_watchlist(self) -> list[str]:
        """Return list of symbols this strategy monitors."""
        pass
    
    def should_exit(self, symbol: str, bars: pd.DataFrame, position_side: str) -> bool:
        """
        Check if an existing position should be exited.
        
        Args:
            symbol: Stock symbol
            bars: DataFrame with OHLCV data
            position_side: "long" or "short"
        
        Returns:
            True if position should be closed
        """
        return False
