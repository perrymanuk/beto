#!/usr/bin/env python3
"""
Simple test script to verify Home Assistant WebSocket search functionality.
This script connects directly to Home Assistant via WebSocket and tests entity searching.

Usage:
    python test_ha_search.py [search_term]
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("ha_search_test")

# Import our Home Assistant tools
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from radbot.tools.ha_websocket_client import HomeAssistantWebsocketClient
from radbot.tools.ha_state_cache import HomeAssistantStateCache
from radbot.tools.ha_tools_impl import search_home_assistant_entities

async def update_state_callback(event_data):
    """Simple callback for state updates - just logs the entity ID"""
    entity_id = event_data.get("entity_id", "unknown")
    logger.debug(f"Received state update for: {entity_id}")


async def main():
    """Main test function"""
    # Load environment variables
    load_dotenv()

    # Get WebSocket URL and token from environment
    ws_url = os.environ.get("HA_WEBSOCKET_URL")
    ws_token = os.environ.get("HA_WEBSOCKET_TOKEN")
    
    # Fall back to MCP variables if needed
    if not ws_url and os.environ.get("HA_MCP_SSE_URL"):
        mcp_url = os.environ.get("HA_MCP_SSE_URL")
        base_url = mcp_url
        if "/mcp_server/sse" in base_url:
            base_url = base_url.split("/mcp_server/sse")[0]
        elif "/api/mcp_server/sse" in base_url:
            base_url = base_url.split("/api/mcp_server/sse")[0]
            
        # Convert http/https to ws/wss
        if base_url.startswith("http://"):
            base_url = base_url.replace("http://", "ws://")
        elif base_url.startswith("https://"):
            base_url = base_url.replace("https://", "wss://")
            
        ws_url = f"{base_url}/api/websocket"
        logger.info(f"Derived WebSocket URL from MCP URL: {ws_url}")

    if not ws_token and os.environ.get("HA_AUTH_TOKEN"):
        ws_token = os.environ.get("HA_AUTH_TOKEN")
        logger.info("Using token from HA_AUTH_TOKEN environment variable")

    if not ws_url or not ws_token:
        logger.error("Missing HA_WEBSOCKET_URL or HA_WEBSOCKET_TOKEN environment variables")
        return 1

    try:
        # Create state cache
        state_cache = HomeAssistantStateCache()

        # Create and start WebSocket client
        logger.info(f"Connecting to Home Assistant at {ws_url}")
        ws_client = HomeAssistantWebsocketClient(ws_url, ws_token, update_state_callback)
        
        logger.info("Starting WebSocket client...")
        connection_success = await ws_client.start()
        if not connection_success:
            logger.warning("Connection reported issues during startup")
            # Wait a bit longer
            logger.info("Giving connection extra time...")
            await asyncio.sleep(5)

        # Try to get states
        try:
            logger.info("Fetching entity states...")
            all_states = await ws_client.get_all_states()
            logger.info(f"Received {len(all_states)} entity states")

            # Process entities into state cache
            for state in all_states:
                entity_id = state.get("entity_id")
                if entity_id:
                    event_data = {
                        "entity_id": entity_id,
                        "new_state": state
                    }
                    await state_cache.update_state(event_data)
            
            # Try to get entity registry
            try:
                logger.info("Fetching entity registry...")
                entity_registry = await ws_client.get_entity_registry()
                logger.info(f"Received {len(entity_registry)} registry entries")
                await state_cache.update_entity_registry(entity_registry)
            except Exception as e:
                logger.error(f"Failed to get entity registry: {e}")
            
            # Try to get device registry
            try:
                logger.info("Fetching device registry...")
                device_registry = await ws_client.get_device_registry()
                logger.info(f"Received {len(device_registry)} device registry entries")
                await state_cache.update_device_registry(device_registry)
            except Exception as e:
                logger.error(f"Failed to get device registry: {e}")
                
            # Log domains found
            domains = await state_cache.get_domains()
            domain_counts = {}
            for domain in domains:
                entities = await state_cache.get_entities_by_domain(domain)
                domain_counts[domain] = len(entities)
            
            logger.info(f"Found {len(domains)} domains: {domain_counts}")
            
            # Get search term from command line or use default
            search_term = sys.argv[1] if len(sys.argv) > 1 else "light"
            logger.info(f"Searching for entities matching '{search_term}'...")

            # Test general search
            result = await search_home_assistant_entities(search_term)
            logger.info(f"Search results: {result.get('count')} entities found")
            
            # Print all entities found
            for i, entity in enumerate(result.get('entities', [])):
                entity_id = entity.get('entity_id')
                friendly_name = entity.get('friendly_name')
                state = entity.get('state')
                score = entity.get('score', 0)
                logger.info(f"  {i+1}. {entity_id} - '{friendly_name}' (state: {state}, score: {score})")
            
            # Now search with domain filter
            for domain in ['light', 'switch', 'sensor', 'binary_sensor']:
                domain_result = await search_home_assistant_entities(search_term, domain)
                logger.info(f"Search with domain '{domain}': {domain_result.get('count')} entities found")
            
            # Also do a domain-only search
            for domain in ['light', 'switch', 'sensor', 'binary_sensor']:
                domain_result = await search_home_assistant_entities("", domain)
                logger.info(f"Domain-only '{domain}': {domain_result.get('count')} entities found") 
            
        except Exception as e:
            logger.error(f"Error getting states: {e}", exc_info=True)
        
        # Clean up
        logger.info("Stopping WebSocket client...")
        await ws_client.stop()
        logger.info("Test complete")
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1
        
    return 0

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)