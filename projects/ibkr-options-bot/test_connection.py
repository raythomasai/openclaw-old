#!/usr/bin/env python3
"""Test IBKR connection - run this first to verify connection"""

import asyncio
import sys
from pathlib import Path

# Fix event loop FIRST before any ib_insync imports
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import nest_asyncio
nest_asyncio.apply()

# Now import ib_insync
from ib_insync import IB

def test_connection():
    """Test IBKR connection"""
    print("Testing IB Gateway connection...")
    print(f"Python: {sys.version}")
    print(f"IB Gateway should be running on port 7497 (paper)")
    
    ib = IB()
    
    try:
        print("Connecting...")
        # Use blocking connect with timeout
        ib.connect('127.0.0.1', 7497, clientId=1, timeout=10)
        
        print(f"✓ Connected!")
        print(f"  Account: {ib.client.accountId}")
        print(f"  Server version: {ib.client.serverVersion()}")
        print(f"  Connection time: {ib.client.twsConnectionTime()}")
        
        # Get account summary
        summary = ib.accountSummary()
        for item in summary:
            if item.tag == 'NetLiquidation':
                print(f"  Portfolio Value: ${float(item.value):,.2f}")
            elif item.tag == 'CashBalance':
                print(f"  Cash: ${float(item.value):,.2f}")
        
        # Test a quote
        print("\nTesting quote for AAPL...")
        contract = IB.Stock('AAPL', 'SMART', 'USD')
        ticker = ib.reqMktData(contract, '', False, False)
        import time
        time.sleep(0.5)
        if ticker.last:
            print(f"  AAPL: ${ticker.last:.2f}")
        else:
            print(f"  AAPL: Bid ${ticker.bid:.2f} / Ask ${ticker.ask:.2f}")
        
        ib.disconnect()
        print("\n✓ Connection test passed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure IB Gateway is running")
        print("2. Verify you're logged in to paper account")
        print("3. Check API settings: Enable Socket Clients")
        print("4. Verify port 7497 is open")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
