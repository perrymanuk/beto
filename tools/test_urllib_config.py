#!/usr/bin/env python3
"""
Test urllib configuration to debug connectivity issues.
"""

import urllib.request
import ssl
import os
import socket
import contextlib
import traceback

def detailed_connection_test(url):
    """Run a detailed connection test with verbose error reporting."""
    print(f"\nDetailed connection test for {url}")
    print("-" * 50)
    
    # Parse URL
    if "://" not in url:
        scheme = "http"
        host_part = url
    else:
        scheme, host_part = url.split("://", 1)
    
    # Extract host and port
    if ":" in host_part:
        host, port_str = host_part.split(":", 1)
        if "/" in port_str:
            port_str = port_str.split("/", 1)[0]
        port = int(port_str)
    else:
        host = host_part.split("/", 1)[0]
        port = 443 if scheme == "https" else 80
    
    # Print DNS resolution
    print(f"DNS resolution for {host}:")
    try:
        ip_address = socket.gethostbyname(host)
        print(f"  Resolved to: {ip_address}")
    except socket.gaierror as e:
        print(f"  DNS resolution failed: {e}")
    
    # Raw socket test
    print(f"\nRaw socket test to {host}:{port}:")
    try:
        with contextlib.closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.settimeout(5)
            sock.connect((host, port))
            print(f"  Socket connection successful!")
            # For HTTP, try a basic request
            if scheme == "http":
                try:
                    sock.send(b"GET / HTTP/1.1\r\nHost: " + host.encode() + b"\r\n\r\n")
                    response = sock.recv(1024)
                    print(f"  Got HTTP response: {response[:100]}")
                except Exception as e:
                    print(f"  Basic HTTP request failed: {e}")
    except Exception as e:
        print(f"  Socket connection failed: {e}")
        print(f"  Error type: {type(e).__name__}")
    
    # Full urllib request
    print(f"\nFull urllib request to {url}:")
    try:
        # Check if urllib is using a proxy
        proxies = {
            'http': os.environ.get('HTTP_PROXY'),
            'https': os.environ.get('HTTPS_PROXY')
        }
        print(f"  Proxy settings: {proxies}")
        
        # Try the request with detailed error handling
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                content = response.read(100)  # Read only the first 100 bytes
                print(f"  Request successful! Status: {response.status}")
                print(f"  Response: {content}")
        except urllib.error.URLError as e:
            print(f"  URLError: {e}")
            if hasattr(e, 'reason') and isinstance(e.reason, ssl.SSLError):
                print(f"  SSL Error: {e.reason}")
            if hasattr(e, 'reason'):
                print(f"  Reason type: {type(e.reason).__name__}")
                print(f"  Reason: {e.reason}")
            if hasattr(e, 'errno') and e.errno:
                print(f"  Errno: {e.errno}")
            traceback.print_exc()
        except Exception as e:
            print(f"  Other exception: {e}")
            print(f"  Exception type: {type(e).__name__}")
            traceback.print_exc()
    except Exception as e:
        print(f"  Setup error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    # Test both DNS name and IP with explicit port
    detailed_connection_test("http://qdrant.service.consul:6333")
    detailed_connection_test("http://192.168.50.120:6333")