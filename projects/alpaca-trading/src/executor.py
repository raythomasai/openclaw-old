"""Order execution module."""
from typing import Optional

from .alpaca_client import AlpacaClient
from .models import TradeSignal, Trade
from .logger import TradingLogger


class OrderExecutor:
    """Manages order submission and position management."""
    
    def __init__(
        self, 
        client: AlpacaClient,
        logger: TradingLogger | None = None
    ):
        self.client = client
        self.logger = logger or TradingLogger()
    
    def submit_order(
        self, 
        signal: TradeSignal, 
        qty: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> Optional[Trade]:
        """
        Submit a market order based on a trade signal.
        
        Args:
            signal: The trade signal
            qty: Number of shares to trade
            stop_loss: Stop loss price (not yet implemented via bracket order)
            take_profit: Take profit price (not yet implemented)
        
        Returns:
            Trade object if successful, None if failed
        """
        try:
            result = self.client.submit_market_order(
                symbol=signal.symbol,
                qty=qty,
                side=signal.side
            )
            
            trade = Trade(
                symbol=signal.symbol,
                side=signal.side,
                qty=qty,
                entry_price=signal.entry_price or 0.0,
                strategy=signal.strategy_name,
                status=result.get("status", "submitted"),
                order_id=result.get("id")
            )
            
            self.logger.log_trade({
                "symbol": trade.symbol,
                "side": trade.side,
                "qty": trade.qty,
                "strategy": trade.strategy,
                "order_id": trade.order_id,
                "status": trade.status
            })
            
            return trade
            
        except Exception as e:
            self.logger.log_error(e, {
                "action": "submit_order",
                "symbol": signal.symbol,
                "side": signal.side,
                "qty": qty
            })
            return None
    
    def close_position(self, symbol: str, reason: str = "signal") -> bool:
        """
        Close a position by symbol.
        
        Args:
            symbol: Stock symbol to close
            reason: Reason for closing (for logging)
        
        Returns:
            True if successful
        """
        try:
            result = self.client.close_position(symbol)
            
            self.logger.info("position_closed", {
                "symbol": symbol,
                "reason": reason,
                "status": result.get("status")
            })
            
            return True
            
        except Exception as e:
            self.logger.log_error(e, {
                "action": "close_position",
                "symbol": symbol,
                "reason": reason
            })
            return False
    
    def close_all_positions(self, reason: str = "halt") -> int:
        """
        Close all positions.
        
        Args:
            reason: Reason for closing all positions
        
        Returns:
            Number of positions closed
        """
        try:
            results = self.client.close_all_positions()
            
            self.logger.info("all_positions_closed", {
                "count": len(results),
                "reason": reason
            })
            
            return len(results)
            
        except Exception as e:
            self.logger.log_error(e, {
                "action": "close_all_positions",
                "reason": reason
            })
            return 0
    
    def get_positions(self):
        """Get current positions."""
        return self.client.get_positions()


if __name__ == "__main__":
    print("Executor module loaded OK")
