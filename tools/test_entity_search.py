#!/usr/bin/env python3
"""
Test the Home Assistant entity search functionality with WebSocket and display registry.

This script tests the improved entity search functionality that uses the
Home Assistant WebSocket API and entity registry display information.
"""

import asyncio
import os
import sys
import logging
from pprint import pprint
import json
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import radbot modules
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

# Default Home Assistant WebSocket URL
DEFAULT_HA_WS_URL = "ws://localhost:8123/api/websocket"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f" {title} ".center(70, "="))
    print("=" * 70)

def print_subheader(title):
    """Print a formatted subheader."""
    print("\n" + "-" * 60)
    print(f" {title} ")
    print("-" * 60)

async def update_state_callback(event_data: Dict[str, Any]) -> None:
    """Dummy callback for state updates during testing."""
    # Not used in this test, but required for the WebSocket client
    pass

async def test_websocket_entity_search():
    """Test the improved entity search functionality with WebSocket."""
    from radbot.tools.ha_websocket_client import HomeAssistantWebsocketClient
    from radbot.tools.ha_state_cache import HomeAssistantStateCache

    # Check environment variables
    ha_ws_url = os.getenv("HA_WS_URL", DEFAULT_HA_WS_URL)
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_token:
        print("❌ HA_TOKEN environment variable is not set")
        print("Please set this in your .env file or directly in your environment and try again.")
        return False
    
    print_header("Home Assistant WebSocket Entity Search Test")
    print(f"Connecting to Home Assistant at {ha_ws_url}")
    
    ws_client = None
    state_cache = HomeAssistantStateCache()
    
    try:
        # Connect to Home Assistant
        ws_client = HomeAssistantWebsocketClient(ha_ws_url, ha_token, update_state_callback)
        
        # Connect without starting the listener yet
        connection_result = await ws_client.connect(auto_listen=False)
        if not connection_result:
            print("❌ Failed to connect to Home Assistant")
            return False
        
        print("✅ Connected to Home Assistant WebSocket API")
        
        # Initialize with all states
        print("Fetching all entity states...")
        all_states = await ws_client.get_all_states()
        print(f"✅ Received {len(all_states)} entities from Home Assistant")
        
        # Process each state into the cache
        for state_data in all_states:
            entity_id = state_data.get("entity_id")
            if entity_id:
                event_data = {"entity_id": entity_id, "new_state": state_data}
                await state_cache.update_state(event_data)
        
        # Fetch enhanced registry data
        print("Fetching registry display information...")
        try:
            entity_registry_display = await ws_client.get_entity_registry_for_display()
            print(f"✅ Received {len(entity_registry_display)} display registry entries")
            await state_cache.update_entity_registry_display(entity_registry_display)
        except Exception as display_error:
            print(f"❌ Error fetching display registry: {display_error}")
            
            # Fall back to regular registry
            print("Falling back to standard registry...")
            entity_registry = await ws_client.get_entity_registry()
            print(f"✅ Received {len(entity_registry)} standard registry entries")
            await state_cache.update_entity_registry(entity_registry)
        
        # Get device registry for additional context
        print("Fetching device registry...")
        device_registry = await ws_client.get_device_registry()
        print(f"✅ Received {len(device_registry)} device registry entries")
        await state_cache.update_device_registry(device_registry)
        
        # Get available domains for context
        domains = await state_cache.get_domains()
        print(f"Available domains: {', '.join(domains[:10])}{'...' if len(domains) > 10 else ''}")
        
        # Define test searches to evaluate the improved search functionality
        test_searches = [
            {"term": "light", "domain": None, "description": "Basic domain search"},
            {"term": "living room", "domain": None, "description": "Location search"},
            {"term": "temperature", "domain": None, "description": "Attribute search"},
            {"term": "motion", "domain": None, "description": "Feature search"},
            {"term": "door", "domain": None, "description": "Device type search"},
            {"term": "upstairs", "domain": None, "description": "Area search"},
            {"term": "kitchen light", "domain": None, "description": "Combined location + device"},
            {"term": "bathroom", "domain": "light", "description": "Location with domain filter"},
            {"term": "temp", "domain": "sensor", "description": "Abbreviated term with domain filter"},
        ]
        
        # Run tests and collect results
        test_results = []
        
        for test_case in test_searches:
            term = test_case["term"]
            domain = test_case["domain"]
            description = test_case["description"]
            
            print_subheader(f"Search for '{term}' {f'in domain {domain}' if domain else ''} ({description})")
            
            try:
                # Perform the search
                results = await state_cache.search_entities(term, domain)
                
                # Record results
                result_summary = {
                    "search_term": term,
                    "domain_filter": domain,
                    "description": description,
                    "success": True,
                    "match_count": len(results),
                    "error": None
                }
                test_results.append(result_summary)
                
                # Print results
                if results:
                    print(f"✅ Found {len(results)} matching entities")
                    
                    # Show top results with enhanced information from registry
                    for i, entity in enumerate(results[:5]):
                        score = entity.get("score", 0)
                        entity_id = entity.get("entity_id", "unknown")
                        state = entity.get("state", "unknown")
                        friendly_name = entity.get("friendly_name", entity_id)
                        
                        # Extract registry info for enhanced details
                        registry_info = entity.get("registry_info", {})
                        device_name = None
                        area_name = None
                        
                        if "device" in registry_info and registry_info["device"]:
                            device_name = registry_info["device"].get("name")
                            
                        if "area" in registry_info and registry_info["area"]:
                            area_name = registry_info["area"].get("name")
                        
                        # Print formatted result
                        print(f"  [{i+1}] Score: {score:.1f}, Entity: {entity_id}")
                        print(f"      Name: {friendly_name}, State: {state}")
                        
                        if device_name or area_name:
                            device_str = f"Device: {device_name}" if device_name else ""
                            area_str = f"Area: {area_name}" if area_name else ""
                            context_str = ", ".join(filter(None, [device_str, area_str]))
                            print(f"      {context_str}")
                    
                    # Show total count if more results
                    if len(results) > 5:
                        print(f"  ... and {len(results) - 5} more results")
                else:
                    print("❌ No matches found")
            except Exception as e:
                print(f"❌ Search error: {e}")
                
                # Record error
                result_summary = {
                    "search_term": term,
                    "domain_filter": domain,
                    "description": description,
                    "success": False,
                    "match_count": 0,
                    "error": str(e)
                }
                test_results.append(result_summary)
        
        # Print test summary
        print_header("Test Summary")
        success_count = sum(1 for result in test_results if result["success"])
        total_count = len(test_results)
        
        print(f"Total tests: {total_count}")
        print(f"Successful: {success_count}")
        print(f"Failed: {total_count - success_count}")
        
        # Show any failures
        if success_count < total_count:
            print("\nFailure details:")
            for i, result in enumerate([r for r in test_results if not r["success"]]):
                domain = f" (domain: {result['domain_filter']})" if result["domain_filter"] else ""
                print(f"  {i+1}. Term: \"{result['search_term']}\"{domain}")
                print(f"     Error: {result['error']}")
        
        return success_count == total_count
        
    except Exception as e:
        print(f"❌ Unexpected error during WebSocket test: {e}")
        return False
    finally:
        # Clean up
        if ws_client:
            print("\nCleaning up WebSocket connection...")
            await ws_client.stop()

async def run_tests():
    """Run all entity search tests."""
    websocket_result = await test_websocket_entity_search()
    return websocket_result

def main():
    """Main entry point."""
    try:
        return asyncio.run(run_tests())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)