#!/usr/bin/env python3
"""
Risk Management
Position limits, stop-loss, daily loss tracking
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk level assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskMetrics:
    """Current risk metrics"""
    daily_pnl: float = 0.0
    daily_trades: int = 0
    open_positions: int = 0
    total_exposure: float = 0.0
    max_single_position: float = 0.0
    risk_level: RiskLevel = RiskLevel.LOW
    warnings: List[str] = field(default_factory=list)


@dataclass
class TradeRequest:
    """A trade request for risk approval"""
    market_id: str
    side: str  # 'yes' or 'no'
    amount: float
    price: float
    strategy: str  # Source strategy
    signal_confidence: float = 0.5


class RiskManager:
    """Manages trading risk"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # Limits
        self.max_trade_amount = config.get("max_trade_amount", 25.0)
        self.max_daily_loss = config.get("max_daily_loss", 100.0)
        self.max_daily_trades = config.get("daily_trade_limit", 50)
        self.max_open_positions = config.get("max_open_positions", 10)
        self.max_single_position = config.get("max_single_position", 100.0)
        self.stop_loss_percent = config.get("stop_loss_percent", 0.25)
        self.take_profit_percent = config.get("take_profit_percent", 0.50)
        
        # Daily tracking
        self.reset_daily()
    
    def reset_daily(self):
        """Reset daily counters"""
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_start_time = datetime.now()
        self.daily_high_water = 0.0
        self.positions: Dict[str, Dict] = {}
    
    def check_daily_reset(self):
        """Check if we need to reset daily counters"""
        now = datetime.now()
        if now.date() != self.daily_start_time.date():
            logger.info("Resetting daily counters")
            self.reset_daily()
    
    def assess_risk(self, request: TradeRequest) -> tuple[bool, str]:
        """
        Assess if a trade request is within risk limits.
        Returns (approved, reason).
        """
        self.check_daily_reset()
        
        # Check daily loss limit
        if self.daily_pnl < -self.max_daily_loss:
            return False, f"Daily loss limit reached (${self.max_daily_loss})"
        
        # Check daily trade limit
        if self.daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"
        
        # Check position limits
        total_exposure = self._get_total_exposure()
        if total_exposure + request.amount > self.max_single_position:
            return False, f"Single position limit would be exceeded"
        
        # Check open positions
        if len(self.positions) >= self.max_open_positions:
            return False, f"Max open positions reached ({self.max_open_positions})"
        
        # Check trade amount
        if request.amount > self.max_trade_amount:
            return False, f"Trade amount ${request.amount} exceeds max ${self.max_trade_amount}"
        
        if request.amount < 1.0:
            return False, f"Trade amount ${request.amount} below minimum $1.0"
        
        # Check confidence threshold based on position size
        if request.amount > self.max_trade_amount * 0.5:
            if request.signal_confidence < 0.6:
                return False, f"Low confidence ({request.signal_confidence:.0%}) for large trade"
        
        return True, "Approved"
    
    def update_position(self, market_id: str, side: str, amount: float,
                        price: float, realized_pnl: float = 0.0):
        """Update position after trade"""
        self.check_daily_reset()
        
        self.daily_pnl += realized_pnl
        self.daily_trades += 1
        
        # Track positions
        if market_id not in self.positions:
            self.positions[market_id] = {
                "side": side,
                "amount": 0.0,
                "avg_price": 0.0,
                "unrealized_pnl": 0.0
            }
        
        pos = self.positions[market_id]
        pos["amount"] += amount
        pos["avg_price"] = (pos["avg_price"] * (pos["amount"] - amount) + 
                           price * amount) / pos["amount"]
        
        # Update high water mark
        if self.daily_pnl > self.daily_high_water:
            self.daily_high_water = self.daily_pnl
    
    def get_unrealized_pnl(self, market_id: str, current_price: float,
                            side: str) -> float:
        """Calculate unrealized P&L for a position"""
        if market_id not in self.positions:
            return 0.0
        
        pos = self.positions[market_id]
        if pos["amount"] == 0:
            return 0.0
        
        if side == "yes":
            return (current_price - pos["avg_price"]) * pos["amount"]
        else:
            return ((1 - current_price) - (1 - pos["avg_price"])) * pos["amount"]
    
    def check_stop_loss(self, market_id: str, current_price: float,
                        side: str) -> bool:
        """Check if stop-loss should trigger"""
        if market_id not in self.positions:
            return False
        
        pos = self.positions[market_id]
        unrealized = self.get_unrealized_pnl(market_id, current_price, side)
        
        # Stop out if losing more than threshold
        if unrealized < -pos["amount"] * self.stop_loss_percent:
            logger.warning(f"Stop-loss triggered on {market_id}: ${unrealized:.2f}")
            return True
        
        return False
    
    def check_take_profit(self, market_id: str, current_price: float,
                          side: str) -> bool:
        """Check if take-profit should trigger"""
        if market_id not in self.positions:
            return False
        
        pos = self.positions[market_id]
        unrealized = self.get_unrealized_pnl(market_id, current_price, side)
        
        # Take profit if above threshold
        if unrealized > pos["amount"] * self.take_profit_percent:
            logger.info(f"Take-profit triggered on {market_id}: ${unrealized:.2f}")
            return True
        
        return False
    
    def should_close_position(self, market_id: str, current_price: float,
                              side: str) -> tuple[bool, str]:
        """Determine if a position should be closed"""
        if market_id not in self.positions:
            return False, ""
        
        unrealized = self.get_unrealized_pnl(market_id, current_price, side)
        pos = self.positions[market_id]
        
        # Stop loss
        if unrealized < -pos["amount"] * self.stop_loss_percent:
            return True, "stop_loss"
        
        # Take profit
        if unrealized > pos["amount"] * self.take_profit_percent:
            return True, "take_profit"
        
        # Time-based exit (24 hours)
        # Would need to track entry time
        
        return False, ""
    
    def get_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        self.check_daily_reset()
        
        total_exposure = self._get_total_exposure()
        max_position = self._get_max_position()
        
        # Determine risk level
        if self.daily_pnl < -self.max_daily_loss * 0.8:
            risk_level = RiskLevel.CRITICAL
        elif self.daily_pnl < -self.max_daily_loss * 0.5:
            risk_level = RiskLevel.HIGH
        elif self.daily_pnl < -self.max_daily_loss * 0.25:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        warnings = []
        if self.daily_pnl < -self.max_daily_loss * 0.7:
            warnings.append("Approaching daily loss limit")
        if len(self.positions) >= self.max_open_positions * 0.8:
            warnings.append("Approaching position limit")
        if self.daily_trades >= self.max_daily_trades * 0.8:
            warnings.append("Approaching daily trade limit")
        
        return RiskMetrics(
            daily_pnl=self.daily_pnl,
            daily_trades=self.daily_trades,
            open_positions=len(self.positions),
            total_exposure=total_exposure,
            max_single_position=max_position,
            risk_level=risk_level,
            warnings=warnings
        )
    
    def _get_total_exposure(self) -> float:
        """Calculate total position exposure"""
        return sum(p["amount"] for p in self.positions.values())
    
    def _get_max_position(self) -> float:
        """Get largest single position"""
        if not self.positions:
            return 0.0
        return max(p["amount"] for p in self.positions.values())
    
    def close_position(self, market_id: str) -> float:
        """Close and remove a position, return realized P&L"""
        if market_id not in self.positions:
            return 0.0
        
        del self.positions[market_id]
        return 0.0  # P&L handled by update_position
    
    def get_daily_summary(self) -> Dict:
        """Get daily trading summary"""
        self.check_daily_reset()
        
        return {
            "date": self.daily_start_time.date().isoformat(),
            "pnl": self.daily_pnl,
            "trades": self.daily_trades,
            "high_water": self.daily_high_water,
            "positions_open": len(self.positions),
            "status": "active" if self.daily_pnl > -self.max_daily_loss else "stopped"
        }


