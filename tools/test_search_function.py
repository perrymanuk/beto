#!/usr/bin/env python3
"""
Test the search_home_assistant_entities function directly.

This script directly calls the function tool to verify it works correctly.
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
import inspect

# Add the parent directory to the path so we can import raderbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_search_tool():
    """Test the entity search function tool directly."""
    from raderbot.tools.mcp_utils import find_home_assistant_entities
    
    print("=" * 60)
    print(" Testing Home Assistant Entity Search Directly ".center(60, "="))
    print("=" * 60)
    
    # We're going to bypass the FunctionTool wrapper and call the underlying function directly
    print("Testing direct call to find_home_assistant_entities...")
    
    # Test search terms
    search_terms = [
        "basement",
        "plant",
        "light"
    ]
    
    # Test calling the function directly
    for term in search_terms:
        print(f"\nTesting search term: '{term}'")
        
        try:
            # Call the function directly
            result = find_home_assistant_entities(search_term=term)
            
            # Print the result
            success = result.get('success', False)
            match_count = result.get('match_count', 0)
            status = "✅" if success else "❌"
            
            print(f"{status} Result: {result.get('status', 'unknown')}")
            print(f"  Found {match_count} matches")
            
            if match_count > 0:
                print("\n  Top matches:")
                for i, match in enumerate(result.get('matches', [])[:3]):
                    print(f"    {i+1}. {match['entity_id']} (score: {match['score']})")
            
            # Try also with domain filter
            print(f"\nTesting with domain filter: '{term}' + domain='light'")
            filtered_result = find_home_assistant_entities(search_term=term, domain_filter="light")
            
            filtered_success = filtered_result.get('success', False)
            filtered_match_count = filtered_result.get('match_count', 0)
            filtered_status = "✅" if filtered_success else "❌"
            
            print(f"{filtered_status} Result: {filtered_result.get('status', 'unknown')}")
            print(f"  Found {filtered_match_count} light matches")
            
            if filtered_match_count > 0:
                print("\n  Top light matches:")
                for i, match in enumerate(filtered_result.get('matches', [])[:3]):
                    print(f"    {i+1}. {match['entity_id']} (score: {match['score']})")
                    
        except Exception as e:
            print(f"❌ Error calling function: {str(e)}")
    
    print("\n" + "=" * 60)
    print(" Test complete! ".center(60, "="))
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(test_search_tool())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)