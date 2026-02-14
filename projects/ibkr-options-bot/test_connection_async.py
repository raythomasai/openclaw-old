#!/usr/bin/env python3
"""Test IBKR connection using async approach"""

import asyncio
import sys
from pathlib import Path

# Fix event loop FIRST
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import nest_asyncio
nest_asyncio.apply()

async def test():
    from ib_insync import IB
    
    print("Testing IB Gateway connection (async mode)...")
    ib = IB()
    
    try:
        # Run in executor to avoid event loop issues
        loop = asyncio.get_event_loop()
        
        def connect_sync():
            ib.connect('127.0.0.1', 7497, clientId=1)
        
        await asyncio.wait_for(
            loop.run_in_executor(None, connect_sync),
            timeout=15.0
        )
        
        print(f"✓ Connected!")
        print(f"  Account: {ib.client.accountId}")
        
        # Get account summary
        summary = ib.accountSummary()
        for item in summary:
            if item.tag == 'NetLiquidation':
                print(f"  Portfolio Value: ${float(item.value):,.2f}")
            elif item.tag == 'CashBalance':
                print(f"  Cash: ${float(item.value):,.2f}")
        
        ib.disconnect()
        return True
        
    except asyncio.TimeoutError:
        print("✗ Connection timed out - IB Gateway not responding")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
