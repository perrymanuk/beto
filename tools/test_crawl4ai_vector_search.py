#!/usr/bin/env python3
"""
Test script for Crawl4AI integration with vector search.

This script tests the integration between Crawl4AI and Qdrant
for vector-based semantic search capabilities.
"""

import os
import sys
import logging
from pprint import pprint
import asyncio

# Add the parent directory to the path so we can import radbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import after path setup
from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store
from radbot.tools.mcp_crawl4ai_client import (
    crawl4ai_ingest_and_read,
    crawl4ai_ingest_url, 
    crawl4ai_query
)

async def test_crawl4ai_ingestion():
    """Test the Crawl4AI ingestion and search flow."""
    print("\n=== Testing Crawl4AI Vector Search Integration ===\n")
    
    # Define test URL - using the URL that's failing in the user's case
    test_url = "https://terragrunt.gruntwork.io/docs/reference/config-blocks-and-attributes/"
    # Backup test URL
    backup_test_url = "https://github.com/unclecode/crawl4ai"
    
    # Step 1: Test the vector store directly
    print("\n== Test 1: Vector Store Functions ==")
    try:
        vector_store = get_crawl4ai_vector_store()
        print(f"✅ Successfully connected to vector store: {vector_store.collection_name}")
    except Exception as e:
        print(f"❌ Error connecting to vector store: {str(e)}")
        return
    
    # Check document count
    try:
        count = vector_store.count_documents()
        print(f"📊 Current document count in vector store: {count}")
    except Exception as e:
        print(f"❌ Error counting documents: {str(e)}")
    
    # Step 2: Test ingest_url_to_knowledge_base function
    print("\n== Test 2: Ingesting URL to Knowledge Base ==")
    print(f"🔍 Ingesting URL: {test_url}")
    
    try:
        # Add more debug info
        print(f"\n🔍 Calling direct API to get content (for debugging)")
        import requests
        api_url = os.environ.get("CRAWL4AI_API_URL", "http://localhost:11235")
        api_token = os.environ.get("CRAWL4AI_API_TOKEN", "")
        
        # Get direct API response 
        print(f"API URL: {api_url}")
        headers = {"Content-Type": "application/json"}
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
            
        payload = {
            "url": test_url,
            "filter_type": "all",
            "markdown_flavor": "github"
        }
        
        print("Sending direct request to Crawl4AI API...")
        response = requests.post(f"{api_url}/md", headers=headers, json=payload, timeout=120)
        
        if response.status_code == 200:
            print(f"✅ Direct API call successful: {response.status_code}")
            api_response = response.json()
            print("API response keys:", list(api_response.keys()))
            if "content" in api_response:
                content_len = len(api_response["content"])
                print(f"API content length: {content_len} chars")
                print("Content preview (first 100 chars):")
                print(api_response["content"][:100])
            else:
                print("❌ No content key in API response")
                print("Full API response:")
                pprint(api_response)
        else:
            print(f"❌ Direct API call failed: {response.status_code}")
            print("Response text:")
            print(response.text[:500])  # First 500 chars
        
        # Now try the actual function
        print("\n🔍 Now testing crawl4ai_ingest_url function...")
        result = crawl4ai_ingest_url(test_url)
        print("\n📝 Ingest result:")
        pprint(result)
    except Exception as e:
        print(f"❌ Error ingesting URL: {str(e)}")
        
    # Check document count after ingestion
    try:
        count = vector_store.count_documents()
        print(f"📊 Document count after ingestion: {count}")
    except Exception as e:
        print(f"❌ Error counting documents: {str(e)}")
    
    # Step 3: Test web search function
    print("\n== Test 3: Searching Knowledge Base ==")
    
    test_queries = [
        "What is Crawl4AI?",
        "How to extract structured data?",
        "browser automation capabilities"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Searching for: '{query}'")
        try:
            result = crawl4ai_query(query)
            
            if result.get("success"):
                print(f"✅ Search successful!")
                if isinstance(result.get("results"), str) and len(result.get("results")) > 100:
                    # Truncate long results for display
                    print(f"📄 Results (truncated to 100 chars):")
                    print(result.get("results", "")[:100] + "...\n")
                else:
                    print(f"📄 Results:")
                    print(result.get("results", ""))
            else:
                print(f"❌ Search failed: {result.get('message')}")
        except Exception as e:
            print(f"❌ Error searching: {str(e)}")

def main():
    """Main function to run tests."""
    try:
        # Run the async test using asyncio
        asyncio.run(test_crawl4ai_ingestion())
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())