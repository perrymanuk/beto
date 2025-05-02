#!/usr/bin/env python3
"""
Example script showcasing the enhanced Home Assistant entity search functionality.

This script demonstrates how to use the improved entity search capabilities
using the WebSocket API and entity registry display information.
"""

import asyncio
import logging
import os
import sys
from typing import Dict, Any, List, Optional
from pprint import pprint
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Default Home Assistant WebSocket URL
DEFAULT_HA_WS_URL = "ws://localhost:8123/api/websocket"

# Check necessary modules are available in path
try:
    from dotenv import load_dotenv
    # Load environment variables
    load_dotenv()
except ImportError:
    logger.warning("python-dotenv not installed, falling back to environment variables only")

# Add project root to path if running directly from examples directory
if os.path.basename(os.getcwd()) == "examples":
    sys.path.append(os.path.dirname(os.getcwd()))

from radbot.tools.ha_websocket_client import HomeAssistantWebsocketClient
from radbot.tools.ha_state_cache import HomeAssistantStateCache
from radbot.tools.ha_tools_impl import search_home_assistant_entities

# Global variables
ws_client = None
state_cache = None
initialized = False

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

def print_json(obj):
    """Print an object as formatted JSON."""
    print(json.dumps(obj, indent=2, default=str))

async def update_state_callback(event_data: Dict[str, Any]) -> None:
    """Callback function for state updates."""
    global state_cache
    if state_cache:
        await state_cache.update_state(event_data)
        logger.debug(f"Updated state for {event_data.get('entity_id')}")

async def initialize_home_assistant():
    """Initialize the Home Assistant WebSocket client and state cache."""
    global ws_client, state_cache, initialized
    
    # Get configuration from environment variables
    ha_ws_url = os.getenv("HA_WS_URL", DEFAULT_HA_WS_URL)
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_token:
        logger.error("HA_TOKEN environment variable is not set")
        logger.error("Please set this in your .env file or export it in your environment")
        return False
    
    print_header("Home Assistant WebSocket Search Example")
    print(f"Connecting to Home Assistant at {ha_ws_url}")
    
    # Create state cache
    state_cache = HomeAssistantStateCache()
    
    try:
        # Create and connect WebSocket client
        ws_client = HomeAssistantWebsocketClient(ha_ws_url, ha_token, update_state_callback)
        
        # Connect but don't start the listener yet
        connection_result = await ws_client.connect(auto_listen=False)
        if not connection_result:
            logger.error("Failed to connect to Home Assistant WebSocket API")
            return False
        
        print("✅ Connected to Home Assistant WebSocket API")
        
        # Initialize with all current states
        print("Fetching all entity states...")
        all_states = await ws_client.get_all_states()
        print(f"✅ Received {len(all_states)} entities from Home Assistant")
        
        # Process each state into the cache
        for state_data in all_states:
            entity_id = state_data.get("entity_id")
            if entity_id:
                event_data = {"entity_id": entity_id, "new_state": state_data}
                await state_cache.update_state(event_data)
        
        # Fetch enhanced registry data with display information
        print("\nFetching registry display information...")
        try:
            entity_registry_display = await ws_client.get_entity_registry_for_display()
            print(f"✅ Received {len(entity_registry_display)} display registry entries")
            await state_cache.update_entity_registry_display(entity_registry_display)
        except Exception as display_error:
            logger.error(f"Error fetching display registry: {display_error}")
            
            # Fall back to regular registry
            print("Falling back to standard registry...")
            entity_registry = await ws_client.get_entity_registry()
            print(f"✅ Received {len(entity_registry)} standard registry entries")
            await state_cache.update_entity_registry(entity_registry)
        
        # Get device registry for additional context
        print("\nFetching device registry...")
        device_registry = await ws_client.get_device_registry()
        print(f"✅ Received {len(device_registry)} device registry entries")
        await state_cache.update_device_registry(device_registry)
        
        # Start listener for real-time updates
        print("\nStarting event listener for real-time updates...")
        await ws_client.start_listening()
        
        # Get available domains for context
        domains = await state_cache.get_domains()
        domain_counts = {}
        total_entities = 0
        
        for domain in domains:
            entities = await state_cache.get_entities_by_domain(domain)
            count = len(entities)
            domain_counts[domain] = count
            total_entities += count
        
        # Sort domains by count (descending)
        sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
        
        print(f"\nFound {total_entities} entities across {len(domains)} domains:")
        for domain, count in sorted_domains[:10]:  # Show top 10 domains
            print(f"  - {domain}: {count} entities")
            
        if len(sorted_domains) > 10:
            print(f"  - ...and {len(sorted_domains) - 10} more domains")
        
        initialized = True
        return True
        
    except Exception as e:
        logger.error(f"Error initializing Home Assistant: {e}", exc_info=True)
        return False

