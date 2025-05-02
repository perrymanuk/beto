#!/usr/bin/env python3
"""
Test the Home Assistant entity search functionality.

This script tests the entity search function for Home Assistant integration.
"""

import os
import sys
import logging
from pprint import pprint
import json

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

def verify_ha_config():
    """Verify that Home Assistant configuration is available."""
    from raderbot.tools.mcp_utils import test_home_assistant_connection
    
    # Check environment variables
    ha_url = os.getenv("HA_MCP_SSE_URL")
    ha_token = os.getenv("HA_AUTH_TOKEN")
    
    if not ha_url or not ha_token:
        print("❌ Missing environment variables:")
        if not ha_url:
            print("  - HA_MCP_SSE_URL is not set")
        if not ha_token:
            print("  - HA_AUTH_TOKEN is not set")
        print("\nPlease set these in your .env file and try again.")
        return False
    
    # Test connection
    print("Testing Home Assistant MCP connection...")
    result = test_home_assistant_connection()
    
    if not result.get("success"):
        print(f"❌ Connection failed: {result.get('error', 'Unknown error')}")
        print(f"  Status: {result.get('status', 'unknown')}")
        return False
    
    # Print connection information
    print(f"✅ Connected to Home Assistant MCP")
    print(f"  Found {result.get('tools_count', 0)} tools")
    
    if result.get("detected_domains"):
        print(f"  Detected domains: {', '.join(result['detected_domains'])}")
    
    return True

def main():
    """Run the entity search test."""
    print("=" * 60)
    print(" Home Assistant Entity Search Test ".center(60, "="))
    print("=" * 60)
    
    # First verify Home Assistant configuration
    if not verify_ha_config():
        print("\n⚠️  Skipping tests due to configuration issues")
        return 1
    
    # Import after configuration check to avoid errors if not configured
    from raderbot.tools.mcp_utils import find_home_assistant_entities
    
    # You can customize these search terms
    search_terms = [
        "basement",
        "plant",
        "light",
        "basement plant",
        "living room"
    ]
    
    test_results = []
    
    for term in search_terms:
        print(f"\nSearching for: \"{term}\"")
        print("-" * 40)
        
        try:
            # Search without domain filter
            result = find_home_assistant_entities(term)
            
            # Store test result
            test_case = {
                "search_term": term,
                "domain_filter": None,
                "success": result.get("success", False),
                "match_count": result.get("match_count", 0),
                "error": result.get("error") if not result.get("success") else None
            }
            test_results.append(test_case)
            
            if result.get("success"):
                match_count = result.get("match_count", 0)
                print(f"✅ Found {match_count} matches")
                
                if match_count > 0:
                    print("\nTop matches:")
                    for i, match in enumerate(result.get("matches", [])[:5]):
                        print(f"  {i+1}. {match['entity_id']} (score: {match['score']})")
                else:
                    print("No matches found")
            else:
                print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
            
            # Now try with domain filter for lights
            if term != "light":  # Skip "light" term for light domain filter to avoid confusion
                print(f"\nSearching for: \"{term}\" in domain: light")
                print("-" * 40)
                
                try:
                    light_result = find_home_assistant_entities(term, domain_filter="light")
                    
                    # Store test result
                    test_case = {
                        "search_term": term,
                        "domain_filter": "light",
                        "success": light_result.get("success", False),
                        "match_count": light_result.get("match_count", 0),
                        "error": light_result.get("error") if not light_result.get("success") else None
                    }
                    test_results.append(test_case)
                    
                    if light_result.get("success"):
                        match_count = light_result.get("match_count", 0)
                        print(f"✅ Found {match_count} light matches")
                        
                        if match_count > 0:
                            print("\nTop light matches:")
                            for i, match in enumerate(light_result.get("matches", [])[:5]):
                                print(f"  {i+1}. {match['entity_id']} (score: {match['score']})")
                        else:
                            print("No light matches found")
                    else:
                        print(f"❌ Light search failed: {light_result.get('error', 'Unknown error')}")
                except Exception as e:
                    print(f"❌ Error during light search: {str(e)}")
        except Exception as e:
            print(f"❌ Error during search: {str(e)}")
    
    # Print test summary
    success_count = sum(1 for result in test_results if result["success"])
    total_count = len(test_results)
    
    print("\n" + "=" * 60)
    print(" Test Summary ".center(60, "="))
    print("=" * 60)
    print(f"Total tests: {total_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {total_count - success_count}")
    
    # If there are failures, show details
    if success_count < total_count:
        print("\nFailure details:")
        for i, result in enumerate([r for r in test_results if not r["success"]]):
            domain = f" (domain: {result['domain_filter']})" if result["domain_filter"] else ""
            print(f"  {i+1}. Term: \"{result['search_term']}\"{domain}")
            print(f"     Error: {result['error']}")
    
    return 0 if success_count == total_count else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(1)