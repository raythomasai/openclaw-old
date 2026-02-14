"""
Market Scanner
Scans for trading opportunities based on momentum signals
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import yaml
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """Result from a market scan"""
    symbol: str
    signal_type: str  # 'long' | 'short' | 'neutral'
    confidence: float  # 0.0 - 1.0
    price: float
    change_pct: float
    volume: int
    volume_ratio: float
    rsi: float
    vwap: float
    gap_pct: float
    reason: str
    timestamp: datetime = field(default_factory=datetime.now)


class SignalStrategy(ABC):
    """Base class for signal strategies"""
    
    @abstractmethod
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        pass


class GapUpStrategy(SignalStrategy):
    """Gap up breakout signal"""
    
    def __init__(self, config: dict):
        self.min_gap = config.get('gap_up_threshold', 0.02)
        self.min_volume_ratio = config.get('volume_multiplier', 1.5)
        self.min_confidence = config.get('min_confidence', 0.65)
        
    def get_name(self) -> str:
        return "Gap Up Breakout"
    
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        if not quote or quote.get('change_pct', 0) < self.min_gap:
            return None
            
        if quote.get('volume_ratio', 0) < self.min_volume_ratio:
            return None
            
        # Check for continuation (still trading above open)
        if quote.get('price', 0) <= quote.get('open', 0):
            return None
            
        confidence = min(0.95, 0.7 + (quote['change_pct'] - self.min_gap) * 5)
        
        return ScanResult(
            symbol=quote['symbol'],
            signal_type='long',
            confidence=confidence,
            price=quote['price'],
            change_pct=quote.get('change_pct', 0),
            volume=quote.get('volume', 0),
            volume_ratio=quote.get('volume_ratio', 0),
            rsi=quote.get('rsi', 50),
            vwap=quote.get('vwap', 0),
            gap_pct=quote.get('gap_pct', 0),
            reason=f"Gap up {quote.get('change_pct', 0)*100:.1f}% with {quote.get('volume_ratio', 0)}x volume"
        )


class GapDownStrategy(SignalStrategy):
    """Gap down breakdown signal"""
    
    def __init__(self, config: dict):
        self.min_gap = abs(config.get('gap_down_threshold', -0.02))
        self.min_volume_ratio = config.get('volume_multiplier', 1.5)
        
    def get_name(self) -> str:
        return "Gap Down Breakdown"
    
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        if not quote or quote.get('change_pct', 0) > -self.min_gap:
            return None
            
        if quote.get('volume_ratio', 0) < self.min_volume_ratio:
            return None
            
        if quote.get('price', 0) >= quote.get('open', 0):
            return None
            
        confidence = min(0.95, 0.7 + (abs(quote['change_pct']) - self.min_gap) * 5)
        
        return ScanResult(
            symbol=quote['symbol'],
            signal_type='short',
            confidence=confidence,
            price=quote['price'],
            change_pct=quote.get('change_pct', 0),
            volume=quote.get('volume', 0),
            volume_ratio=quote.get('volume_ratio', 0),
            rsi=quote.get('rsi', 50),
            vwap=quote.get('vwap', 0),
            gap_pct=quote.get('gap_pct', 0),
            reason=f"Gap down {quote.get('change_pct', 0)*100:.1f}% with {quote.get('volume_ratio', 0)}x volume"
        )


class RSIBounceStrategy(SignalStrategy):
    """RSI oversold bounce signal"""
    
    def __init__(self, config: dict):
        self.oversold = 40
        self.min_confidence = config.get('min_confidence', 0.65)
        
    def get_name(self) -> str:
        return "RSI Oversold Bounce"
    
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        rsi = quote.get('rsi', 50)
        
        if rsi > self.oversold:
            return None
            
        # Need some bounce
        if quote.get('change_pct', 0) < -0.01:
            return None
            
        # Price above VWAP or日内低点
        if quote.get('price', 0) < quote.get('vwap', 0):
            return None
            
        confidence = 0.65 + (40 - rsi) * 0.02
        
        return ScanResult(
            symbol=quote['symbol'],
            signal_type='long',
            confidence=min(0.90, confidence),
            price=quote['price'],
            change_pct=quote.get('change_pct', 0),
            volume=quote.get('volume', 0),
            volume_ratio=quote.get('volume_ratio', 0),
            rsi=rsi,
            vwap=quote.get('vwap', 0),
            gap_pct=quote.get('gap_pct', 0),
            reason=f"RSI {rsi:.0f} oversold bounce"
        )


class RSIReversalStrategy(SignalStrategy):
    """RSI overbought reversal signal"""
    
    def __init__(self, config: dict):
        self.overbought = 60
        
    def get_name(self) -> str:
        return "RSI Overbought Reversal"
    
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        rsi = quote.get('rsi', 50)
        
        if rsi < self.overbought:
            return None
            
        if quote.get('change_pct', 0) > 0.01:
            return None
            
        if quote.get('price', 0) > quote.get('vwap', 0):
            return None
            
        confidence = 0.65 + (rsi - 60) * 0.02
        
        return ScanResult(
            symbol=quote['symbol'],
            signal_type='short',
            confidence=min(0.90, confidence),
            price=quote['price'],
            change_pct=quote.get('change_pct', 0),
            volume=quote.get('volume', 0),
            volume_ratio=quote.get('volume_ratio', 0),
            rsi=rsi,
            vwap=quote.get('vwap', 0),
            gap_pct=quote.get('gap_pct', 0),
            reason=f"RSI {rsi:.0f} overbought reversal"
        )


class VWAPBreakoutStrategy(SignalStrategy):
    """VWAP breakout signal"""
    
    def __init__(self, config: dict):
        self.min_confidence = config.get('min_confidence', 0.65)
        
    def get_name(self) -> str:
        return "VWAP Breakout"
    
    def evaluate(self, quote: Dict, history: pd.DataFrame) -> Optional[ScanResult]:
        price = quote.get('price', 0)
        vwap = quote.get('vwap', 0)
        
        if price <= vwap:
            return None
            
        # Check if breaking out with volume
        if quote.get('volume_ratio', 0) < 1.2:
            return None
            
        # Strong move above VWAP
        if (price - vwap) / vwap < 0.01:
            return None
            
        confidence = 0.70 + ((price - vwap) / vwap) * 10
        
        return ScanResult(
            symbol=quote['symbol'],
            signal_type='long',
            confidence=min(0.90, confidence),
            price=price,
            change_pct=quote.get('change_pct', 0),
            volume=quote.get('volume', 0),
            volume_ratio=quote.get('volume_ratio', 0),
            rsi=quote.get('rsi', 50),
            vwap=vwap,
            gap_pct=quote.get('gap_pct', 0),
            reason=f"Broke above VWAP by {((price - vwap) / vwap) * 100:.1f}%"
        )


class MarketScanner:
    """Main market scanner class"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.watchlist = self._load_watchlist()
        self.strategies = self._init_strategies()
        self.last_scan_time = None
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _load_watchlist(self) -> List[str]:
        """Load watchlist from file"""
        watchlist_path = self.config.get('strategy', {}).get(
            'watchlist_path', 'data/watchlist.txt'
        )
        
        try:
            with open(watchlist_path, 'r') as f:
                symbols = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        parts = line.split('|')
                        symbols.append(parts[0].strip())
                return symbols
        except FileNotFoundError:
            # Fall back to config
            return self.config.get('watchlist', {}).get('default', ['SPY', 'QQQ'])
    
    def _init_strategies(self) -> List[SignalStrategy]:
        """Initialize signal strategies"""
        strategy_config = self.config.get('strategy', {})
        
        return [
            GapUpStrategy(strategy_config),
            GapDownStrategy(strategy_config),
            RSIBounceStrategy(strategy_config),
            RSIReversalStrategy(strategy_config),
            VWAPBreakoutStrategy(strategy_config),
        ]
    
    def get_watchlist(self) -> List[str]:
        """Get current watchlist"""
        return self.watchlist
    
    async def scan_symbol(self, symbol: str, quote: Dict) -> List[ScanResult]:
        """Scan a single symbol for signals"""
        results = []
        
        for strategy in self.strategies:
            try:
                result = strategy.evaluate(quote, pd.DataFrame())
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(f"Error evaluating {strategy.get_name()} for {symbol}: {e}")
        
        return results
    
    async def scan_all(self, quotes: Dict[str, Dict]) -> List[ScanResult]:
        """Scan all symbols in watchlist"""
        all_results = []
        
        for symbol, quote in quotes.items():
            if quote is None:
                continue
                
            results = await self.scan_symbol(symbol, quote)
            all_results.extend(results)
        
        # Sort by confidence
        all_results.sort(key=lambda x: x.confidence, reverse=True)
        
        self.last_scan_time = datetime.now()
        
        return all_results
    
    def get_top_signals(self, results: List[ScanResult], 
                       direction: Optional[str] = None,
                       max_results: int = 5) -> List[ScanResult]:
        """Get top signals, optionally filtered by direction"""
        filtered = results
        
        if direction:
            filtered = [r for r in filtered if r.signal_type == direction]
        
        return filtered[:max_results]


# Utility functions for calculating indicators
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Calculate RSI from price series"""
    if len(prices) < period + 1:
        return 50.0
    
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    if avg_loss == 0:
        return 100.0
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_vwap(prices: List[float], volumes: List[float]) -> float:
    """Calculate VWAP"""
    if len(prices) != len(volumes) or sum(volumes) == 0:
        return 0.0
    
    pv = [p * v for p, v in zip(prices, volumes)]
    return sum(pv) / sum(volumes)


def calculate_volume_ratio(volume: int, avg_volume: float) -> float:
    """Calculate current volume vs average"""
    if avg_volume == 0:
        return 0.0
    return volume / avg_volume


if __name__ == "__main__":
    # Test scanner
    scanner = MarketScanner()
    print(f"Watchlist: {scanner.get_watchlist()}")
    print(f"Strategies: {[s.get_name() for s in scanner.strategies]}")
