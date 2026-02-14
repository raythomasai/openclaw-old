#!/usr/bin/env python3
"""Quick IBKR connection test with timeout"""

import sys
import threading
import time

sys.path.insert(0, 'src')

def test_connection():
    from ibkr_client import IBKRClient
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("Testing IBKR connection...")
    client = IBKRClient()
    
    if client.connect(timeout=8):
        print(f"\n✓ CONNECTED!")
        print(f"  Account: {client.account_id}")
        print(f"  Value: ${client.account_value:,.2f}")
        print(f"  Cash: ${client.cash:,.2f}")
        print(f"  Positions: {len(client.positions)}")
        client.disconnect()
        print("\n✓ SUCCESS - IBKR is ready!")
        return True
    else:
        print("\n✗ FAILED - Could not connect")
        return False

if __name__ == "__main__":
    result = [None]
    
    def run_test():
        result[0] = test_connection()
    
    thread = threading.Thread(target=run_test)
    thread.start()
    thread.join(timeout=12)
    
    if thread.is_alive():
        print("\n✗ TIMEOUT - Connection is hanging")
        sys.exit(1)
    elif result[0]:
        sys.exit(0)
    else:
        sys.exit(1)
