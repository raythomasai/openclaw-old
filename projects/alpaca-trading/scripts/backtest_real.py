#!/usr/bin/env python3
"""
Proper Backtesting with REAL Historical Data (Yahoo Finance)

Usage:
    python scripts/backtest_real.py --strategy momentum --symbol SPY --days 365
    python scripts/backtest_real.py --all --days 730
"""
import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Add project to path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_DIR))

import yfinance as yf


class HistoricalBacktester:
    """
    Backtester using REAL historical data from Alpaca.
    
    Key features:
    - Real OHLCV data from Alpaca API
    - Strategy logic applied to historical bars
    - Realistic fill simulation
    - Performance metrics
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}  # symbol -> {qty, entry_price}
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(
        self,
        strategy_name: str,
        symbol: str,
        days: int = 365,
        params: dict = None
    ) -> dict:
        """
        Run backtest on REAL historical data from Yahoo Finance.
        """
        params = params or {}
        
        # Get real data from Yahoo Finance
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start=start_date, end=end_date, interval="1d")
        
        if hist.empty:
            return {"error": f"No data for {symbol}"}
        
        # Convert to list of dicts
        data = []
        for ts, row in hist.iterrows():
            data.append({
                'symbol': symbol,
                'timestamp': ts.isoformat(),
                'open': row['Open'],
                'high': row['High'],
                'low': row['Low'],
                'close': row['Close'],
                'volume': row['Volume']
            })
        
        # Sort by time
        data.sort(key=lambda x: x['timestamp'])
        
        print(f"Loaded {len(data)} days of {symbol} data")
        print(f"Date range: {data[0]['timestamp'][:10]} to {data[-1]['timestamp'][:10]}")
        print()
        
        # Get position size from params
        position_pct = params.get('position_pct', 0.10)
        
        for i, bar in enumerate(data):
            # Get signal
            signal = self._get_signal(strategy_name, bar, data, i, params)
            
            # Execute
            if signal == "buy" and bar['symbol'] not in self.positions:
                # Buy signal
                position_size = self.capital * position_pct
                shares = position_size / bar['close']
                
                self.capital -= position_size
                self.positions[bar['symbol']] = {
                    'qty': shares,
                    'entry_price': bar['close'],
                    'entry_bar': i
                }
                
                self.trades.append({
                    'type': 'buy',
                    'symbol': bar['symbol'],
                    'date': bar['timestamp'][:10],
                    'price': bar['close'],
                    'qty': shares
                })
                
            elif signal == "sell" and bar['symbol'] in self.positions:
                pos = self.positions[bar['symbol']]
                
                # Calculate PNL
                pnl = (bar['close'] - pos['entry_price']) * pos['qty']
                
                self.capital += pos['qty'] * bar['close']
                
                self.trades.append({
                    'type': 'sell',
                    'symbol': bar['symbol'],
                    'date': bar['timestamp'][:10],
                    'price': bar['close'],
                    'qty': pos['qty'],
                    'pnl': pnl,
                    'return': pnl / (pos['entry_price'] * pos['qty']) * 100
                })
                
                del self.positions[bar['symbol']]
            
            # Track equity
            position_value = sum(
                p['qty'] * bar['close'] 
                for p in self.positions.values()
            )
            self.equity_curve.append({
                'date': bar['timestamp'][:10],
                'equity': self.capital + position_value
            })
        
        # Close open positions at last price
        if self.positions:
            last_price = data[-1]['close']
            for symbol, pos in self.positions.items():
                pnl = (last_price - pos['entry_price']) * pos['qty']
                self.trades.append({
                    'type': 'close',
                    'symbol': symbol,
                    'date': data[-1]['timestamp'][:10],
                    'price': last_price,
                    'qty': pos['qty'],
                    'pnl': pnl
                })
            self.equity_curve[-1]['equity'] = self.capital
        
        return self._calculate_metrics()
    
    def _get_signal(
        self,
        strategy_name: str,
        bar: dict,
        data: list,
        i: int,
        params: dict
    ) -> Optional[str]:
        """Get trading signal from strategy."""
        if i < 20:
            return None
        
        if strategy_name == "momentum":
            return self._momentum_signal(bar, data, i, params)
        elif strategy_name == "mean_reversion":
            return self._mean_reversion_signal(bar, data, i, params)
        elif strategy_name == "trend_following":
            return self._trend_following_signal(bar, data, i, params)
        elif strategy_name == "buy_hold":
            if i == 20:  # Buy once
                return "buy"
            return None
        
        return None
    
    def _momentum_signal(self, bar: dict, data: list, i: int, params: dict) -> Optional[str]:
        """Momentum: Buy when price breaks above VWAP with volume confirmation."""
        # Calculate VWAP
        lookback = params.get('vwap_lookback', 20)
        start = max(0, i - lookback)
        
        pv_sum = sum(
            (d['high'] + d['low'] + d['close']) / 3 * d['volume']
            for d in data[start:i+1]
        )
        vol_sum = sum(d['volume'] for d in data[start:i+1])
        
        if vol_sum == 0:
            return None
        
        vwap = pv_sum / vol_sum
        
        # Volume confirmation
        avg_volume = sum(d['volume'] for d in data[start:i+1]) / len(data[start:i+1])
        volume_ratio = bar['volume'] / avg_volume if avg_volume > 0 else 1
        
        # RSI for momentum confirmation
        rsi = self._calculate_rsi(data, i, 14)
        
        # Signals
        buffer = params.get('vwap_buffer', 0.001)
        min_volume = params.get('min_volume_ratio', 1.2)
        min_rsi = params.get('min_rsi', 50)
        
        if (bar['close'] > vwap * (1 + buffer) and
            volume_ratio > min_volume and
            rsi > min_rsi):
            return "buy"
        
        # Exit if RSI overbought
        if rsi > 75:
            return "sell"
        
        return None
    
    def _mean_reversion_signal(self, bar: dict, data: list, i: int, params: dict) -> Optional[str]:
        """Mean reversion: Buy when oversold."""
        if i < 20:
            return None
        
        rsi = self._calculate_rsi(data, i, params.get('rsi_period', 14))
        oversold = params.get('rsi_oversold', 30)
        overbought = params.get('rsi_overbought', 70)
        
        if rsi < oversold:
            return "buy"
        elif rsi > overbought:
            return "sell"
        
        return None
    
    def _trend_following_signal(self, bar: dict, data: list, i: int, params: dict) -> Optional[str]:
        """Trend following: SMA crossover."""
        if i < 50:
            return None
        
        fast = params.get('sma_fast', 9)
        slow = params.get('sma_slow', 21)
        
        # Calculate SMAs
        fast_sma = sum(d['close'] for d in data[i-fast:i+1]) / fast
        slow_sma = sum(d['close'] for d in data[i-slow:i+1]) / slow
        
        # Previous values
        prev_fast = sum(d['close'] for d in data[i-fast-1:i]) / fast
        prev_slow = sum(d['close'] for d in data[i-slow-1:i]) / slow
        
        # Golden cross (fast crosses above slow)
        if prev_fast < prev_slow and fast_sma > slow_sma:
            return "buy"
        
        # Death cross
        if prev_fast > prev_slow and fast_sma < slow_sma:
            return "sell"
        
        return None
    
    def _calculate_rsi(self, data: list, i: int, period: int) -> float:
        """Calculate RSI."""
        if i < period:
            return 50
        
        start = i - period
        closes = [d['close'] for d in data[start:i+1]]
        
        gains = []
        losses = []
        for j in range(1, len(closes)):
            change = closes[j] - closes[j-1]
            if change > 0:
                gains.append(change)
            else:
                losses.append(abs(change))
        
        if not gains:
            return 50
        
        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses) if losses else 0.001
        
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    def _calculate_metrics(self) -> dict:
        """Calculate performance metrics."""
        if not self.equity_curve:
            return {"error": "No data"}
        
        # Total return
        initial = self.equity_curve[0]['equity']
        final = self.equity_curve[-1]['equity']
        total_return = (final - initial) / initial * 100
        
        # Annualized return
        days = len(self.equity_curve)
        years = days / 252
        annualized = ((final / initial) ** (1/years) - 1) * 100 if years > 0 else 0
        
        # Max drawdown
        peak = initial
        max_dd = 0
        for point in self.equity_curve:
            if point['equity'] > peak:
                peak = point['equity']
            dd = (peak - point['equity']) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Win rate
        closed_trades = [t for t in self.trades if t['type'] == 'sell']
        wins = [t for t in closed_trades if t.get('pnl', 0) > 0]
        win_rate = len(wins) / len(closed_trades) * 100 if closed_trades else 0
        
        # Average trade
        if closed_trades:
            avg_pnl = sum(t.get('pnl', 0) for t in closed_trades) / len(closed_trades)
        else:
            avg_pnl = 0
        
        return {
            'initial_capital': self.initial_capital,
            'final_equity': final,
            'total_return': total_return,
            'annualized_return': annualized,
            'max_drawdown': max_dd * 100,
            'total_trades': len(closed_trades),
            'winning_trades': len(wins),
            'losing_trades': len(closed_trades) - len(wins),
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'days': days,
            'equity_curve': self.equity_curve,
            'trades': self.trades
        }


def run_real_backtest(args):
    """Main backtest function."""
    print("=" * 60)
    print("REAL BACKTESTING WITH ALPACA HISTORICAL DATA")
    print("=" * 60)
    print()
    
    if args.strategy and args.symbol:
        # Single strategy/symbol
        strategies = {args.strategy: {}}
        symbols = [args.symbol]
    else:
        # All combinations
        strategies = {
            "momentum": {
                'vwap_buffer': 0.001,
                'vwap_lookback': 20,
                'min_volume_ratio': 1.2,
                'min_rsi': 50,
                'position_pct': 0.10
            },
            "trend_following": {
                'sma_fast': 9,
                'sma_slow': 21,
                'position_pct': 0.10
            },
            "mean_reversion": {
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'position_pct': 0.10
            }
        }
        symbols = args.symbols or ['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA']
    
    results = {}
    
    for strat_name in strategies:
        for symbol in symbols:
            key = f"{strat_name}_{symbol}"
            print(f"Testing {strat_name} on {symbol}...")
            
            bt = HistoricalBacktester(args.capital)
            result = bt.run_backtest(
                strat_name,
                symbol,
                args.days,
                strategies.get(strat_name, {})
            )
            
            if 'error' in result:
                print(f"  Error: {result['error']}")
                continue
            
            results[key] = result
            
            print(f"  Return: {result['total_return']:.2f}%")
            print(f"  Win Rate: {result['win_rate']:.1f}%")
            print(f"  Max DD: {result['max_drawdown']:.2f}%")
            print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if results:
        best = max(results.items(), key=lambda x: x[1]['total_return'])
        print(f"Best Strategy: {best[0]}")
        print(f"  Return: {best[1]['total_return']:.2f}%")
        print(f"  Win Rate: {best[1]['win_rate']:.1f}%")
        print()
        
        # Show all
        print("All Results:")
        for name, res in sorted(results.items(), key=lambda x: -x[1]['total_return']):
            emoji = "✅" if res['total_return'] > 0 and res['win_rate'] > 50 else "❌"
            print(f"  {emoji} {name}: {res['total_return']:+.2f}% ({res['win_rate']:.0f}% win rate)")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Real backtesting with Alpaca data')
    parser.add_argument('--strategy', type=str,
                       choices=['momentum', 'mean_reversion', 'trend_following', 'buy_hold'],
                       help='Strategy to test')
    parser.add_argument('--symbol', type=str,
                       help='Symbol to test')
    parser.add_argument('--symbols', nargs='+', default=['SPY', 'QQQ', 'AAPL', 'MSFT', 'NVDA'],
                       help='Symbols to test')
    parser.add_argument('--days', type=int, default=365,
                       help='Days of historical data')
    parser.add_argument('--capital', type=float, default=10000,
                       help='Initial capital')
    
    args = parser.parse_args()
    run_real_backtest(args)
