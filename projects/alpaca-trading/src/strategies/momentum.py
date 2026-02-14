"""Momentum breakout strategy."""
from typing import Optional

import pandas as pd
import ta

from ..models import TradeSignal
from .base import Strategy


class MomentumStrategy(Strategy):
    """
    Momentum breakout strategy.
    
    Generates buy signals when:
    - Price breaks above VWAP
    - Volume is above average (configurable threshold)
    - Price is within configured range
    """
    
    name = "momentum_breakout"
    
    def __init__(self, params: dict | None = None, watchlist: list[str] | None = None):
        super().__init__(params)
        self.watchlist = watchlist or ["SPY", "QQQ", "AAPL", "MSFT", "NVDA"]
        
        # Default parameters
        self.vwap_buffer = self.params.get("vwap_buffer", 0.001)  # 0.1% above VWAP
        self.volume_threshold = self.params.get("volume_threshold", 1.5)  # 1.5x avg volume
        self.min_price = self.params.get("min_price", 10)
        self.max_price = self.params.get("max_price", 500)
        self.rsi_min = self.params.get("rsi_min", 50)  # Only buy when RSI > 50
    
    def get_watchlist(self) -> list[str]:
        return self.watchlist
    
    def analyze(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Analyze bars for momentum breakout signal."""
        if bars.empty or len(bars) < 20:
            return None
        
        # Ensure we have required columns
        required_cols = ["open", "high", "low", "close", "volume"]
        if not all(col in bars.columns for col in required_cols):
            return None
        
        # Calculate VWAP
        vwap = self._calculate_vwap(bars)
        
        # Calculate indicators
        current_price = bars["close"].iloc[-1]
        current_volume = bars["volume"].iloc[-1]
        avg_volume = bars["volume"].rolling(20).mean().iloc[-1]
        
        # RSI for momentum confirmation
        rsi = ta.momentum.RSIIndicator(bars["close"], window=14).rsi().iloc[-1]
        
        # Check price bounds
        if current_price < self.min_price or current_price > self.max_price:
            return None
        
        # Generate signal conditions
        price_above_vwap = current_price > vwap * (1 + self.vwap_buffer)
        volume_surge = current_volume > avg_volume * self.volume_threshold
        momentum_positive = rsi > self.rsi_min
        
        if price_above_vwap and volume_surge and momentum_positive:
            # Calculate confidence based on how strongly conditions are met
            confidence = self._calculate_confidence(
                current_price, vwap, current_volume, avg_volume, rsi
            )
            
            return TradeSignal(
                symbol=symbol,
                side="buy",
                strategy_name=self.name,
                confidence=confidence,
                entry_price=current_price
            )
        
        return None
    
    def _calculate_vwap(self, bars: pd.DataFrame) -> float:
        """Calculate VWAP from bar data."""
        typical_price = (bars["high"] + bars["low"] + bars["close"]) / 3
        vwap = (typical_price * bars["volume"]).cumsum() / bars["volume"].cumsum()
        return vwap.iloc[-1]
    
    def _calculate_confidence(
        self, 
        price: float, 
        vwap: float, 
        volume: float, 
        avg_volume: float,
        rsi: float
    ) -> float:
        """Calculate signal confidence score (0.0 - 1.0)."""
        # Price above VWAP component (max 0.3)
        price_score = min((price / vwap - 1) * 10, 0.3)
        
        # Volume component (max 0.4)
        volume_ratio = volume / avg_volume
        volume_score = min((volume_ratio - 1) * 0.2, 0.4)
        
        # RSI component (max 0.3)
        # Higher RSI = stronger momentum
        rsi_score = min((rsi - 50) / 50 * 0.3, 0.3)
        
        total = price_score + volume_score + rsi_score
        return min(max(total, 0.1), 1.0)  # Clamp between 0.1 and 1.0
    
    def should_exit(self, symbol: str, bars: pd.DataFrame, position_side: str) -> bool:
        """Check if we should exit a long position."""
        if bars.empty or len(bars) < 14:
            return False
        
        # Exit if price drops below VWAP
        vwap = self._calculate_vwap(bars)
        current_price = bars["close"].iloc[-1]
        
        if position_side == "long" and current_price < vwap * 0.995:
            return True
        
        # Exit if RSI shows overbought
        rsi = ta.momentum.RSIIndicator(bars["close"], window=14).rsi().iloc[-1]
        if rsi > 75:
            return True
        
        return False


if __name__ == "__main__":
    # Quick test with sample data
    import numpy as np
    
    # Create sample bars
    np.random.seed(42)
    n = 50
    bars = pd.DataFrame({
        "open": 100 + np.random.randn(n).cumsum() * 0.5,
        "high": 101 + np.random.randn(n).cumsum() * 0.5,
        "low": 99 + np.random.randn(n).cumsum() * 0.5,
        "close": 100 + np.random.randn(n).cumsum() * 0.5,
        "volume": np.random.randint(1000000, 5000000, n)
    })
    
    strategy = MomentumStrategy()
    print(f"Watchlist: {strategy.get_watchlist()}")
    
    signal = strategy.analyze("TEST", bars)
    if signal:
        print(f"Signal: {signal}")
    else:
        print("No signal generated")
