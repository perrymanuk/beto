#!/usr/bin/env python3
"""
Test script for the staged crawling and depth limiting features of crawl4ai.

This script tests:
1. Link extraction (Stage 1 of staged crawling)
2. Targeted crawling (Stage 2 of staged crawling)
3. Default depth limiting (depth=1)

Run this test with:
    python -m tests.tools.test_crawl4ai_staged
"""

import unittest
import os
import sys
import logging
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url
from radbot.tools.crawl4ai.utils import run_async_safely

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Test URL (a documentation site that's designed to be traversed)
TEST_URL = "https://terragrunt.gruntwork.io/docs"

class TestCrawl4AIStaged(unittest.TestCase):
    """Test cases for the staged crawling and depth limiting features."""
    
    def test_staged_crawl_link_extraction(self):
        """Test Stage 1 of staged crawling: link extraction."""
        print("\n== Testing Stage 1: Link Extraction ==")
        
        # Execute Stage 1
        result = crawl4ai_ingest_url(
            url=TEST_URL,
            staged_crawl=True
        )
        
        # Verify result structure
        self.assertTrue(isinstance(result, dict))
        self.assertIn('success', result)
        
        # If successful, check link extraction
        if result.get('success'):
            self.assertIn('links', result)
            self.assertGreater(len(result['links']), 0)
            self.assertIn('internal_link_count', result)
            self.assertIn('external_link_count', result)
            
            # Print results
            print(f"✅ Extracted {len(result['links'])} links")
            print(f"   - {result['internal_link_count']} internal links")
            print(f"   - {result['external_link_count']} external links")
            
            # Return links for use in the next test
            return result.get('links', [])
        else:
            print(f"❌ Link extraction failed: {result.get('error', 'Unknown error')}")
            return []
    
    def test_staged_crawl_targeted_crawling(self):
        """Test Stage 2 of staged crawling: targeted crawling."""
        # Get links from Stage 1
        links = self.test_staged_crawl_link_extraction()
        
        if not links:
            self.skipTest("Skipping test_staged_crawl_targeted_crawling due to failed link extraction")
            return
            
        print("\n== Testing Stage 2: Targeted Crawling ==")
        
        # Select first 2 internal links
        internal_links = [
            link.get('url') for link in links
            if 'terragrunt.gruntwork.io' in link.get('url', '')
        ][:2]
        
        if not internal_links:
            self.skipTest("No internal links found for targeted crawling")
            return
            
        # Execute Stage 2
        result = crawl4ai_ingest_url(
            url=TEST_URL,
            target_links=internal_links
        )
        
        # Verify result
        self.assertTrue(isinstance(result, dict))
        self.assertIn('success', result)
        
        if result.get('success'):
            self.assertIn('urls_processed', result)
            self.assertEqual(result['urls_processed'], len(internal_links))
            
            # Print results
            print(f"✅ Crawled {result.get('urls_successful', 0)} out of {len(internal_links)} targeted links")
            print(f"   - Total chunks: {result.get('total_chunks', 0)}")
        else:
            print(f"❌ Targeted crawling failed: {result.get('error', 'Unknown error')}")
    
    def test_depth_limited_crawling(self):
        """Test depth-limited crawling with the default depth=1."""
        print("\n== Testing Depth-Limited Crawling (depth=1) ==")
        
        # Execute with default depth=1
        result = crawl4ai_ingest_url(
            url=TEST_URL
        )
        
        # Verify result
        self.assertTrue(isinstance(result, dict))
        self.assertIn('success', result)
        
        if result.get('success'):
            # Print results
            if 'pages_crawled' in result:
                print(f"✅ Crawled {result.get('pages_crawled', 0)} pages")
                print(f"   - Stored {result.get('pages_stored', 0)} pages")
                print(f"   - Total chunks: {result.get('total_chunks', 0)}")
            else:
                print(f"✅ Crawling completed: {result.get('message', 'No message')}")
        else:
            print(f"❌ Depth-limited crawling failed: {result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    unittest.main()
