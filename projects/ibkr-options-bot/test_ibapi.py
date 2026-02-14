#!/usr/bin/env python3
"""
Simplified IBKR connection test using ibapi
"""

import sys
import time
import threading
from queue import Queue

sys.path.insert(0, 'src')

from ibapi.wrapper import EWrapper
from ibapi.client import EClient

class TestApp(EWrapper, EClient):
    def __init__(self):
        EWrapper.__init__(self)
        EClient.__init__(self, wrapper=self)
        self.connected = False
        self.account_id = None
        self.messages = Queue()
        
    def error(self, reqId, errorCode, errorString, advancedOrderRejectJson=""):
        print(f"  Error {errorCode}: {errorString}")
        
    def connectionClosed(self):
        print("  Connection closed")
        
    def connectAck(self):
        print("  Connection acknowledged!")
        self.connected = True
        
    def accountSummary(self, reqId, account, tag, value, currency):
        self.messages.put({'type': 'account', 'tag': tag, 'value': value})
        
    def accountSummaryEnd(self, reqId):
        self.messages.put({'type': 'done'})
        
    def managedAccounts(self, accountsList):
        print(f"  Managed accounts: {accountsList}")
        self.account_id = accountsList

def main():
    print("=" * 50)
    print("IBKR Connection Test")
    print("=" * 50)
    
    app = TestApp()
    
    print("\nConnecting to 127.0.0.1:7497...")
    app.connect("127.0.0.1", 7497, clientId=1)
    
    # Start message loop
    thread = threading.Thread(target=app.run, daemon=True)
    thread.start()
    
    # Wait
    print("Waiting...")
    time.sleep(4)
    
    if app.connected:
        print(f"\n✓ CONNECTED!")
        print(f"  Account: {app.account_id}")
        
        # Get account data
        print("\nFetching account data...")
        app.reqAccountSummary(1, "All", "NetLiquidation,CashBalance")
        time.sleep(2)
        
        while not app.messages.empty():
            msg = app.messages.get()
            if msg['type'] == 'account':
                print(f"  {msg['tag']}: {msg['value']}")
        
        print("\n✓ SUCCESS!")
        app.disconnect()
    else:
        print("\n✗ Not connected")
        print("  IB Gateway may need more time or restart")

if __name__ == "__main__":
    main()
