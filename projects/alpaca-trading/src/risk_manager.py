"""Risk management for the trading system."""
import json
from dataclasses import asdict
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from .models import TradeSignal, ValidationResult, RiskConfig, AccountInfo, Position


class RiskManager:
    """Manages risk controls and position sizing."""
    
    def __init__(self, config_path: str | Path | None = None):
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "strategy.json"
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Daily tracking
        self._daily_pnl: float = 0.0
        self._daily_trades: int = 0
        self._last_reset: date = date.today()
        self._starting_equity: float = 0.0
    
    def _load_config(self) -> RiskConfig:
        """Load risk config from JSON file."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                data = json.load(f)
                risk_data = data.get("risk", {})
                return RiskConfig(
                    max_position_pct=risk_data.get("max_position_pct", 0.10),
                    max_daily_loss_pct=risk_data.get("max_daily_loss_pct", 0.02),
                    max_positions=risk_data.get("max_positions", 5),
                    stop_loss_pct=risk_data.get("stop_loss_pct", 0.015),
                    take_profit_pct=risk_data.get("take_profit_pct", 0.02),
                    trailing_stop_activation=risk_data.get("trailing_stop_activation", 0.02),
                    min_buying_power=risk_data.get("min_buying_power", 10.0)
                )
        return RiskConfig()
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()
    
    def reset_daily_limits(self, starting_equity: float) -> None:
        """Reset daily tracking (call at market open)."""
        self._daily_pnl = 0.0
        self._daily_trades = 0
        self._last_reset = date.today()
        self._starting_equity = starting_equity
    
    def update_daily_pnl(self, pnl: float) -> None:
        """Update daily P&L (call after each trade)."""
        self._daily_pnl += pnl
        self._daily_trades += 1
    
    def validate_trade(
        self, 
        signal: TradeSignal, 
        account: AccountInfo,
        positions: list[Position]
    ) -> ValidationResult:
        """Validate a trade signal against risk controls."""
        
        # Check if we should halt trading
        if self.should_halt_trading(account):
            return ValidationResult(
                approved=False,
                reason=f"Trading halted: daily loss exceeds {self.config.max_daily_loss_pct * 100}%"
            )
        
        # Check buying power
        if account.buying_power < self.config.min_buying_power:
            return ValidationResult(
                approved=False,
                reason=f"Insufficient buying power: ${account.buying_power:.2f} < ${self.config.min_buying_power:.2f}"
            )
        
        # Check max positions (only for new buys)
        if signal.side == "buy":
            current_symbols = {p.symbol for p in positions}
            if signal.symbol not in current_symbols and len(positions) >= self.config.max_positions:
                return ValidationResult(
                    approved=False,
                    reason=f"Max positions reached: {len(positions)} >= {self.config.max_positions}"
                )
        
        # Calculate allowed position size
        max_position_value = account.portfolio_value * self.config.max_position_pct
        
        return ValidationResult(
            approved=True,
            adjusted_size=max_position_value
        )
    
    def calculate_position_size(
        self, 
        signal: TradeSignal, 
        account: AccountInfo,
        current_price: float
    ) -> float:
        """Calculate position size in shares."""
        # Max position value based on portfolio
        max_value = account.portfolio_value * self.config.max_position_pct
        
        # Can't exceed buying power
        max_value = min(max_value, account.buying_power)
        
        # Reduce size if in drawdown
        if account.portfolio_value < self._starting_equity * 0.9:  # 10% drawdown
            max_value *= 0.5  # Reduce position size by 50%
        
        # Convert to shares
        if current_price > 0:
            shares = max_value / current_price
            return round(shares, 4)  # Alpaca supports fractional shares
        return 0.0
    
    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """Calculate stop loss price."""
        if side == "buy":
            return entry_price * (1 - self.config.stop_loss_pct)
        else:  # sell/short
            return entry_price * (1 + self.config.stop_loss_pct)
    
    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """Calculate take profit price."""
        if side == "buy":
            return entry_price * (1 + self.config.take_profit_pct)
        else:
            return entry_price * (1 - self.config.take_profit_pct)
    
    def should_halt_trading(self, account: AccountInfo) -> bool:
        """Check if trading should be halted due to daily loss."""
        if self._starting_equity <= 0:
            return False
        
        daily_loss_pct = (self._starting_equity - account.equity) / self._starting_equity
        return daily_loss_pct >= self.config.max_daily_loss_pct
    
    def check_trailing_stop(self, position: Position) -> Optional[float]:
        """Check if trailing stop should be updated. Returns new stop price or None."""
        # Only activate trailing stop after reaching activation threshold
        if position.unrealized_pnl_pct < self.config.trailing_stop_activation * 100:
            return None
        
        # Trail at 1% below current price (for long positions)
        trail_pct = 0.01
        new_stop = position.current_price * (1 - trail_pct)
        
        return round(new_stop, 2)
    
    def get_daily_stats(self) -> dict:
        """Get current daily statistics."""
        return {
            "date": self._last_reset.isoformat(),
            "starting_equity": self._starting_equity,
            "daily_pnl": self._daily_pnl,
            "trades_count": self._daily_trades,
            "max_daily_loss_pct": self.config.max_daily_loss_pct
        }


if __name__ == "__main__":
    # Quick test
    rm = RiskManager()
    print("Risk config:", asdict(rm.config))
    print("Stop loss for $100 buy:", rm.calculate_stop_loss(100, "buy"))
    print("Take profit for $100 buy:", rm.calculate_take_profit(100, "buy"))
