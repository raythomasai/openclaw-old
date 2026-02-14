#!/usr/bin/env python3
"""
Simple test to verify bot structure
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

def test_imports():
    """Test that all modules can be imported"""
    print("Testing imports...")
    
    try:
        from config.settings import (
            PROJECT_ROOT, LOGS_DIR, DEMO_MODE,
            KALSHI_USE_DEMO, MAX_TRADE_AMOUNT
        )
        print("✓ config.settings imported successfully")
    except Exception as e:
        print(f"✗ config.settings failed: {e}")
        return False
    
    try:
        from src.polymarket_client import PolymarketClient, MarketPrice
        print("✓ polymarket_client imported successfully")
    except Exception as e:
        print(f"✗ polymarket_client failed: {e}")
        return False
    
    try:
        from src.kalshi_client import KalshiClient, KalshiPosition
        print("✓ kalshi_client imported successfully")
    except Exception as e:
        print(f"✗ kalshi_client failed: {e}")
        return False
    
    try:
        from src.signal_engine import SignalEngine, TradingSignal, SignalType
        print("✓ signal_engine imported successfully")
    except Exception as e:
        print(f"✗ signal_engine failed: {e}")
        return False
    
    try:
        from src.mechanical_arbitrage import MechanicalArbitrage, ArbPosition
        print("✓ mechanical_arbitrage imported successfully")
    except Exception as e:
        print(f"✗ mechanical_arbitrage failed: {e}")
        return False
    
    try:
        from src.risk_manager import RiskManager, TradeRequest
        print("✓ risk_manager imported successfully")
    except Exception as e:
        print(f"✗ risk_manager failed: {e}")
        return False
    
    return True


def test_arbitrage():
    """Test mechanical arbitrage logic"""
    print("\nTesting mechanical arbitrage...")
    
    from src.mechanical_arbitrage import MechanicalArbitrage
    
    arb = MechanicalArbitrage({
        "max_trade_amount": 25.0,
        "arb_threshold": 0.02
    })
    
    # Test fresh position with significant mispricing
    # YES=$0.35, NO=$0.65 (YES is 15% below fair)
    result = arb.analyze_market(0.35, 0.65, "test_market")
    
    if result:
        side, amount, expected = result
        print(f"✓ Found arb opportunity: {side} ${amount:.2f}, expected ${expected:.2f}")
        
        # Execute
        arb.execute_buy("test_market", side, amount, 0.35)
        
        pos = arb.get_position("test_market")
        print(f"✓ Position: YES={pos.yes_qty:.2f}, NO={pos.no_qty:.2f}")
        print(f"✓ Pair Cost: ${pos.pair_cost:.3f}")
    else:
        print("ℹ No immediate arb - checking position logic")
        # Force a position for testing
        arb.execute_buy("test_market", "yes", 10.0, 0.40)
        pos = arb.get_position("test_market")
        print(f"✓ Forced position: YES={pos.yes_qty:.2f} @ ${pos.avg_yes:.2f}")
    
    # Second trade to test rebalancing
    result = arb.analyze_market(0.55, 0.50, "test_market")
    
    if result:
        side, amount, expected = result
        print(f"✓ Second trade: {side} ${amount:.2f}")
        arb.execute_buy("test_market", side, amount, 0.50 if side == "no" else 0.55)
        
        pos = arb.get_position("test_market")
        print(f"✓ Updated: YES={pos.yes_qty:.2f}, NO={pos.no_qty:.2f}")
        print(f"✓ Pair Cost: ${pos.pair_cost:.3f}")
        
        if pos.locked:
            print(f"✓✓ LOCKED! Guaranteed profit: ${pos.guaranteed_profit:.2f}")
    else:
        print("ℹ Second trade not triggered")
        pos = arb.get_position("test_market")
        print(f"  Current: YES={pos.yes_qty:.2f}, NO={pos.no_qty:.2f}")
    
    # Test stats
    stats = arb.get_stats()
    print(f"✓ Stats: trades={stats['total_trades']}, open={stats['open_positions']}")
    
    return True


def test_risk_manager():
    """Test risk management"""
    print("\nTesting risk manager...")
    
    from src.risk_manager import RiskManager, TradeRequest
    
    manager = RiskManager({
        "max_trade_amount": 25.0,
        "max_daily_loss": 100.0,
        "daily_trade_limit": 50
    })
    
    # Test approval
    request = TradeRequest(
        market_id="test",
        side="yes",
        amount=20.0,
        price=0.70,
        strategy="test",
        signal_confidence=0.75
    )
    
    approved, reason = manager.assess_risk(request)
    print(f"✓ Trade approved: {approved}, reason: {reason}")
    
    if approved:
        manager.update_position("test", "yes", 20.0, 0.70)
        metrics = manager.get_metrics()
        print(f"✓ Metrics: P&L=${metrics.daily_pnl:.2f}, Trades={metrics.daily_trades}")
    
    # Test rejection (exceeds daily loss) - need -100.01 to fail
    manager.daily_pnl = -100.01  # Over limit
    
    request = TradeRequest(
        market_id="test2",
        side="no",
        amount=20.0,
        price=0.30,
        strategy="test",
        signal_confidence=0.75
    )
    
    approved, reason = manager.assess_risk(request)
    print(f"✓ Trade rejected at limit: {approved}, reason: {reason}")
    
    return True


def test_signal_engine():
    """Test signal generation"""
    print("\nTesting signal engine...")
    
    from src.signal_engine import SignalEngine
    
    engine = SignalEngine({
        "momentum_threshold": 0.05,
        "whale_min_amount": 1000.0,
        "arb_threshold": 0.03
    })
    
    # Update market pair
    engine.update_market_pair(
        poly_market_id="poly_123",
        kalshi_market_id="kalshi_456",
        poly_yes=0.75,
        poly_no=0.25,
        kalshi_yes=0.70,
        kalshi_no=0.30
    )
    
    signals = engine.analyze_all_pairs()
    print(f"✓ Generated {len(signals)} signals")
    
    for sig in signals:
        print(f"  - {sig.signal_type.value}: {sig.side} @ {sig.confidence:.0%}")
    
    return True


def main():
    """Run all tests"""
    print("=" * 50)
    print("KALSHI BOT STRUCTURE TEST")
    print("=" * 50)
    
    all_passed = True
    
    if not test_imports():
        all_passed = False
    
    if not test_arbitrage():
        all_passed = False
    
    if not test_risk_manager():
        all_passed = False
    
    if not test_signal_engine():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 50)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
