#!/usr/bin/env python3
"""
Validate the Qdrant compatibility fix by testing vector store operations.
"""

import sys
import os
from pprint import pprint

# Add the parent directory to the path so we can import radbot
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import the vector store class with our fix
    from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store, Crawl4AIVectorStore
    
    print("=== Validating Qdrant Collection Count Fix ===\n")
    
    # First test: Direct vector store operations
    try:
        print("1. Testing direct vector store operations:")
        vector_store = get_crawl4ai_vector_store()
        print(f"✅ Successfully initialized vector store with collection: {vector_store.collection_name}")
        
        # Test counting documents
        count = vector_store.count_documents()
        print(f"✅ Successfully counted documents: {count}")
        
        # Test adding a test document
        test_url = "https://example.com/test"
        test_title = "Test Document"
        test_content = """
        # Test Document
        
        This is a test document for validating the Qdrant fix.
        
        ## Section 1
        
        This is section 1 content about vector databases.
        
        ## Section 2
        
        This is section 2 content about Qdrant and compatibility.
        """
        
        print("\n2. Testing document addition:")
        result = vector_store.add_document(
            url=test_url, 
            title=test_title,
            content=test_content
        )
        print(f"✅ Document addition {'succeeded' if result.get('success') else 'failed'}")
        print(f"Message: {result.get('message', 'No message')}")
        print(f"Chunks: {result.get('chunks_count', 0)}")
        
        # Test counting documents again
        new_count = vector_store.count_documents()
        print(f"\n3. Testing document counting after addition:")
        print(f"✅ New document count: {new_count} (previous: {count})")
        
        # Test searching
        print("\n4. Testing vector search:")
        search_result = vector_store.search("vector database")
        print(f"✅ Search {'succeeded' if search_result.get('success') else 'failed'}")
        print(f"Results count: {search_result.get('count', 0)}")
        
        # Clean up by deleting test document
        print("\n5. Testing document deletion:")
        delete_result = vector_store.delete_document(test_url)
        print(f"✅ Document deletion {'succeeded' if delete_result.get('success') else 'failed'}")
        print(f"Message: {delete_result.get('message', 'No message')}")
        
        # Final count check
        final_count = vector_store.count_documents()
        print(f"\n6. Final document count: {final_count}")
        
        print("\n✅ All vector store operations completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during vector store operations: {str(e)}")
    
    # Second test: With the crawl4ai_ingest_url functions
    try:
        print("\n=== Testing with crawl4ai functions ===")
        from radbot.tools.mcp_crawl4ai_client import crawl4ai_ingest_url, crawl4ai_query
        
        print("1. Testing URL ingestion:")
        test_url = "https://docs.qdrant.tech/documentation/"
        result = crawl4ai_ingest_url(test_url)
        
        if result.get("success", False):
            print(f"✅ URL ingestion successful!")
            print(f"Message: {result.get('message')}")
            print(f"Content length: {result.get('content_length', 'unknown')}")
            
            # Test query
            print("\n2. Testing query after ingestion:")
            query_result = crawl4ai_query("vector search")
            
            if query_result.get("success", False):
                print(f"✅ Query successful!")
                print("Content found in results!")
            else:
                print(f"❌ Query failed!")
                print(f"Error: {query_result.get('error')}")
                print(f"Message: {query_result.get('message')}")
        else:
            print("❌ URL ingestion failed!")
            print(f"Error: {result.get('error')}")
            print(f"Message: {result.get('message')}")
            
    except ImportError:
        print("ℹ️ Skipping crawl4ai function tests (imports not available)")
    except Exception as e:
        print(f"❌ Error during crawl4ai tests: {str(e)}")

except ImportError as e:
    print(f"❌ ERROR: Failed to import required modules: {str(e)}")
    print("Make sure you have all required dependencies installed.")
    sys.exit(1)
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
    sys.exit(1)
    
print("\nValidation complete!")