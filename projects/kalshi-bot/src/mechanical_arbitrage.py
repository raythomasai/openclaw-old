#!/usr/bin/env python3
"""
Mechanical Arbitrage Strategy
Buy YES and NO until avg_YES + avg_NO < $1.00
Based on the Gabagool Method
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ArbPosition:
    """Mechanical arbitrage position"""
    market_id: str
    yes_qty: float = 0.0
    no_qty: float = 0.0
    yes_cost: float = 0.0
    no_cost: float = 0.0
    avg_yes: float = 0.0
    avg_no: float = 0.0
    pair_cost: float = 1.0
    locked: bool = False
    created_at: datetime = field(default_factory=datetime.now)
    
    @property
    def guaranteed_profit(self) -> float:
        """Is this position guaranteed to profit?"""
        min_shares = min(self.yes_qty, self.no_qty)
        total_cost = self.yes_cost + self.no_cost
        return min_shares - total_cost
    
    @property
    def profit_if_yes_wins(self) -> float:
        """Profit if YES wins"""
        return self.yes_qty - (self.yes_cost + self.no_cost)
    
    @property
    def profit_if_no_wins(self) -> float:
        """Profit if NO wins"""
        return self.no_qty - (self.yes_cost + self.no_cost)


class MechanicalArbitrage:
    """
    Implements the mechanical arbitrage strategy:
    - Track YES and NO quantities and costs
    - Buy the cheap side when mispriced
    - Stop when pair_cost < $1.00 (guaranteed profit)
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_trade_amount = config.get("max_trade_amount", 25.0)
        self.profit_threshold = config.get("arb_threshold", 0.02)  # Target 2% min
        self.min_cheap_threshold = 0.15  # Only buy if side is >15% below fair
        
        # Track open positions
        self.positions: Dict[str, ArbPosition] = {}
        
        # Closed positions for history
        self.closed_positions: List[ArbPosition] = []
        
        # Stats
        self.total_trades = 0
        self.total_profit = 0.0
    
    def get_position(self, market_id: str) -> ArbPosition:
        """Get or create position for a market"""
        if market_id not in self.positions:
            self.positions[market_id] = ArbPosition(market_id=market_id)
        return self.positions[market_id]
    
    def calculate_buy_amount(self, position: ArbPosition, current_price: float,
                            side: str) -> float:
        """
        Calculate how much to buy on the cheap side.
        
        Strategy: Keep buying until pair_cost < $1.00
        We want roughly equal quantities for maximum hedge.
        """
        # Calculate what we need
        target_pair_cost = 1.0 - self.profit_threshold
        current_pair_cost = position.pair_cost
        
        if current_pair_cost >= target_pair_cost:
            # Need to reduce pair cost
            shortfall = current_pair_cost - target_pair_cost
            
            # Amount needed at current price
            # shortfall = (current_cost + (price * qty)) / (current_qty + qty)
            # Simplified: just buy enough to move average
            
            if position.yes_qty == position.no_qty:
                # Balanced, buy the cheap side
                amount = min(shortfall / current_price * 2, self.max_trade_amount)
            else:
                # Unbalanced, try to rebalance
                diff = abs(position.yes_qty - position.no_qty)
                amount = min(diff * current_price, self.max_trade_amount)
            
            return max(amount, 1.0)  # Minimum $1
        
        return 0.0
    
    def analyze_market(self, yes_price: float, no_price: float,
                       market_id: str) -> Optional[Tuple[str, float, float]]:
        """
        Analyze a market for arbitrage opportunity.
        
        Returns: (side_to_buy, amount, expected_profit) or None
        """
        position = self.get_position(market_id)
        
        # Check if already locked (guaranteed profit)
        if position.locked:
            logger.debug(f"Position {market_id} already locked")
            return None
        
        # Check if already have significant position
        if position.yes_qty > 0 and position.no_qty > 0:
            if position.pair_cost < 1.0:
                # Locked profit!
                position.locked = True
                profit = position.guaranteed_profit
                logger.info(f"ARB LOCKED on {market_id}: ${profit:.2f} guaranteed")
                return None  # Don't buy more
        
        # Calculate current averages
        if position.yes_qty > 0:
            position.avg_yes = position.yes_cost / position.yes_qty
        if position.no_qty > 0:
            position.avg_no = position.no_cost / position.no_qty
        
        position.pair_cost = position.avg_yes + position.avg_no
        
        # Find cheap side
        # A fair market has YES + NO = $1.00
        # If YES = $0.40, NO should be $0.60 (but might be $0.55)
        # Cheap side is the one below its fair value
        
        fair_value = 1.0 - (position.avg_yes if position.avg_yes > 0 else 0.5)
        cheap_side = None
        
        if position.avg_yes == 0 and position.avg_no == 0:
            # Fresh position - both at initial prices
            if yes_price < no_price - self.min_cheap_threshold:
                cheap_side = "yes"
            elif no_price < yes_price - self.min_cheap_threshold:
                cheap_side = "no"
        else:
            # Existing position - compare to fair
            if position.avg_yes < 0.5 and yes_price < position.avg_yes * 0.9:
                cheap_side = "yes"
            elif position.avg_no < 0.5 and no_price < position.avg_no * 0.9:
                cheap_side = "no"
            else:
                # Check if we can complete the hedge
                if position.yes_qty > position.no_qty * 1.2:
                    cheap_side = "no"
                elif position.no_qty > position.yes_qty * 1.2:
                    cheap_side = "yes"
        
        if cheap_side is None:
            return None
        
        # Calculate amount
        price = yes_price if cheap_side == "yes" else no_price
        amount = self.calculate_buy_amount(position, price, cheap_side)
        
        if amount < 1.0:
            return None
        
        # Calculate expected profit
        new_pair_cost = (position.yes_cost + (price * amount if cheap_side == "yes" else 0) +
                        position.no_cost + (price * amount if cheap_side == "no" else 0)) / \
                       (position.yes_qty + (amount if cheap_side == "yes" else 0) +
                        position.no_qty + (amount if cheap_side == "no" else 0))
        
        expected_profit = 1.0 - new_pair_cost
        
        return cheap_side, amount, expected_profit
    
    def execute_buy(self, market_id: str, side: str, amount: float,
                    price: float) -> None:
        """Record a buy execution"""
        position = self.get_position(market_id)
        
        cost = amount * price
        
        if side == "yes":
            position.yes_qty += amount
            position.yes_cost += cost
            position.avg_yes = position.yes_cost / position.yes_qty
        else:
            position.no_qty += amount
            position.no_cost += cost
            position.avg_no = position.no_cost / position.no_qty
        
        position.pair_cost = position.avg_yes + position.avg_no
        
        # Check if locked
        if position.yes_qty > 0 and position.no_qty > 0:
            if position.pair_cost < 1.0:
                position.locked = True
                logger.info(f"Position {market_id} LOCKED with ${position.guaranteed_profit:.2f} profit")
        
        self.total_trades += 1
        logger.info(f"ARB: Bought {side} {amount:.2f} @ ${price:.2f} on {market_id}")
    
    def close_position(self, market_id: str, outcome: str) -> float:
        """Close a position after market resolves"""
        if market_id not in self.positions:
            return 0.0
        
        position = self.positions[market_id]
        
        # Calculate profit
        if outcome == "yes":
            profit = position.yes_qty - position.yes_cost - position.no_cost
        else:
            profit = position.no_qty - position.yes_cost - position.no_cost
        
        self.total_profit += profit
        
        # Move to closed
        self.closed_positions.append(position)
        del self.positions[market_id]
        
        logger.info(f"Closed {market_id} ({outcome}): ${profit:.2f}")
        return profit
    
    def get_stats(self) -> Dict:
        """Get strategy statistics"""
        open_profit = sum(p.guaranteed_profit for p in self.positions.values() if p.locked)
        
        return {
            "open_positions": len(self.positions),
            "locked_positions": sum(1 for p in self.positions.values() if p.locked),
            "closed_positions": len(self.closed_positions),
            "total_trades": self.total_trades,
            "total_profit": self.total_profit,
            "open_locked_profit": open_profit,
            "total_pnl": self.total_profit + open_profit
        }
    
    def should_exit(self, market_id: str, current_price: float,
                    side: str) -> Tuple[bool, float]:
        """
        Determine if we should exit a position early.
        Returns (should_exit, profit).
        """
        if market_id not in self.positions:
            return False, 0.0
        
        position = self.positions[market_id]
        
        # Calculate current unrealized P&L
        if side == "yes":
            current_value = position.yes_qty * current_price
        else:
            current_value = position.no_qty * (1 - current_price)
        
        total_cost = position.yes_cost + position.no_cost
        unrealized_pnl = current_value - total_cost
        
        # Exit if we're in profit and price moved against us
        if unrealized_pnl > 0:
            return False, unrealized_pnl
        
        # Exit if we're losing more than 20% of cost
        if abs(unrealized_pnl) > total_cost * 0.20:
            return True, unrealized_pnl
        
        return False, 0.0


