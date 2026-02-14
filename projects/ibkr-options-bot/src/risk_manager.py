"""
Risk Manager
Aggressive risk controls for momentum trading
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

import yaml

from ibkr_client import Position

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Current risk metrics"""
    portfolio_value: float
    cash_available: float
    daily_pnl: float
    daily_pnl_pct: float
    open_positions_value: float
    long_exposure: float
    short_exposure: float
    net_exposure: float
    max_drawdown: float
    var_1day: float  # Value at Risk


class RiskManager:
    """Risk management for aggressive trading"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.config = self._load_config(config_path)
        self.portfolio_value = 100000  # Default
        self.cash = 100000
        self.daily_pnl = 0.0
        self.daily_high = 0.0
        self.daily_low = 0.0
        self.peak_value = 100000
        self.positions: List[Position] = []
        
    def _load_config(self, config_path: str) -> dict:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def update_portfolio(self, account_value: float, cash: float, 
                        positions: List[Position]):
        """Update portfolio state"""
        self.portfolio_value = account_value
        self.cash = cash
        self.positions = positions
        
        # Track daily P&L
        if self.daily_high == 0:
            self.daily_high = account_value
        if self.daily_low == 0:
            self.daily_low = account_value
            
        self.daily_high = max(self.daily_high, account_value)
        self.daily_low = min(self.daily_low, account_value)
        
        # Calculate daily P&L
        self.daily_pnl = account_value - self.peak_value
        
        # Update peak
        self.peak_value = max(self.peak_value, account_value)
    
    def get_metrics(self) -> RiskMetrics:
        """Get current risk metrics"""
        # Calculate exposures
        long_exposure = sum(
            p.market_value for p in self.positions if p.position > 0
        )
        short_exposure = sum(
            p.market_value for p in self.positions if p.position < 0
        )
        
        return RiskMetrics(
            portfolio_value=self.portfolio_value,
            cash_available=self.cash,
            daily_pnl=self.daily_pnl,
            daily_pnl_pct=(self.daily_pnl / self.peak_value * 100) if self.peak_value > 0 else 0,
            open_positions_value=sum(p.market_value for p in self.positions),
            long_exposure=long_exposure,
            short_exposure=short_exposure,
            net_exposure=long_exposure - short_exposure,
            max_drawdown=self._calculate_max_drawdown(),
            var_1day=self._calculate_var()
        )
    
    def can_open_position(self, trade_value: float, direction: str) -> Tuple[bool, str]:
        """
        Check if we can open a new position
        
        Returns: (can_trade, reason)
        """
        risk_config = self.config.get('risk', {})
        strategy_config = self.config.get('strategy', {})
        
        # 1. Check daily loss limit
        max_daily_loss = risk_config.get('max_daily_loss_pct', 0.05)
        daily_loss = abs(self.daily_pnl) / self.peak_value if self.peak_value > 0 else 0
        
        if daily_loss >= max_daily_loss:
            return False, f"Daily loss limit reached ({daily_loss*100:.1f}% / {max_daily_loss*100}%)"
        
        # 2. Check circuit breaker (intraday)
        circuit_breaker = risk_config.get('circuit_breaker_pct', 0.03)
        if daily_loss >= circuit_breaker:
            return False, f"Circuit breaker triggered ({daily_loss*100:.1f}%)"
        
        # 3. Check max position allocation
        max_allocation = strategy_config.get('max_allocation_per_trade', 0.08)
        if trade_value > self.portfolio_value * max_allocation:
            return False, f"Trade value ${trade_value:,.0f} exceeds ${self.portfolio_value * max_allocation:,.0f} limit"
        
        # 4. Check side exposure
        metrics = self.get_metrics()
        max_side = strategy_config.get('max_side_exposure', 0.60)
        
        if direction == 'long':
            new_long = metrics.long_exposure + trade_value
            if new_long > self.portfolio_value * max_side:
                return False, f"Long exposure would be {new_long/self.portfolio_value*100:.0f}% (max: {max_side*100}%)"
        else:  # short
            new_short = metrics.short_exposure + trade_value
            if new_short > self.portfolio_value * max_side:
                return False, f"Short exposure would be {new_short/self.portfolio_value*100:.0f}% (max: {max_side*100}%)"
        
        # 5. Check cash availability
        if trade_value > self.cash:
            return False, f"Insufficient cash (${self.cash:,.0f} < ${trade_value:,.0f})"
        
        return True, "OK"
    
    def should_close_position(self, position: Position, current_price: float,
                             direction: str) -> Tuple[bool, str]:
        """
        Check if a position should be closed
        
        Returns: (should_close, reason)
        """
        risk_config = self.config.get('risk', {})
        
        # 1. Check stop loss
        stop_loss_pct = risk_config.get('max_loss_per_trade', 0.02)
        
        if direction == 'long':
            loss_pct = (position.avg_cost - current_price) / position.avg_cost
        else:
            loss_pct = (current_price - position.avg_cost) / position.avg_cost
        
        if loss_pct >= stop_loss_pct:
            return True, f"Stop loss triggered ({loss_pct*100:.1f}%)"
        
        # 2. Check profit target
        profit_target = risk_config.get('profit_target_pct', 0.03)
        
        if direction == 'long':
            gain_pct = (current_price - position.avg_cost) / position.avg_cost
        else:
            gain_pct = (position.avg_cost - current_price) / position.avg_cost
        
        if gain_pct >= profit_target:
            return True, f"Profit target reached ({gain_pct*100:.1f}%)"
        
        # 3. Check trailing stop
        trailing_stop = risk_config.get('trailing_stop', False)
        trailing_pct = risk_config.get('trailing_stop_pct', 0.015)
        
        if trailing_stop and position.unrealized_pnl > 0:
            # Would need to track high water mark per position
            pass
        
        return False, ""
    
    def get_position_size(self, confidence: float, reward_risk: float,
                          account_pct: float = 0.02) -> int:
        """
        Calculate position size based on Kelly Criterion (conservative)
        
        Args:
            confidence: Signal confidence (0-1)
            reward_risk: Reward to risk ratio
            account_pct: Percentage of account to risk
            
        Returns: Number of contracts
        """
        # Kelly fraction (conservative = 0.5 * Kelly)
        kelly = (confidence * reward_risk - (1 - confidence)) / reward_risk
        kelly = max(0, kelly * 0.5)  # Half Kelly
        
        # Calculate position size
        risk_amount = self.portfolio_value * account_pct
        contracts = int(risk_amount / 100 / kelly) if kelly > 0 else 1
        
        # Limit contracts
        max_contracts = int(self.portfolio_value * 0.10 / 1000)  # Max 10% of portfolio
        return min(contracts, max_contracts, 10)
    
    def should_stop_trading(self) -> Tuple[bool, str]:
        """Check if trading should be stopped entirely"""
        risk_config = self.config.get('risk', {})
        
        # Check max drawdown
        max_drawdown = risk_config.get('max_drawdown_pct', 0.10)
        current_drawdown = (self.peak_value - self.portfolio_value) / self.peak_value
        
        if current_drawdown >= max_drawdown:
            return True, f"Max drawdown reached ({current_drawdown*100:.1f}%)"
        
        # Check daily loss
        max_daily_loss = risk_config.get('max_daily_loss_pct', 0.05)
        daily_loss = abs(self.daily_pnl) / self.peak_value
        
        if daily_loss >= max_daily_loss:
            return True, f"Daily loss limit reached ({daily_loss*100:.1f}%)"
        
        return False, "OK"
    
    def _calculate_max_drawdown(self) -> float:
        """Calculate current max drawdown"""
        if self.peak_value == 0:
            return 0.0
        return (self.peak_value - self.portfolio_value) / self.peak_value
    
    def _calculate_var(self, confidence: float = 0.95) -> float:
        """Calculate Value at Risk (simplified)"""
        # Simple historical VaR approximation
        volatility = 0.02  # 2% daily volatility assumption
        z_score = 1.645  # 95% confidence
        return self.portfolio_value * volatility * z_score
    
    def reset_daily(self):
        """Reset daily metrics"""
        self.daily_pnl = 0.0
        self.daily_high = 0.0
        self.daily_low = 0.0
        self.peak_value = self.portfolio_value
        
        logger.info("Daily metrics reset")


class ExposureManager:
    """Manages portfolio exposure across positions"""
    
    def __init__(self, config: dict):
        self.config = config
        self.sector_limits = {}
        self.symbol_limits = {}
        
    def check_exposure(self, symbol: str, sector: str, 
                      trade_value: float, total_value: float) -> Tuple[bool, str]:
        """Check if trade would exceed exposure limits"""
        
        # Check symbol concentration
        current_symbol = self.symbol_limits.get(symbol, 0)
        max_symbol = self.config.get('strategy', {}).get('max_symbol_exposure', 0.10)
        
        if current_symbol + trade_value > total_value * max_symbol:
            return False, f"Symbol exposure limit for {symbol}"
        
        # Check sector concentration
        current_sector = self.sector_limits.get(sector, 0)
        max_sector = self.config.get('strategy', {}).get('max_sector_exposure', 0.30)
        
        if current_sector + trade_value > total_value * max_sector:
            return False, f"Sector exposure limit for {sector}"
        
        return True, "OK"
    
    def add_position(self, symbol: str, sector: str, value: float):
        """Add a position to exposure tracking"""
        self.symbol_limits[symbol] = self.symbol_limits.get(symbol, 0) + value
        self.sector_limits[sector] = self.sector_limits.get(sector, 0) + value
    
    def remove_position(self, symbol: str, sector: str, value: float):
        """Remove a position from exposure tracking"""
        self.symbol_limits[symbol] = max(0, self.symbol_limits.get(symbol, 0) - value)
        self.sector_limits[sector] = max(0, self.sector_limits.get(sector, 0) - value)


if __name__ == "__main__":
    print("Risk Manager loaded")
