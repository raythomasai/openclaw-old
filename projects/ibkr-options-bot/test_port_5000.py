#!/usr/bin/env python3
"""Test IBKR connection on port 5000"""

import asyncio
import sys

# Fix event loop
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import nest_asyncio
nest_asyncio.apply()

from ib_insync import IB

def test_port_5000():
    """Test connection on port 5000"""
    print("Testing IBKR connection on port 5000...")
    ib = IB()
    
    try:
        # Connect with explicit host and port
        ib.connect('127.0.0.1', 5000, clientId=1, timeout=10)
        
        print(f"✓ Connected!")
        print(f"  Account: {ib.client.accountId}")
        print(f"  Server Version: {ib.client.serverVersion()}")
        print(f"  Connection Time: {ib.client.twsConnectionTime()}")
        
        # Get account summary
        summary = ib.accountSummary()
        for item in summary:
            if item.tag == 'NetLiquidation':
                print(f"  Portfolio Value: ${float(item.value):,.2f}")
            elif item.tag == 'CashBalance':
                print(f"  Cash: ${float(item.value):,.2f}")
        
        ib.disconnect()
        print("\n✓ Connection successful!")
        return True
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_port_5000()
    sys.exit(0 if success else 1)
