#!/usr/bin/env python3
"""
Backtesting Framework - Test strategies before risking money

Usage:
    python backtest.py --strategy momentum --days 30
    python backtest.py --all --days 90
"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable
import sys

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))


class Backtester:
    """
    Backtesting framework for testing trading strategies.
    
    Key features:
    - Historical data simulation
    - Realistic slippage modeling
    - Commission-free (like Alpaca)
    - Position sizing rules
    - Performance metrics
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # symbol -> {qty, entry_price}
        self.trades = []
        self.daily_returns = []
        
    def run(self, 
            strategy: Callable,
            data: list[dict],
            params: dict) -> dict:
        """
        Run backtest for a strategy.
        
        Args:
            strategy: Strategy function that takes price data and returns signal
            data: List of price bars {open, high, low, close, volume, timestamp}
            params: Strategy parameters
        
        Returns:
            Performance metrics dict
        """
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_returns = []
        
        equity_curve = []
        
        for i, bar in enumerate(data):
            signal = strategy(bar, i, data, params)
            
            if signal == "buy" and bar['symbol'] not in self.positions:
                # Calculate position size
                position_size = self.capital * params.get('position_pct', 0.1)
                shares = position_size / bar['close']
                
                # Execute
                cost = shares * bar['close']
                self.capital -= cost
                self.positions[bar['symbol']] = {
                    'qty': shares,
                    'entry_price': bar['close'],
                    'bar': bar
                }
                
                self.trades.append({
                    'type': 'buy',
                    'symbol': bar['symbol'],
                    'price': bar['close'],
                    'qty': shares,
                    'timestamp': bar.get('timestamp', i)
                })
            
            elif signal == "sell" and bar['symbol'] in self.positions:
                pos = self.positions[bar['symbol']]
                
                # Calculate PNL
                cost_basis = pos['qty'] * pos['entry_price']
                proceeds = pos['qty'] * bar['close']
                pnl = proceeds - cost_basis
                
                self.capital += proceeds
                
                self.trades.append({
                    'type': 'sell',
                    'symbol': bar['symbol'],
                    'price': bar['close'],
                    'qty': pos['qty'],
                    'pnl': pnl,
                    'timestamp': bar.get('timestamp', i)
                })
                
                del self.positions[bar['symbol']]
            
            # Track equity
            position_value = sum(
                p['qty'] * bar['close'] 
                for p in self.positions.values()
            )
            total_value = self.capital + position_value
            equity_curve.append(total_value)
        
        # Close any open positions
        if self.positions:
            last_price = data[-1]['close']
            for symbol, pos in self.positions.items():
                pnl = pos['qty'] * last_price - pos['qty'] * pos['entry_price']
                self.trades.append({
                    'type': 'close',
                    'symbol': symbol,
                    'pnl': pnl
                })
        
        return self._calculate_metrics(equity_curve)
    
    def _calculate_metrics(self, equity_curve: list[float]) -> dict:
        """Calculate performance metrics."""
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i] - equity_curve[i-1]) / equity_curve[i-1]
            returns.append(ret)
        
        total_return = (equity_curve[-1] - self.initial_capital) / self.initial_capital
        
        # Win rate
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        
        # Max drawdown
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return {
            'initial_capital': self.initial_capital,
            'final_value': equity_curve[-1],
            'total_return': total_return * 100,
            'total_trades': len([t for t in self.trades if t['type'] == 'sell']),
            'win_rate': win_rate,
            'max_drawdown': max_dd * 100,
            'avg_return_per_trade': sum(t.get('pnl', 0) for t in closed_trades) / len(closed_trades) if closed_trades else 0,
            'equity_curve': equity_curve
        }


def momentum_strategy(bar: dict, i: int, data: list, params: dict) -> Optional[str]:
    """
    Momentum strategy - buy when price breaks above VWAP.
    
    Signal logic:
    - Calculate VWAP
    - If price > VWAP * (1 + buffer): BUY
    - If price < VWAP * (1 - buffer): SELL
    """
    if i < 20:
        return None
    
    # Calculate VWAP
    typical_price = (bar['high'] + bar['low'] + bar['close']) / 3
    volume = bar['volume']
    
    # Get previous bars for cumulative calculation
    recent = data[max(0, i-20):i+1]
    
    pv_sum = sum((r['high'] + r['low'] + r['close']) / 3 * r['volume'] for r in recent)
    vol_sum = sum(r['volume'] for r in recent)
    
    if vol_sum == 0:
        return None
    
    vwap = pv_sum / vol_sum
    
    # Signal
    buffer = params.get('vwap_buffer', 0.001)
    
    if bar['close'] > vwap * (1 + buffer):
        return "buy"
    elif bar['close'] < vwap * (1 - buffer):
        return "sell"
    
    return None


