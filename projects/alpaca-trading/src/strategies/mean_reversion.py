"""Mean reversion strategy using RSI."""
from typing import Optional

import pandas as pd
import ta

from ..models import TradeSignal
from .base import Strategy


class MeanReversionStrategy(Strategy):
    """
    Mean reversion strategy based on RSI oversold conditions.
    
    Generates buy signals when:
    - RSI drops below oversold threshold
    - Price is near recent support levels
    """
    
    name = "mean_reversion"
    
    def __init__(self, params: dict | None = None, watchlist: list[str] | None = None):
        super().__init__(params)
        self.watchlist = watchlist or ["SPY", "QQQ"]
        
        # Default parameters
        self.rsi_oversold = self.params.get("rsi_oversold", 30)
        self.rsi_overbought = self.params.get("rsi_overbought", 70)
        self.lookback_period = self.params.get("lookback_period", 14)
        self.min_price = self.params.get("min_price", 10)
    
    def get_watchlist(self) -> list[str]:
        return self.watchlist
    
    def analyze(self, symbol: str, bars: pd.DataFrame) -> Optional[TradeSignal]:
        """Analyze bars for mean reversion signal."""
        if bars.empty or len(bars) < self.lookback_period + 5:
            return None
        
        # Calculate RSI
        rsi = ta.momentum.RSIIndicator(
            bars["close"], 
            window=self.lookback_period
        ).rsi()
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2]
        current_price = bars["close"].iloc[-1]
        
        # Check price minimum
        if current_price < self.min_price:
            return None
        
        # Buy signal: RSI crosses above oversold from below
        if prev_rsi < self.rsi_oversold and current_rsi >= self.rsi_oversold:
            confidence = self._calculate_confidence(current_rsi, bars)
            
            return TradeSignal(
                symbol=symbol,
                side="buy",
                strategy_name=self.name,
                confidence=confidence,
                entry_price=current_price
            )
        
        return None
    
    def _calculate_confidence(self, rsi: float, bars: pd.DataFrame) -> float:
        """Calculate signal confidence."""
        # Lower RSI = more oversold = higher confidence
        rsi_score = max(0.3, (40 - rsi) / 40)  # Higher when RSI was very low
        
        # Check if price is near support (recent low)
        recent_low = bars["low"].tail(20).min()
        current_price = bars["close"].iloc[-1]
        price_to_support = (current_price - recent_low) / recent_low
        
        # Closer to support = higher confidence
        support_score = max(0, 0.4 - price_to_support * 2)
        
        return min(rsi_score + support_score, 1.0)
    
    def should_exit(self, symbol: str, bars: pd.DataFrame, position_side: str) -> bool:
        """Check if we should exit - when RSI becomes overbought."""
        if bars.empty or len(bars) < self.lookback_period:
            return False
        
        rsi = ta.momentum.RSIIndicator(
            bars["close"], 
            window=self.lookback_period
        ).rsi().iloc[-1]
        
        # Exit when overbought
        if position_side == "long" and rsi > self.rsi_overbought:
            return True
        
        return False


if __name__ == "__main__":
    # Quick test
    import numpy as np
    
    np.random.seed(42)
    n = 50
    
    # Create declining price data to trigger oversold
    prices = 100 - np.arange(n) * 0.5 + np.random.randn(n) * 0.5
    
    bars = pd.DataFrame({
        "open": prices + 0.5,
        "high": prices + 1,
        "low": prices - 1,
        "close": prices,
        "volume": np.random.randint(1000000, 5000000, n)
    })
    
    strategy = MeanReversionStrategy()
    print(f"Watchlist: {strategy.get_watchlist()}")
    
    signal = strategy.analyze("TEST", bars)
    if signal:
        print(f"Signal: {signal}")
    else:
        print("No signal generated (normal - needs specific RSI conditions)")
