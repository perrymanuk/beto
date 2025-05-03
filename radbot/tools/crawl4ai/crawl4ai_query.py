#!/usr/bin/env python3
"""
Crawl4AI Query Module

This module provides functionality for querying content stored in the Crawl4AI vector database.
"""

import logging
from typing import Dict, Any

from .utils import run_async_safely

# Configure logging
logger = logging.getLogger(__name__)

async def _call_crawl4ai_query_api(search_query):
    """Internal function to call the vector store for semantic search in crawled content."""
    # Print input for debugging
    print(f"DEBUG - Crawl4AI vector search with query: '{search_query}'")
    logger.info(f"Crawl4AI vector search querying knowledge base for: {search_query}")
    
    # Validate query parameter
    if not search_query or not isinstance(search_query, str):
        error_msg = f"Invalid search query parameter: {search_query!r}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "Search query must be a non-empty string",
            "results": []
        }
    
    # Use our vector store for search instead of the crawl4ai API directly
    try:
        # Import here to avoid circular imports
        from radbot.tools.crawl4ai_vector_store import get_crawl4ai_vector_store
        
        # Get vector store instance
        vector_store = get_crawl4ai_vector_store()
        
        # Search using the vector store
        search_result = vector_store.search(query=search_query, limit=5)
        
        if search_result["success"]:
            if search_result["count"] > 0:
                logger.info(f"Found {search_result['count']} results for query: {search_query}")
                
                # Format the results into markdown for easy consumption by the LLM
                formatted_results = []
                
                for i, result in enumerate(search_result["results"]):
                    # Format each result as markdown
                    formatted_result = f"""
### Result {i+1} - {result['title']} (Score: {result['similarity']:.2f})

**Source URL**: {result['url']}

{result['content'].strip()}

---"""
                    formatted_results.append(formatted_result)
                
                # Combine the results
                combined_content = "\n".join(formatted_results)
                
                return {
                    "success": True,
                    "message": f"Found {search_result['count']} relevant results",
                    "results": combined_content
                }
            else:
                logger.info(f"No results found for query: {search_query}")
                return {
                    "success": True,
                    "message": "No relevant information found in the knowledge base",
                    "results": "No matching content was found in the knowledge base for your query. You may need to first ingest content using the crawl4ai_ingest_url function before searching."
                }
        else:
            error_msg = search_result.get('message', '')
            logger.error(f"Vector search error: {error_msg}")
            
            # Check if the error is about no documents
            if "no documents have been stored" in error_msg.lower():
                return {
                    "success": False,
                    "message": "The knowledge base is empty. Please ingest content first using crawl4ai_ingest_url.",
                    "error": error_msg,
                    "results": []
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to search knowledge base: {error_msg}",
                    "error": error_msg,
                    "results": []
                }
    except Exception as e:
        logger.error(f"Error in vector search: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to search knowledge base: {str(e)}",
            "error": str(e),
            "results": []
        }

def crawl4ai_query(query: str) -> Dict[str, Any]:
    """
    Search the Crawl4AI knowledge base for information about the query.
    
    This function searches the previously crawled and ingested web content
    using vector-based semantic search. It returns relevant excerpts from 
    the crawled web pages that match your query.
    
    IMPORTANT: Before using this function, you must first ingest content 
    using either crawl4ai_ingest_url or crawl4ai_ingest_and_read functions,
    otherwise there will be nothing to search.
    
    Typical workflow:
    1. Use crawl4ai_ingest_url("https://example.com/docs") to load content
    2. Use crawl4ai_query("my search terms") to search the ingested content
    
    Args:
        query: The search query to look for in the Crawl4AI knowledge base
        
    Returns:
        A dictionary containing search results from crawled web content
    """
    print(f"🔍 Crawl4AI query called with query: {query}")
    return run_async_safely(_call_crawl4ai_query_api(query))
