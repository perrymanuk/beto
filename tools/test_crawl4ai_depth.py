#!/usr/bin/env python3
"""
Test script for validating the improved Crawl4AI depth crawling functionality.

This script tests different depth levels to verify that the crawling behaves
as expected, with proper depth handling and link following.
"""

import os
import sys
import asyncio
import logging
from pprint import pprint
from typing import Dict, List, Any, Set

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Crawl4AI functions
from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url
from radbot.tools.crawl4ai.utils import get_crawl4ai_config, run_async_safely

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_crawl_depth(url: str, depth: int = 1, include_external: bool = False, max_pages: int = 10):
    """
    Test the crawl4ai_ingest_url function with different depth settings.
    
    Args:
        url: URL to crawl
        depth: Crawling depth
        include_external: Whether to follow external links
        max_pages: Maximum pages per depth level
    """
    print(f"\n{'=' * 80}")
    print(f"Testing crawl depth: {depth} for URL: {url}")
    print(f"include_external: {include_external}, max_pages: {max_pages}")
    print(f"{'=' * 80}\n")
    
    # Crawl the URL with specified depth
    result = crawl4ai_ingest_url(
        url=url, 
        crawl_depth=depth,
        include_external=include_external,
        max_pages=max_pages
    )
    
    # Print the result
    pprint(result)
    
    # Check if the crawl was successful
    if result.get('success'):
        print(f"\n✅ Crawl successful!")
        if 'pages_crawled' in result:
            print(f"Pages crawled: {result['pages_crawled']}")
            print(f"Pages stored: {result['pages_stored']}")
        print(f"Total chunks: {result.get('total_chunks', 0)}")
    else:
        print(f"\n❌ Crawl failed: {result.get('message')}")
    
    return result

def main():
    """Test different depth levels on a sample website."""
    # Get the test URL from command line or use default
    url = sys.argv[1] if len(sys.argv) > 1 else "https://example.com"
    
    # Test with depth=0 (base URL only)
    print("\nTesting with depth=0 (base URL only)")
    test_crawl_depth(url, depth=0)
    
    # Test with depth=1 (base URL + direct links)
    print("\nTesting with depth=1 (base URL + direct links)")
    test_crawl_depth(url, depth=1)
    
    # Ask if the user wants to test deeper levels which could take longer
    if input("\nTest with depth=2? This could take longer (y/n): ").lower() == 'y':
        print("\nTesting with depth=2 (base URL + direct links + links from those pages)")
        test_crawl_depth(url, depth=2, max_pages=5)  # Limit max_pages to avoid excessive crawling
    
    # Ask if user wants to test with external links
    if input("\nTest with external links? (y/n): ").lower() == 'y':
        print("\nTesting with depth=1 and include_external=True")
        test_crawl_depth(url, depth=1, include_external=True, max_pages=5)
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError: {str(e)}")
        raise
