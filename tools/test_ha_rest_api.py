#!/usr/bin/env python3
"""
Test script for Home Assistant REST API entity listing and search functionality.
"""

import os
import sys
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the Home Assistant REST client
from dotenv import load_dotenv
from radbot.tools.ha_rest_client import HomeAssistantClient
from radbot.tools.ha_state_cache import get_state_cache, search_ha_entities

# Load environment variables
load_dotenv()

def get_client():
    """Get a configured Home Assistant REST client."""
    ha_url = os.getenv("HA_URL")
    ha_token = os.getenv("HA_TOKEN")
    
    if not ha_url or not ha_token:
        logger.error("HA_URL or HA_TOKEN environment variables not set.")
        return None
        
    return HomeAssistantClient(ha_url, ha_token)

def test_direct_api_access():
    """
    Test direct access to Home Assistant REST API.
    """
    logger.info("Testing direct REST API access...")
    
    client = get_client()
    if not client:
        logger.error("Failed to create Home Assistant client.")
        return False
        
    # Check API status
    if not client.get_api_status():
        logger.error("API status check failed. Home Assistant API is not accessible.")
        return False
        
    logger.info("API status check successful.")
    
    # Get all entities
    entities = client.list_entities()
    if not entities:
        logger.error("Failed to retrieve entities from Home Assistant.")
        return False
        
    logger.info(f"Successfully retrieved {len(entities)} entities from REST API.")
    
    # Print the first 5 entities as a sample
    logger.info("Sample entities:")
    for i, entity in enumerate(entities[:5]):
        entity_id = entity.get("entity_id", "unknown")
        state = entity.get("state", "unknown")
        friendly_name = entity.get("attributes", {}).get("friendly_name", "unknown")
        logger.info(f"  {i+1}. {entity_id} - {friendly_name} - {state}")
        
    # Look specifically for entities with "milsbo" in their ID
    milsbo_entities = [e for e in entities if "milsbo" in e.get("entity_id", "").lower()]
    
    if milsbo_entities:
        logger.info(f"Found {len(milsbo_entities)} entities containing 'milsbo':")
        for entity in milsbo_entities:
            logger.info(f"  - {entity.get('entity_id')} - "
                       f"{entity.get('state')} - "
                       f"{entity.get('attributes', {}).get('friendly_name', 'unknown')}")
    else:
        logger.info("No entity containing 'milsbo' was found.")
        
        # List all switches to check if it might be there with a different name
        switches = [e for e in entities if e.get("entity_id", "").startswith("switch.")]
        logger.info(f"Found {len(switches)} switches:")
        for i, switch in enumerate(switches):
            if i < 10:  # Limit to 10 switches to avoid flooding logs
                logger.info(f"  - {switch.get('entity_id')} - {switch.get('attributes', {}).get('friendly_name', 'unknown')}")
        if len(switches) > 10:
            logger.info(f"  ... and {len(switches) - 10} more switches")
    
    # Test specific entity retrieval
    logger.info("Testing specific entity retrieval...")
    
    # Try to get a known entity (light.kitchen or similar)
    test_entity = next((e.get("entity_id") for e in entities if e.get("entity_id", "").startswith("light.")), None)
    
    if test_entity:
        entity_state = client.get_state(test_entity)
        if entity_state:
            logger.info(f"Successfully retrieved state for {test_entity}: {entity_state.get('state')}")
        else:
            logger.error(f"Failed to retrieve state for {test_entity}")
    else:
        logger.info("No light entities found for testing specific entity retrieval.")
    
    return True

def test_entity_search():
    """
    Test the entity search functionality using our search_ha_entities function.
    """
    logger.info("Testing entity search functionality...")
    
    # First search for "milsbo"
    search_result = search_ha_entities("milsbo")
    
    logger.info(f"Search for 'milsbo' result: {search_result.get('status')}")
    if search_result.get('status') == "error":
        logger.error(f"Search error: {search_result.get('message')}")
    else:
        logger.info(f"Found {search_result.get('match_count', 0)} matches for 'milsbo'")
        for match in search_result.get('matches', []):
            logger.info(f"  - {match.get('entity_id')} (score: {match.get('score')}) - {match.get('match_reasons')}")
        
    # Try searching with a domain filter
    switch_search = search_ha_entities("", "switch")
    
    logger.info(f"Search in 'switch' domain result: {switch_search.get('status')}")
    if switch_search.get('status') == "error":
        logger.error(f"Switch domain search error: {switch_search.get('message')}")
    else:
        logger.info(f"Found {switch_search.get('match_count', 0)} switches")
        for match in switch_search.get('matches', [])[:10]:  # Limit to 10 entries
            logger.info(f"  - {match.get('entity_id')} - {match.get('friendly_name')}")
    
    # Get available domains
    domains = search_result.get('available_domains', [])
    if domains:
        logger.info(f"Available domains from search: {', '.join(domains)}")
    else:
        logger.info("No domains returned in search result.")

def main():
    """
    Main function to run tests.
    """
    print("=" * 60)
    print("  Testing Home Assistant REST API Functionality")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("HA_URL") or not os.getenv("HA_TOKEN"):
        print("\nError: HA_URL and HA_TOKEN environment variables must be set.")
        print("Please set these in your .env file:")
        print("  HA_URL=http://your-home-assistant:8123")
        print("  HA_TOKEN=your_long_lived_access_token")
        return
    
    logger.info(f"Using Home Assistant at {os.getenv('HA_URL')}")
    
    # Run tests
    print("\n1. Testing direct REST API access...")
    test_direct_api_access()
    
    print("\n2. Testing entity search functionality...")
    test_entity_search()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main()