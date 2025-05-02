#!/usr/bin/env python3
"""
Test script for Home Assistant entity listing and search functionality.
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

# Import the Home Assistant client and search functionality
from dotenv import load_dotenv
from radbot.tools.ha_client_singleton import get_ha_client
from radbot.tools.ha_state_cache import get_state_cache, search_ha_entities

# Load environment variables
load_dotenv()

def test_entity_listing():
    """
    Test listing all Home Assistant entities directly using the client.
    """
    logger.info("Testing direct entity listing...")
    
    client = get_ha_client()
    if not client:
        logger.error("Failed to get Home Assistant client. Check environment variables.")
        return False
        
    # Try to get all entities
    entities = client.list_entities()
    if not entities:
        logger.error("No entities returned from Home Assistant.")
        return False
        
    logger.info(f"Successfully retrieved {len(entities)} entities directly from Home Assistant.")
    
    # Print the first 5 entities as a sample
    logger.info("Sample entities:")
    for i, entity in enumerate(entities[:5]):
        entity_id = entity.get("entity_id", "unknown")
        state = entity.get("state", "unknown")
        friendly_name = entity.get("attributes", {}).get("friendly_name", "unknown")
        logger.info(f"  {i+1}. {entity_id} - {friendly_name} - {state}")
        
    # Look specifically for the milsbo_tall entity
    milsbo_entity = next((e for e in entities if "milsbo" in e.get("entity_id", "").lower()), None)
    
    if milsbo_entity:
        logger.info(f"Found milsbo entity: {milsbo_entity.get('entity_id')} - "
                   f"{milsbo_entity.get('state')} - "
                   f"{milsbo_entity.get('attributes', {}).get('friendly_name', 'unknown')}")
    else:
        logger.info("No entity containing 'milsbo' was found in the direct entity list.")
        
        # List all switches to check if it might be there
        switches = [e for e in entities if e.get("entity_id", "").startswith("switch.")]
        logger.info(f"Found {len(switches)} switches:")
        for switch in switches:
            logger.info(f"  - {switch.get('entity_id')}")
    
    return True

def test_cache_functionality():
    """
    Test the state cache functionality.
    """
    logger.info("Testing state cache functionality...")
    
    cache = get_state_cache()
    
    # Force cache update
    success = cache.update_cache()
    if not success:
        logger.error("Failed to update the entity cache.")
        return False
        
    # Get all entities from cache
    entities = cache.get_all_entities()
    logger.info(f"Cache contains {len(entities)} entities.")
    
    # Get available domains
    domains = cache.get_domains()
    logger.info(f"Available domains: {', '.join(sorted(domains))}")
    
    # Look specifically for the milsbo_tall entity in the cache
    milsbo_entity = cache.get_entity_state("switch.milsbo_tall")
    
    if milsbo_entity:
        logger.info(f"Found milsbo_tall in cache: {milsbo_entity.get('entity_id')} - "
                   f"{milsbo_entity.get('state')}")
    else:
        logger.info("switch.milsbo_tall not found in cache.")
        
        # Try searching for entities with "milsbo" in their name or ID
        milsbo_entities = cache.search_entities("milsbo")
        if milsbo_entities:
            logger.info(f"Found {len(milsbo_entities)} entities matching 'milsbo' in cache:")
            for entity in milsbo_entities:
                logger.info(f"  - {entity.get('entity_id')} - {entity.get('score')} - {entity.get('match_reasons')}")
        else:
            logger.info("No entities matching 'milsbo' found in cache.")
    
    return True

def test_search_function():
    """
    Test the search_ha_entities function directly.
    """
    logger.info("Testing search_ha_entities function...")
    
    # Try searching for milsbo_tall
    result = search_ha_entities("milsbo")
    logger.info(f"Search result status: {result.get('status')}")
    logger.info(f"Search result message: {result.get('message', 'No message')}")
    logger.info(f"Match count: {result.get('match_count', 0)}")
    
    if result.get('match_count', 0) > 0:
        logger.info("Matches found:")
        for match in result.get('matches', []):
            logger.info(f"  - {match.get('entity_id')} - {match.get('score')} - {match.get('match_reasons')}")
    else:
        logger.info("No matches found.")
    
    # List available domains from the result
    domains = result.get('available_domains', [])
    if domains:
        logger.info(f"Available domains from search result: {', '.join(sorted(domains))}")
    else:
        logger.info("No domains returned in search result.")
        
    # Try with domain filter for switches
    logger.info("Searching for entities in the switch domain...")
    switch_result = search_ha_entities("", "switch")
    
    if switch_result.get('status') == 'success':
        logger.info(f"Found {switch_result.get('match_count', 0)} switches:")
        for match in switch_result.get('matches', []):
            logger.info(f"  - {match.get('entity_id')} - {match.get('friendly_name')}")
    else:
        logger.info(f"Error searching for switches: {switch_result.get('message', 'No message')}")

def main():
    """
    Main function to run tests.
    """
    print("=" * 60)
    print("  Testing Home Assistant Entity Listing and Search")
    print("=" * 60)
    
    # Check environment variables
    if not os.getenv("HA_URL") or not os.getenv("HA_TOKEN"):
        logger.error("HA_URL and HA_TOKEN environment variables not set.")
        print("\nPlease set HA_URL and HA_TOKEN in your .env file.")
        return
    
    logger.info(f"Using Home Assistant at {os.getenv('HA_URL')}")
    
    # Run tests
    print("\n1. Testing direct entity listing...")
    test_entity_listing()
    
    print("\n2. Testing state cache functionality...")
    test_cache_functionality()
    
    print("\n3. Testing search function...")
    test_search_function()
    
    print("\nAll tests completed.")

if __name__ == "__main__":
    main()