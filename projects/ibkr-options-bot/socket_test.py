#!/usr/bin/env python3
"""
Synchronous IBKR test - no threading, just socket
"""
import socket
import select
import sys

def send_message(sock, msg):
    """Send message and wait for response"""
    try:
        sock.sendall(msg.encode())
        
        # Wait for response with timeout
        ready = select.select([sock], [], [], 2)
        if ready[0]:
            return sock.recv(4096).decode()
        return None
    except Exception as e:
        return f"Error: {e}"

def main():
    print("=" * 50)
    print("IBKR Socket Test")
    print("=" * 50)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(5)
    
    print("\n1. Connecting to 127.0.0.1:7497...")
    try:
        sock.connect(('127.0.0.1', 7497))
        print("   ✓ Connected")
        
        # IBKR API expects API version message first
        print("\n2. Sending API version...")
        response = send_message(sock, "APIv100\n")
        if response:
            print(f"   Response: {response[:100]}")
        else:
            print("   No response (socket open but silent)")
        
        print("\n3. Checking connection...")
        # Try sending another message
        response = send_message(sock, "\n")
        if response:
            print(f"   Response: {response[:100]}")
        
        print("\n✓ Socket connection works!")
        print("   Note: Full ibapi functionality requires")
        print("   proper message handling library.")
        
    except Exception as e:
        print(f"   ✗ Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    main()
