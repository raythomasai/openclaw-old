"""Learning module to track and optimize trading strategies."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional


class StrategyLearner:
    """
    Track signal performance and suggest optimizations.
    
    Learns from:
    - Which signals actually execute
    - Which signals are profitable
    - Which strategies perform best in current market conditions
    """
    
    def __init__(self, data_dir: str | Path | None = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / "data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.signals_file = self.data_dir / "signal_performance.json"
        self.load_signals()
    
    def load_signals(self) -> None:
        """Load historical signal data."""
        if self.signals_file.exists():
            with open(self.signals_file) as f:
                self.signals = json.load(f)
        else:
            self.signals = []
    
    def save_signals(self) -> None:
        """Save signal data."""
        with open(self.signals_file, "w") as f:
            json.dump(self.signals, f, indent=2)
    
    def record_signal(
        self,
        symbol: str,
        strategy: str,
        signal_type: str,
        confidence: float,
        executed: bool = False,
        pnl: float = 0.0
    ) -> None:
        """Record a signal for learning."""
        self.signals.append({
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "strategy": strategy,
            "signal_type": signal_type,
            "confidence": confidence,
            "executed": executed,
            "pnl": pnl,
            "day": datetime.now().strftime("%Y-%m-%d")
        })
        # Keep only last 1000 signals
        if len(self.signals) > 1000:
            self.signals = self.signals[-1000:]
        self.save_signals()
    
    def get_strategy_stats(self, days: int = 7) -> dict:
        """Get performance stats for each strategy."""
        cutoff = datetime.now() - timedelta(days=days)
        stats = defaultdict(lambda: {
            "signals": 0,
            "executed": 0,
            "profitable": 0,
            "total_pnl": 0.0,
            "confidence_sum": 0.0,
            "symbols": defaultdict(lambda: {"signals": 0, "pnl": 0.0})
        })
        
        for s in self.signals:
            s_time = datetime.fromisoformat(s["timestamp"])
            if s_time < cutoff:
                continue
            
            strat = s["strategy"]
            stats[strat]["signals"] += 1
            stats[strat]["confidence_sum"] += s["confidence"]
            
            if s["executed"]:
                stats[strat]["executed"] += 1
                if s["pnl"] > 0:
                    stats[strat]["profitable"] += 1
                stats[strat]["total_pnl"] += s["pnl"]
            
            stats[strat]["symbols"][s["symbol"]]["signals"] += 1
            stats[strat]["symbols"][s["symbol"]]["pnl"] += s["pnl"]
        
        # Format results
        results = {}
        for name, data in stats.items():
            executed = data["executed"] or 1  # Avoid divide by zero
            results[name] = {
                "signals_generated": data["signals"],
                "signals_executed": data["executed"],
                "win_rate": (data["profitable"] / executed) * 100 if executed > 0 else 0,
                "total_pnl": data["total_pnl"],
                "avg_confidence": data["confidence_sum"] / data["signals"] if data["signals"] > 0 else 0,
                "best_symbol": max(data["symbols"].items(), key=lambda x: x[1]["pnl"])[0] if data["symbols"] else None,
                "worst_symbol": min(data["symbols"].items(), key=lambda x: x[1]["pnl"])[0] if data["symbols"] else None
            }
        
        return results
    
    def get_recommendations(self) -> list[str]:
        """Generate optimization recommendations."""
        recommendations = []
        stats = self.get_strategy_stats(days=3)
        
        for name, data in stats.items():
            if data["signals_generated"] < 5:
                continue
            
            # Low win rate
            if data["win_rate"] < 40:
                recommendations.append(
                    f"[{name}] Low win rate ({data['win_rate']:.1f}%) - consider tightening entry criteria"
                )
            
            # High confidence but low execution
            if data["signals_generated"] > 10 and data["signals_executed"] == 0:
                recommendations.append(
                    f"[{name}] Signals not executing - check if position limits are blocking"
                )
            
            # Unprofitable
            if data["total_pnl"] < 0:
                recommendations.append(
                    f"[{name}] Unprofitable (${data['total_pnl']:.2f}) - review stop losses"
                )
        
        return recommendations
    
    def get_best_performing_symbols(self, limit: int = 5) -> list[str]:
        """Get symbols with best recent performance."""
        stats = self.get_strategy_stats(days=7)
        
        symbol_pnl = defaultdict(float)
        for strat_data in stats.values():
            for symbol, data in strat_data.get("symbols", {}).items():
                symbol_pnl[symbol] += data["pnl"]
        
        sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1], reverse=True)
        return [s[0] for s in sorted_symbols[:limit]]
    
    def get_worst_performing_symbols(self, limit: int = 5) -> list[str]:
        """Get symbols with worst recent performance."""
        stats = self.get_strategy_stats(days=7)
        
        symbol_pnl = defaultdict(float)
        for strat_data in stats.values():
            for symbol, data in strat_data.get("symbols", {}).items():
                symbol_pnl[symbol] += data["pnl"]
        
        sorted_symbols = sorted(symbol_pnl.items(), key=lambda x: x[1])
        return [s[0] for s in sorted_symbols[:limit]]


if __name__ == "__main__":
    learner = StrategyLearner()
    print("Strategy Stats:")
    stats = learner.get_strategy_stats()
    for name, data in stats.items():
        print(f"  {name}: {data}")
    
    print("\nRecommendations:")
    for rec in learner.get_recommendations():
        print(f"  - {rec}")
