#!/usr/bin/env python3
"""
Paper trading tester - test strategies without risking real money.

Usage:
    python scripts/paper_trade.py --days 7 --strategies momentum_breakout
"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np


class PaperTrader:
    """
    Paper trading simulator for strategy testing.
    
    Simulates:
    - Order execution at market prices
    - Slippage
    - Commission (Alpaca has 0 commission)
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.max_positions = 10
    
    def execute_buy(self, symbol: str, price: float, qty: float) -> dict:
        """Simulate buying."""
        cost = price * qty
        if cost > self.capital:
            return {"success": False, "reason": "insufficient_capital"}
        
        self.capital -= cost
        if symbol in self.positions:
            current = self.positions[symbol]
            total_qty = current["qty"] + qty
            avg_price = (current["avg_price"] * current["qty"] + price * qty) / total_qty
            self.positions[symbol] = {"qty": total_qty, "avg_price": avg_price}
        else:
            self.positions[symbol] = {"qty": qty, "avg_price": price}
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": "buy",
            "price": price,
            "qty": qty,
            "pnl": 0
        }
        self.trades.append(trade)
        return {"success": True, "trade": trade}
    
    def execute_sell(self, symbol: str, price: float, qty: Optional[float] = None) -> dict:
        """Simulate selling."""
        if symbol not in self.positions:
            return {"success": False, "reason": "no_position"}
        
        position = self.positions[symbol]
        sell_qty = qty if qty else position["qty"]
        
        if sell_qty > position["qty"]:
            return {"success": False, "reason": "insufficient_shares"}
        
        proceeds = price * sell_qty
        self.capital += proceeds
        
        # Calculate realized PNL
        cost_basis = position["avg_price"] * sell_qty
        realized_pnl = proceeds - cost_basis
        
        position["qty"] -= sell_qty
        if position["qty"] <= 0:
            del self.positions[symbol]
        
        trade = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "side": "sell",
            "price": price,
            "qty": sell_qty,
            "pnl": realized_pnl
        }
        self.trades.append(trade)
        return {"success": True, "trade": trade}
    
    def get_portfolio_value(self, current_prices: dict) -> float:
        """Calculate total portfolio value."""
        value = self.capital
        for symbol, position in self.positions.items():
            price = current_prices.get(symbol, position["avg_price"])
            value += position["qty"] * price
        return value
    
    def get_stats(self) -> dict:
        """Get trading statistics."""
        closed_trades = [t for t in self.trades if t["side"] == "sell"]
        winning = [t for t in closed_trades if t["pnl"] > 0]
        losing = [t for t in closed_trades if t["pnl"] < 0]
        
        return {
            "total_trades": len(closed_trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(closed_trades) * 100) if closed_trades else 0,
            "total_pnl": sum(t["pnl"] for t in closed_trades),
            "avg_win": sum(t["pnl"] for t in winning) / len(winning) if winning else 0,
            "avg_loss": sum(t["pnl"] for t in losing) / len(losing) if losing else 0
        }


def simulate_price_movement(start_price: float, volatility: float = 0.02) -> float:
    """Simulate a price movement."""
    change = np.random.normal(0, volatility)
    return start_price * (1 + change)


def run_backtest(
    strategy_name: str,
    symbols: list[str],
    days: int = 30,
    initial_capital: float = 10000
) -> dict:
    """
    Run a simple backtest for a strategy.
    
    This is a placeholder - real backtesting would use historical data.
    """
    trader = PaperTrader(initial_capital)
    
    # Generate simulated price data
    prices = {s: 100.0 for s in symbols}  # Start at $100
    
    for day in range(days):
        # Simulate daily price movement
        for symbol in symbols:
            prices[symbol] = simulate_price_movement(prices[symbol])
        
        # Simple momentum strategy simulation
        if random.random() < 0.3:  # 30% chance of signal each day
            symbol = random.choice(symbols)
            
            if len(trader.positions) < trader.max_positions and symbol not in trader.positions:
                # Buy signal
                result = trader.execute_buy(symbol, prices[symbol], 10)
            
            elif symbol in trader.positions and random.random() < 0.2:
                # Sell signal (take profits or stop loss)
                result = trader.execute_sell(symbol, prices[symbol])
    
    return {
        "strategy": strategy_name,
        "symbols": symbols,
        "days": days,
        "initial_capital": initial_capital,
        "final_capital": trader.capital,
        "portfolio_value": trader.get_portfolio_value(prices),
        "stats": trader.get_stats()
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Paper trading tester")
    parser.add_argument("--days", type=int, default=30, help="Days to simulate")
    parser.add_argument("--capital", type=float, default=10000, help="Initial capital")
    parser.add_argument("--strategies", nargs="+", default=["momentum_breakout"])
    parser.add_argument("--symbols", nargs="+", default=["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"])
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("PAPER TRADING SIMULATION")
    print("=" * 60)
    print(f"Initial Capital: ${args.capital:,.2f}")
    print(f"Days: {args.days}")
    print(f"Symbols: {', '.join(args.symbols)}")
    print()
    
    results = run_backtest(
        args.strategies[0] if args.strategies else "test",
        args.symbols,
        args.days,
        args.capital
    )
    
    print(f"Final Portfolio Value: ${results['portfolio_value']:,.2f}")
    print(f"Return: {((results['portfolio_value'] - args.capital) / args.capital) * 100:.2f}%")
    print()
    print("Statistics:")
    stats = results["stats"]
    print(f"  Total Trades: {stats['total_trades']}")
    print(f"  Win Rate: {stats['win_rate']:.1f}%")
    print(f"  Total P&L: ${stats['total_pnl']:,.2f}")
    print(f"  Avg Win: ${stats['avg_win']:.2f}")
    print(f"  Avg Loss: ${stats['avg_loss']:.2f}")
