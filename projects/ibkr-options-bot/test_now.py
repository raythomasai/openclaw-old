#!/usr/bin/env python3
"""Simple IBKR connection test"""
import sys
import socket
import time

print("=" * 50)
print("IBKR Connection Test")
print("=" * 50)

# Test 1: Port is open
print("\n1. Checking port 7497...")
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(2)
result = sock.connect_ex(('127.0.0.1', 7497))
sock.close()

if result == 0:
    print("   ✓ Port 7497 is OPEN")
else:
    print("   ✗ Port 7497 is CLOSED")
    sys.exit(1)

# Test 2: Try ibapi connection
print("\n2. Testing ibapi connection...")
try:
    sys.path.insert(0, 'src')
    from ibkr_client import IBKRClient
    
    client = IBKRClient()
    if client.connect():
        print(f"   ✓ CONNECTED!")
        print(f"   Account: {client.account_id}")
        print(f"   Value: ${client.account_value:,.2f}")
        print(f"   Cash: ${client.cash:,.2f}")
        client.disconnect()
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED - Bot is ready to trade!")
        print("=" * 50)
    else:
        print("   ✗ Connection failed")
        sys.exit(1)
        
except ImportError as e:
    print(f"   ✗ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)
