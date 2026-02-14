#!/usr/bin/env python3
"""
Simple synchronous IBKR test
"""
import sys
import socket
import threading
import time

def test_socket_port():
    """Test if port is truly responsive"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    try:
        sock.connect(('127.0.0.1', 7497))
        # IBKR API sends initial message
        data = sock.recv(1024)
        sock.close()
        return True, data[:100]
    except Exception as e:
        sock.close()
        return False, str(e)

def test_port_5000():
    """Test Client Portal Gateway"""
    import http.client
    conn = http.client.HTTPConnection('127.0.0.1', 5000, timeout=3)
    try:
        conn.request('GET', '/')
        response = conn.getresponse()
        data = response.read()
        conn.close()
        return True, f"HTTP {response.status}"
    except Exception as e:
        conn.close()
        return False, str(e)

print("=" * 50)
print("IBKR Connection Diagnostic")
print("=" * 50)

# Test port 7497
print("\n1. Testing port 7497 (IB Gateway API)...")
success, msg = test_socket_port()
if success:
    print(f"   ✓ Port 7497: RESPONDING ({msg})")
else:
    print(f"   ✗ Port 7497: {msg}")

# Test port 5000
print("\n2. Testing port 5000 (Client Portal)...")
success, msg = test_port_5000()
if success:
    print(f"   ✓ Port 5000: {msg}")
else:
    print(f"   ✗ Port 5000: {msg}")

# Try ibapi
print("\n3. Testing ibapi...")
sys.path.insert(0, 'src')

try:
    from ibkr_client import IBKRClient
    
    client = IBKRClient()
    
    # Test with thread timeout
    result = [None]
    def connect_test():
        result[0] = client.connect(timeout=5)
    
    thread = threading.Thread(target=connect_test)
    thread.start()
    thread.join(timeout=8)
    
    if thread.is_alive():
        print("   ⚠ ibapi: TIMEOUT (Gateway may need restart)")
        print("   Note: IB Gateway may need to be restarted after API settings change")
    elif result[0]:
        print(f"   ✓ ibapi: CONNECTED")
        print(f"   Account: {client.account_id}")
        print(f"   Value: ${client.account_value:,.2f}")
        client.disconnect()
    else:
        print("   ✗ ibapi: FAILED")
        
except ImportError as e:
    print(f"   ✗ Import error: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 50)
print("If ibapi times out:")
print("1. RESTART IB Gateway completely")
print("2. Wait 30 seconds after restart")
print("3. Try again")
print("=" * 50)
