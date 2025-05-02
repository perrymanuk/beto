#!/usr/bin/env python3
"""
Test script for Home Assistant entity state retrieval.

This script tests the Home Assistant MCP integration by attempting to
retrieve the state of a specified entity.
"""

import os
import sys
import logging
import argparse
from dotenv import load_dotenv

from raderbot.tools.mcp_utils import test_home_assistant_connection
from raderbot.tools.mcp_utils import check_home_assistant_entity
from raderbot.tools.mcp_utils import list_home_assistant_domains

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """Test Home Assistant entity state retrieval."""
    parser = argparse.ArgumentParser(description="Test Home Assistant entity state retrieval")
    parser.add_argument("entity_id", nargs="?", help="Entity ID to check (e.g., sensor.living_room_temperature)")
    parser.add_argument("--list-domains", action="store_true", help="List available Home Assistant domains")
    args = parser.parse_args()

    print("=" * 60)
    print("Home Assistant Entity Test".center(60))
    print("=" * 60)
    
    # Test the general connection first
    print("\nTesting Home Assistant MCP connection...")
    ha_result = test_home_assistant_connection()
    
    if ha_result["success"]:
        print(f"✅ Connected to Home Assistant MCP server")
        print(f"Found {ha_result.get('tools_count', 0)} tools")
        
        # List domains if requested
        if args.list_domains:
            domains_result = list_home_assistant_domains()
            if domains_result["success"]:
                print("\nAvailable domains:")
                for domain in domains_result.get("domains", []):
                    print(f"- {domain}")
            else:
                print(f"\n❌ Failed to list domains")
                print(f"Error: {domains_result.get('error', 'Unknown error')}")
        
        # Check entity state if provided
        if args.entity_id:
            print(f"\nChecking entity state for: {args.entity_id}")
            entity_result = check_home_assistant_entity(args.entity_id)
            
            if entity_result["success"]:
                print("✅ Entity found")
                print(f"Domain: {entity_result.get('domain', 'unknown')}")
                
                if "state" in entity_result:
                    print(f"State: {entity_result['state']}")
                else:
                    print("State: Not available")
                    
                print("Details:")
                print(f"- {entity_result.get('details', 'No details available')}")
            else:
                print("❌ Entity check failed")
                print(f"Status: {entity_result.get('status', 'unknown')}")
                print(f"Error: {entity_result.get('error', 'Unknown error')}")
        elif not args.list_domains:
            print("\nNo entity ID provided. Use --list-domains to see available domains")
            print("or provide an entity ID to check its state.")
    else:
        print(f"❌ Failed to connect to Home Assistant MCP server")
        print(f"Error: {ha_result.get('error', 'Unknown error')}")
        print("\nPlease check your Home Assistant MCP configuration in .env file:")
        print("- HA_MCP_SSE_URL should point to your Home Assistant MCP Server SSE endpoint")
        print("- HA_AUTH_TOKEN should contain a valid long-lived access token")

if __name__ == "__main__":
    main()