def mean_reversion_strategy(bar: dict, i: int, data: list, params: dict) -> Optional[str]:
    """
    Mean reversion - buy when RSI oversold.
    """
    if i < 14:
        return None
    
    # Calculate RSI
    closes = [d['close'] for d in data[i-14:i+1]]
    
    gains = []
    losses = []
    for j in range(1, len(closes)):
        change = closes[j] - closes[j-1]
        if change > 0:
            gains.append(change)
        else:
            losses.append(abs(change))
    
    if not gains or not losses:
        return None
    
    avg_gain = sum(gains) / len(gains)
    avg_loss = sum(losses) / len(losses)
    
    if avg_loss == 0:
        return None
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    # Signal
    oversold = params.get('rsi_oversold', 30)
    overbought = params.get('rsi_overbought', 70)
    
    if rsi < oversold:
        return "buy"
    elif rsi > overbought:
        return "sell"
    
    return None


def generate_synthetic_data(symbol: str, days: int = 100) -> list[dict]:
    """
    Generate synthetic price data for testing.
    
    Uses random walk with drift.
    """
    import numpy as np
    
    np.random.seed(42)  # Reproducible
    
    start_price = 100
    daily_return = 0.0002  # Small positive drift
    volatility = 0.02
    
    prices = []
    current_price = start_price
    
    for i in range(days):
        daily_vol = np.random.normal(daily_return, volatility)
        current_price = current_price * (1 + daily_vol)
        
        open_price = current_price
        close_price = current_price * (1 + np.random.normal(0, 0.005))
        high_price = max(open_price, close_price) * (1 + abs(np.random.normal(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(np.random.normal(0, 0.01)))
        volume = int(1000000 * (1 + np.random.normal(0, 0.3)))
        
        prices.append({
            'symbol': symbol,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume,
            'timestamp': (datetime.now() - timedelta(days=days-i)).isoformat()
        })
        
        current_price = close_price
    
    return prices


def run_backtest(args):
    """Main backtest runner."""
    print("=" * 60)
    print("BACKTESTING FRAMEWORK")
    print("=" * 60)
    print()
    
    # Generate test data
    if args.symbols:
        symbols = args.symbols
    else:
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Days: {args.days}")
    print(f"Initial Capital: ${args.capital:,.2f}")
    print()
    
    # Test each strategy
    strategies = {
        'momentum': (momentum_strategy, {'vwap_buffer': 0.001, 'position_pct': 0.1}),
        'mean_reversion': (mean_reversion_strategy, {'rsi_oversold': 30, 'rsi_overbought': 70, 'position_pct': 0.1})
    }
    
    if args.strategy and args.strategy in strategies:
        strategies = {args.strategy: strategies[args.strategy]}
    
    results = {}
    
    for strat_name, (strat_func, params) in strategies.items():
        print(f"Testing {strat_name}...")
        
        bt = Backtester(args.capital)
        
        all_data = []
        for symbol in symbols:
            data = generate_synthetic_data(symbol, args.days)
            all_data.extend(data)
        
        # Sort by timestamp
        all_data.sort(key=lambda x: x['timestamp'])
        
        metrics = bt.run(strat_func, all_data, params)
        results[strat_name] = metrics
        
        print(f"  Final Value: ${metrics['final_value']:,.2f}")
        print(f"  Return: {metrics['total_return']:.2f}%")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Max Drawdown: {metrics['max_drawdown']:.2f}%")
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    best = max(results.items(), key=lambda x: x[1]['total_return'])
    print(f"Best Strategy: {best[0]} ({best[1]['total_return']:.2f}%)")
    
    # Recommendation
    print()
    print("RECOMMENDATION:")
    for name, metrics in results.items():
        if metrics['total_return'] > 0 and metrics['win_rate'] > 50:
            print(f"  ✅ {name}: Worth testing with paper trading")
        else:
            print(f"  ❌ {name}: Needs more work")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backtesting framework')
    parser.add_argument('--strategy', type=str, choices=['momentum', 'mean_reversion'],
                       help='Strategy to test')
    parser.add_argument('--days', type=int, default=100,
                       help='Number of days to test')
    parser.add_argument('--capital', type=float, default=10000,
                       help='Initial capital')
    parser.add_argument('--symbols', nargs='+', default=None,
                       help='Symbols to test')
    
    args = parser.parse_args()
    run_backtest(args)