# Convenience functions
def calculate_position_size(confidence: float, max_size: float,
                            risk_per_trade: float = 0.02) -> float:
    """
    Calculate position size based on Kelly Criterion (simplified).
    
    Args:
        confidence: Estimated win probability (0-1)
        max_size: Maximum allowed position size
        risk_per_trade: Fraction of bankroll to risk
    
    Returns:
        Recommended position size
    """
    # Kelly fraction = p - q/b
    # where p = win prob, q = loss prob (1-p), b = win/loss ratio
    
    # Simplified: scale by confidence
    if confidence < 0.5:
        return 0.0  # Don't trade
    
    kelly = confidence - (1 - confidence) / 1.0  # Assuming 1:1 payout
    kelly = max(0, kelly)  # Don't go negative
    
    # Fractional Kelly (reduce variance)
    kelly = kelly * 0.5  # Half Kelly
    
    size = kelly * max_size * 10  # Scale to position size
    
    return min(size, max_size)


# Example usage
if __name__ == "__main__":
    manager = RiskManager({
        "max_trade_amount": 25.0,
        "max_daily_loss": 100.0,
        "daily_trade_limit": 50,
        "max_open_positions": 10,
        "stop_loss_percent": 0.25,
        "take_profit_percent": 0.50
    })
    
    # Test some trades
    request = TradeRequest(
        market_id="test_market",
        side="yes",
        amount=20.0,
        price=0.70,
        strategy="momentum",
        signal_confidence=0.75
    )
    
    approved, reason = manager.assess_risk(request)
    print(f"Trade approved: {approved}, reason: {reason}")
    
    if approved:
        manager.update_position(
            market_id=request.market_id,
            side=request.side,
            amount=request.amount,
            price=request.price
        )
    
    metrics = manager.get_metrics()
    print(f"\nRisk Metrics:")
    print(f"  Daily P&L: ${metrics.daily_pnl:.2f}")
    print(f"  Daily Trades: {metrics.daily_trades}")
    print(f"  Open Positions: {metrics.open_positions}")
    print(f"  Risk Level: {metrics.risk_level.value}")
