#!/usr/bin/env python3
"""Test script to verify the Crawl4AI module refactoring."""

import sys
import os

def main():
    """Test the imports and report success or failure."""
    try:
        # Try both the original import that should now forward to the modular implementation
        from radbot.tools.mcp_crawl4ai_client import create_crawl4ai_toolset, test_crawl4ai_connection
        print("✅ Successfully imported from the original location")
        
        # Try importing directly from the new modular structure
        from radbot.tools.crawl4ai import create_crawl4ai_toolset
        from radbot.tools.crawl4ai.utils import get_crawl4ai_config
        from radbot.tools.crawl4ai.crawl4ai_query import crawl4ai_query
        from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url
        from radbot.tools.crawl4ai.crawl4ai_ingest_and_read import crawl4ai_ingest_and_read
        print("✅ Successfully imported from the new modular locations")
        
        print("All import tests successful!")
        return 0
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
