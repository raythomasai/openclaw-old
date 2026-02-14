#!/usr/bin/env python3
"""
Signal Engine
Detects trading opportunities based on Polymarket signals
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of trading signals"""
    MOMENTUM = "momentum"
    WHALE_FOLLOW = "whale_follow"
    ARBITRAGE = "arbitrage"
    SENTIMENT = "sentiment"


@dataclass
class TradingSignal:
    """A trading signal"""
    signal_type: SignalType
    market_id: str
    side: str  # 'yes' or 'no'
    confidence: float  # 0-1
    expected_move: float  # Expected price move
    source: str  # Where signal came from
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class MarketPair:
    """Linked Polymarket and Kalshi market"""
    poly_market_id: str
    kalshi_market_id: str
    poly_yes: float
    poly_no: float
    kalshi_yes: float
    kalshi_no: float
    spread: float
    last_updated: datetime


class SignalEngine:
    """Engine for generating trading signals"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.momentum_threshold = config.get("momentum_threshold", 0.05)
        self.whale_min_amount = config.get("whale_min_amount", 1000)
        self.arb_threshold = config.get("arb_threshold", 0.03)
        
        # Track market pairs for correlation
        self.market_pairs: Dict[str, MarketPair] = {}
        
        # Historical data for momentum
        self.price_history: Dict[str, List[Dict]] = {}
    
    def update_market_pair(self, poly_market_id: str, kalshi_market_id: str,
                           poly_yes: float, poly_no: float,
                           kalshi_yes: float, kalshi_no: float) -> None:
        """Update tracked market pair"""
        pair = MarketPair(
            poly_market_id=poly_market_id,
            kalshi_market_id=kalshi_market_id,
            poly_yes=poly_yes,
            poly_no=poly_no,
            kalshi_yes=kalshi_yes,
            kalshi_no=kalshi_no,
            spread=kalshi_yes - poly_yes,
            last_updated=datetime.now()
        )
        self.market_pairs[f"{poly_market_id}_{kalshi_market_id}"] = pair
        
        # Track price history
        self._update_price_history(poly_market_id, poly_yes, poly_no)
        self._update_price_history(kalshi_market_id, kalshi_yes, kalshi_no)
    
    def detect_momentum_signal(self, poly_market_id: str) -> Optional[TradingSignal]:
        """Detect if Polymarket is moving before Kalshi"""
        if poly_market_id not in self.price_history:
            return None
        
        history = self.price_history[poly_market_id]
        if len(history) < 2:
            return None
        
        # Calculate short-term momentum
        recent = history[-1]
        previous = history[-5] if len(history) >= 5 else history[0]
        
        price_change = recent["yes_price"] - previous["yes_price"]
        momentum = price_change
        
        # Also check against Kalshi
        pair_key = f"{poly_market_id}_"
        if pair_key in self.market_pairs:
            pair = self.market_pairs[pair_key]
            spread = pair.kalshi_yes - pair.poly_yes
            
            # If Polymarket is significantly higher, Kalshi might catch up
            if momentum > self.momentum_threshold and spread > 0.02:
                return TradingSignal(
                    signal_type=SignalType.MOMENTUM,
                    market_id=pair.kalshi_market_id,
                    side="yes",
                    confidence=min(abs(momentum) * 5, 0.9),
                    expected_move=spread,
                    source="polymarket_momentum",
                    metadata={
                        "poly_price": pair.poly_yes,
                        "kalshi_price": pair.kalshi_yes,
                        "momentum": momentum
                    }
                )
            
            # Short if Polymarket drops significantly
            elif momentum < -self.momentum_threshold and spread < -0.02:
                return TradingSignal(
                    signal_type=SignalType.MOMENTUM,
                    market_id=pair.kalshi_market_id,
                    side="no",
                    confidence=min(abs(momentum) * 5, 0.9),
                    expected_move=abs(spread),
                    source="polymarket_momentum",
                    metadata={
                        "poly_price": pair.poly_yes,
                        "kalshi_price": pair.kalshi_yes,
                        "momentum": momentum
                    }
                )
        
        return None
    
    def detect_whale_signal(self, wallet_name: str, market_id: str,
                            side: str, amount: float) -> Optional[TradingSignal]:
        """Detect signal from whale activity"""
        if amount < self.whale_min_amount:
            return None
        
        # Only follow proven whales
        known_whales = ["ImJustKen", "SwissMiss", "fengdubiying"]
        if wallet_name not in known_whales:
            return None
        
        # Find corresponding Kalshi market
        pair_key = f"{market_id}_"
        pair = self.market_pairs.get(pair_key)
        
        if pair:
            return TradingSignal(
                signal_type=SignalType.WHALE_FOLLOW,
                market_id=pair.kalshi_market_id,
                side=side,
                confidence=0.7 if amount > 5000 else 0.5,
                expected_move=0.05,
                source=f"whale_{wallet_name}",
                metadata={
                    "wallet": wallet_name,
                    "amount": amount,
                    "poly_market": market_id
                }
            )
        
        return None
    
    def detect_arbitrage_opportunity(self, pair: MarketPair) -> Optional[TradingSignal]:
        """Detect mechanical arbitrage opportunity on Kalshi"""
        # For single-platform arb, we need YES + NO < 1
        # This requires holding both sides
        
        pair_cost = pair.kalshi_yes + pair.kalshi_no
        
        if pair_cost < (1.0 - self.arb_threshold):
            # Guaranteed profit if we buy both
            return TradingSignal(
                signal_type=SignalType.ARBITRAGE,
                market_id=pair.kalshi_market_id,
                side="both",
                confidence=0.95,
                expected_move=1.0 - pair_cost,
                source="mechanical_arb",
                metadata={
                    "yes_price": pair.kalshi_yes,
                    "no_price": pair.kalshi_no,
                    "pair_cost": pair_cost
                }
            )
        
        # Also check for cheap side
        if pair.kalshi_yes < 0.3 and pair.kalshi_yes < pair.kalshi_no - 0.1:
            return TradingSignal(
                signal_type=SignalType.ARBITRAGE,
                market_id=pair.kalshi_market_id,
                side="yes",
                confidence=0.6,
                expected_move=0.10,
                source="cheap_yes",
                metadata={
                    "yes_price": pair.kalshi_yes,
                    "no_price": pair.kalshi_no
                }
            )
        
        if pair.kalshi_no < 0.3 and pair.kalshi_no < pair.kalshi_yes - 0.1:
            return TradingSignal(
                signal_type=SignalType.ARBITRAGE,
                market_id=pair.kalshi_market_id,
                side="no",
                confidence=0.6,
                expected_move=0.10,
                source="cheap_no",
                metadata={
                    "yes_price": pair.kalshi_yes,
                    "no_price": pair.kalshi_no
                }
            )
        
        return None
    
    def detect_sentiment_signal(self, poly_market_id: str,
                                 poly_yes: float) -> Optional[TradingSignal]:
        """Detect sentiment-based signals"""
        # If Polymarket is very high (>0.9) or very low (<0.1)
        # Might be overbought/oversold
        
        if poly_yes > 0.92:
            # Possible pullback
            return TradingSignal(
                signal_type=SignalType.SENTIMENT,
                market_id="",
                side="no",
                confidence=0.4,
                expected_move=-0.05,
                source="overbought",
                metadata={"poly_yes": poly_yes}
            )
        
        elif poly_yes < 0.08:
            # Possible bounce
            return TradingSignal(
                signal_type=SignalType.SENTIMENT,
                market_id="",
                side="yes",
                confidence=0.4,
                expected_move=0.05,
                source="oversold",
                metadata={"poly_yes": poly_yes}
            )
        
        return None
    
    def analyze_all_pairs(self) -> List[TradingSignal]:
        """Analyze all tracked market pairs for signals"""
        signals = []
        
        for pair_key, pair in self.market_pairs.items():
            # Check mechanical arb
            arb_signal = self.detect_arbitrage_opportunity(pair)
            if arb_signal:
                signals.append(arb_signal)
            
            # Check momentum
            mom_signal = self.detect_momentum_signal(pair.poly_market_id)
            if mom_signal:
                signals.append(mom_signal)
            
            # Check sentiment
            sent_signal = self.detect_sentiment_signal(
                pair.poly_market_id, pair.poly_yes
            )
            if sent_signal and sent_signal.market_id:
                signals.append(sent_signal)
        
        return signals
    
    def _update_price_history(self, market_id: str, yes_price: float,
                               no_price: float) -> None:
        """Update price history for momentum calculation"""
        if market_id not in self.price_history:
            self.price_history[market_id] = []
        
        self.price_history[market_id].append({
            "yes_price": yes_price,
            "no_price": no_price,
            "timestamp": datetime.now()
        })
        
        # Keep only last 60 data points
        if len(self.price_history[market_id]) > 60:
            self.price_history[market_id] = self.price_history[market_id][-60:]
    
    def find_correlated_market(self, poly_market_id: str) -> Optional[str]:
        """Find Kalshi market ID that correlates to Polymarket market"""
        # In a real implementation, this would use:
        # - Market name matching
        # - Event slug matching
        # - Description matching
        
        # For now, return placeholder
        return None


class SignalAggregator:
    """Aggregates signals from multiple sources"""
    
    def __init__(self, engines: List[SignalEngine]):
        self.engines = engines
    
    def aggregate_signals(self, signals: List[TradingSignal]) -> List[TradingSignal]:
        """Aggregate and filter signals"""
        # Remove duplicates by market_id + side
        seen = set()
        unique_signals = []
        
        for signal in signals:
            key = f"{signal.market_id}_{signal.side}"
            if key not in seen:
                seen.add(key)
                unique_signals.append(signal)
        
        # Sort by confidence
        unique_signals.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_signals
    
    def filter_by_confidence(self, signals: List[TradingSignal],
                             min_confidence: float = 0.5) -> List[TradingSignal]:
        """Filter signals by minimum confidence"""
        return [s for s in signals if s.confidence >= min_confidence]


# Example usage
if __name__ == "__main__":
    engine = SignalEngine({
        "momentum_threshold": 0.05,
        "whale_min_amount": 1000,
        "arb_threshold": 0.03
    })
    
    # Simulate market pair
    engine.update_market_pair(
        poly_market_id="poly_123",
        kalshi_market_id="kalshi_456",
        poly_yes=0.75,
        poly_no=0.25,
        kalshi_yes=0.70,
        kalshi_no=0.30
    )
    
    signals = engine.analyze_all_pairs()
    for s in signals:
        print(f"Signal: {s.signal_type.value} {s.side} @ {s.confidence:.2%}")
