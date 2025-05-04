import logging
import requests
from typing import Dict, Any, List, Optional

from google.adk.tools import FunctionTool
from qdrant_client.http.models import Filter

# Use relative import since the module is now in the same package
from .crawl4ai_vector_store import get_crawl4ai_vector_store

logger = logging.getLogger(__name__)


def _call_crawl4ai_query_api(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Call the Crawl4AI API to search for content.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        API response as a dictionary
    """
    try:
        # Get configuration
        from .utils import get_crawl4ai_config
        api_url, api_token = get_crawl4ai_config()
        
        # Build the request URL and headers
        search_url = f"{api_url}/api/search"
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add authentication if token is provided
        if api_token:
            headers["Authorization"] = f"Bearer {api_token}"
        
        # Build the request body
        payload = {
            "query": query,
            "limit": limit
        }
        
        # Make the request
        response = requests.post(search_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Return the JSON response
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error calling Crawl4AI search API: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": []
        }

def crawl4ai_query(query: str, limit: int = 5) -> Dict[str, Any]:
    """
    Search the Crawl4AI knowledge base.
    
    This function searches the Crawl4AI knowledge base for documents
    matching the provided query. It uses either vector search from
    the local Qdrant database (if available) or falls back to the
    Crawl4AI API.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        Dictionary with search results
    """
    try:
        # Try using the vector store first
        results = search_crawl4ai_content(query, limit=limit)
        
        if results:
            # Format the results in a standard way
            return {
                "success": True,
                "message": f"Found {len(results)} results for query: {query}",
                "results": results
            }
        else:
            # Fall back to API if no results
            logger.info(f"No vector store results for '{query}', falling back to API")
            api_results = _call_crawl4ai_query_api(query, limit=limit)
            return api_results
    except Exception as e:
        logger.error(f"Error in crawl4ai_query: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Error searching for '{query}': {str(e)}",
            "results": []
        }


def search_crawl4ai_content(query: str, limit: int = 5, metadata_filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Search for crawled content using vector search.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        metadata_filter: Optional filter for metadata fields
        
    Returns:
        List of matching documents with content and metadata
    """
    try:
        vector_store = get_crawl4ai_vector_store()
        if not vector_store:
            logger.warning("Vector store not available for Crawl4AI search")
            return []
        
        filter_condition = None
        if metadata_filter:
            # Convert the metadata filter to a Qdrant filter
            # This is a simplistic implementation - would need to be expanded for more complex filters
            filter_condition = Filter(**metadata_filter)
        
        results = vector_store.similarity_search_with_score(
            query=query,
            k=limit,
            filter=filter_condition
        )
        
        # Format the results
        formatted_results = []
        for doc, score in results:
            result = {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": score
            }
            formatted_results.append(result)
            
        return formatted_results
    except Exception as e:
        logger.error(f"Error searching crawled content: {e}")
        return []


def create_crawl4ai_query_tool() -> FunctionTool:
    """
    Create a function tool for querying the crawled knowledge base.
    
    Returns:
        FunctionTool for crawl4ai_query
    """
    return FunctionTool(
        name="crawl4ai_query",
        description="Search for information in the crawled knowledge base",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to find information in the crawled knowledge base"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    )
