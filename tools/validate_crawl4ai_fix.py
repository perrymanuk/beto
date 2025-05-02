#!/usr/bin/env python3
"""
Validate the Crawl4AI fix by testing URL ingestion.
"""

import sys
import os
from pprint import pprint

# Add the parent directory to the path so we can import radbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import the fixed functions
    from radbot.tools.mcp_crawl4ai_client import (
        crawl4ai_ingest_url, 
        crawl4ai_query
    )
    
    print("=== Validating Crawl4AI Fix ===\n")
    
    # Use the URL that was previously failing
    test_url = "https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/"
    
    print(f"Testing URL ingestion: {test_url}")
    
    # Try to ingest the URL
    result = crawl4ai_ingest_url(test_url)
    
    # Check if the ingestion was successful
    if result.get("success", False):
        print(f"✅ URL Ingestion SUCCESSFUL!")
        print(f"Message: {result.get('message')}")
        print(f"Content length: {result.get('content_length', 'unknown')} characters")
        print(f"Chunks: {result.get('chunks_count', 'unknown')}")
        print(f"Status: {result.get('status')}")
        
        # Now test the query
        print("\nTesting search functionality...")
        query_result = crawl4ai_query("terragrunt version constraint")
        
        if query_result.get("success", False):
            print("✅ Search SUCCESSFUL!")
            print("Search results contain content!")
            
            # Show a preview of the search results
            results_preview = query_result.get("results", "")[:200] + "..."
            print(f"\nSearch results preview:\n{results_preview}")
        else:
            print("❌ Search FAILED!")
            print(f"Error: {query_result.get('error')}")
            print(f"Message: {query_result.get('message')}")
    else:
        print("❌ URL Ingestion FAILED!")
        print(f"Error: {result.get('error')}")
        print(f"Message: {result.get('message')}")
    
except ImportError as e:
    print(f"❌ ERROR: Failed to import required modules: {str(e)}")
    print("Make sure you have all required dependencies installed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)
    
print("\nValidation complete!")