# Example usage
if __name__ == "__main__":
    arb = MechanicalArbitrage({
        "max_trade_amount": 25.0,
        "arb_threshold": 0.02
    })
    
    # Simulate a trade
    # Market: YES=$0.40, NO=$0.65 (cheap YES)
    result = arb.analyze_market(0.40, 0.65, "test_market")
    if result:
        side, amount, expected = result
        print(f"Buy {side}: ${amount:.2f}, expected profit: ${expected:.2f}")
        arb.execute_buy("test_market", side, amount, 0.40)
    
    # Market moves: YES=$0.55, NO=$0.50 (now NO is cheap)
    result = arb.analyze_market(0.55, 0.50, "test_market")
    if result:
        side, amount, expected = result
        print(f"Buy {side}: ${amount:.2f}, expected profit: ${expected:.2f}")
        arb.execute_buy("test_market", side, amount, 0.50)
    
    # Check position
    pos = arb.get_position("test_market")
    print(f"\nPosition:")
    print(f"  YES: {pos.yes_qty:.2f} @ ${pos.avg_yes:.2f}")
    print(f"  NO: {pos.no_qty:.2f} @ ${pos.avg_no:.2f}")
    print(f"  Pair Cost: ${pos.pair_cost:.3f}")
    print(f"  Locked: {pos.locked}")
    if pos.locked:
        print(f"  Guaranteed Profit: ${pos.guaranteed_profit:.2f}")
    
    print(f"\nStats: {arb.get_stats()}")