async def cleanup_home_assistant():
    """Clean up the Home Assistant WebSocket client."""
    global ws_client
    if ws_client:
        await ws_client.stop()
        print("\nHome Assistant WebSocket client stopped")

async def perform_entity_search(search_term, domain_filter=None):
    """Perform an entity search and display the results."""
    global state_cache, initialized
    
    if not initialized or not state_cache:
        print("❌ Home Assistant not initialized")
        return
    
    domain_text = f" in domain '{domain_filter}'" if domain_filter else ""
    print_subheader(f"Searching for '{search_term}'{domain_text}")
    
    try:
        # Use the direct state cache search method for demonstration
        results = await state_cache.search_entities(search_term, domain_filter)
        
        if results:
            print(f"✅ Found {len(results)} matching entities")
            
            # Show top results with enhanced information from registry
            for i, entity in enumerate(results[:10]):  # Show top 10 results
                score = entity.get("score", 0)
                entity_id = entity.get("entity_id", "unknown")
                state = entity.get("state", "unknown")
                friendly_name = entity.get("friendly_name", entity_id)
                
                # Extract registry info for enhanced details
                registry_info = entity.get("registry_info", {})
                
                print(f"\n[{i+1}] {friendly_name} ({entity_id})")
                print(f"    Score: {score:.1f}, State: {state}")
                
                # Show device information if available
                if "device" in registry_info and registry_info["device"]:
                    device = registry_info["device"]
                    device_name = device.get("name", "Unknown device")
                    manufacturer = device.get("manufacturer", "Unknown manufacturer")
                    model = device.get("model", "Unknown model")
                    print(f"    Device: {device_name}")
                    print(f"    Manufacturer: {manufacturer}, Model: {model}")
                
                # Show area information if available
                if "area" in registry_info and registry_info["area"]:
                    area = registry_info["area"]
                    area_name = area.get("name", "Unknown area")
                    print(f"    Area: {area_name}")
            
            # Show total count if more results
            if len(results) > 10:
                print(f"\n... and {len(results) - 10} more results")
        else:
            print("❌ No matching entities found")
    
    except Exception as e:
        print(f"❌ Error during search: {e}")

async def interactive_search():
    """Run an interactive search loop."""
    print_header("Interactive Entity Search")
    print("Type 'exit' to quit, 'domains' to list domains, or your search term.")
    print("Format: [search term] or [search term]:[domain] to filter by domain")
    
    while True:
        try:
            # Get user input
            user_input = input("\nSearch> ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit"]:
                break
                
            if user_input.lower() == "domains":
                domains = await state_cache.get_domains()
                print("\nAvailable domains:")
                for domain in sorted(domains):
                    entities = await state_cache.get_entities_by_domain(domain)
                    print(f"  - {domain}: {len(entities)} entities")
                continue
            
            # Check if domain filter is specified
            domain_filter = None
            search_term = user_input
            
            if ":" in user_input:
                parts = user_input.split(":", 1)
                search_term = parts[0].strip()
                domain_filter = parts[1].strip()
            
            # Perform the search
            await perform_entity_search(search_term, domain_filter)
            
        except KeyboardInterrupt:
            print("\nSearch interrupted")
            break
        except Exception as e:
            print(f"Error: {e}")

async def run_demo_searches():
    """Run a series of demo searches to showcase functionality."""
    demo_searches = [
        {"term": "light", "domain": None, "description": "Basic domain search"},
        {"term": "living room", "domain": None, "description": "Location search"},
        {"term": "temperature", "domain": None, "description": "Attribute search"},
        {"term": "motion", "domain": None, "description": "Feature search"},
        {"term": "door", "domain": None, "description": "Device type search"},
        {"term": "kitchen light", "domain": None, "description": "Combined location + device"},
        {"term": "bedroom", "domain": "light", "description": "Location with domain filter"},
        {"term": "temp", "domain": "sensor", "description": "Abbreviated term with domain filter"},
    ]
    
    print_header("Demonstration Searches")
    
    for search in demo_searches:
        await perform_entity_search(search["term"], search["domain"])
        await asyncio.sleep(1)  # Brief pause between searches

async def main():
    """Main entry point."""
    try:
        # Initialize Home Assistant
        success = await initialize_home_assistant()
        if not success:
            return 1
        
        # Offer choice between interactive and demo mode
        print_header("Home Assistant Entity Search Demo")
        print("1. Run demonstration searches")
        print("2. Interactive search mode")
        
        choice = input("Select mode (1-2): ").strip()
        
        if choice == "1":
            await run_demo_searches()
        else:
            await interactive_search()
            
        return 0
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return 1
    finally:
        # Clean up
        await cleanup_home_assistant()

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\nProgram interrupted")
        sys.exit(130)