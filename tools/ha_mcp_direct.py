#!/usr/bin/env python3
"""
Direct interaction with Home Assistant MCP Server using raw SSE connection.

This script demonstrates direct connection to Home Assistant MCP Server
without relying on ADK's MCPToolset.
"""

import os
import json
import asyncio
import logging
import sys
import requests
from typing import Dict, Any, List, Optional
from pprint import pprint

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_ha_credentials():
    """Get Home Assistant credentials from environment variables."""
    ha_url = os.getenv("HA_MCP_SSE_URL")
    ha_token = os.getenv("HA_AUTH_TOKEN")
    
    if not ha_url or not ha_token:
        logger.error("Home Assistant MCP credentials missing.")
        logger.error("Please set HA_MCP_SSE_URL and HA_AUTH_TOKEN environment variables.")
        return None, None
    
    return ha_url, ha_token

def check_sse_connection():
    """Check if we can connect to the Home Assistant MCP SSE endpoint."""
    ha_url, ha_token = get_ha_credentials()
    
    if not ha_url or not ha_token:
        return {
            "success": False,
            "error": "Missing credentials"
        }
    
    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Accept": "text/event-stream"
    }
    
    try:
        # Make a GET request to check connectivity (some endpoints don't support HEAD)
        response = requests.get(ha_url, headers=headers, timeout=5, stream=True)
        # Just get headers and close connection, we don't need to read the full SSE stream
        response.close()
        
        return {
            "success": response.status_code < 400,
            "status_code": response.status_code,
            "status_message": response.reason
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def main():
    """Run the Home Assistant MCP direct connection test."""
    print("=" * 60)
    print(" Home Assistant MCP Direct Connection Test ".center(60, "="))
    print("=" * 60)
    
    # Check if credentials are available
    ha_url, ha_token = get_ha_credentials()
    if not ha_url or not ha_token:
        print("\n❌ Home Assistant MCP credentials missing!")
        print("Please set the following environment variables:")
        print("  HA_MCP_SSE_URL: URL to the Home Assistant MCP SSE endpoint")
        print("  HA_AUTH_TOKEN: Long-lived access token for Home Assistant")
        return 1
    
    print(f"\nHome Assistant MCP URL: {ha_url}")
    print(f"Home Assistant Auth Token: {'*' * 10}{ha_token[-5:]}")
    
    # Test direct SSE connection
    print("\nTesting direct connection to Home Assistant MCP SSE endpoint...")
    result = check_sse_connection()
    
    if result["success"]:
        print(f"\n✅ Direct connection successful!")
        print(f"Status: {result.get('status_code')} {result.get('status_message')}")
        
        # Print environment information
        print("\nEnvironment Information:")
        print(f"  Python version: {sys.version}")
        try:
            import google.adk
            print(f"  Google ADK version: {google.adk.__version__}")
        except (ImportError, AttributeError):
            print("  Google ADK: Not found or version not available")
    else:
        print(f"\n❌ Direct connection failed!")
        print(f"Error: {result.get('error', 'Unknown error')}")
        
        # Suggest next steps
        print("\nPossible issues:")
        print("  1. Home Assistant is not running or not accessible")
        print("  2. The MCP Server integration is not enabled")
        print("  3. The access token is invalid or expired")
        print("  4. Network or firewall issues")
        
        print("\nTroubleshooting steps:")
        print("  1. Check if Home Assistant is running")
        print("  2. Verify MCP Server integration is enabled in Home Assistant")
        print("  3. Generate a new long-lived access token")
        print("  4. Check if you can access Home Assistant in your browser")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())