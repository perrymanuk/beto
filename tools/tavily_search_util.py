#!/usr/bin/env python3
"""
Utility script for performing direct searches using the Tavily API.

This script completely bypasses the agent and directly uses the Tavily API.
"""

import os
import sys
import argparse
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def search_tavily(query, max_results=3, search_depth="advanced"):
    """
    Perform a search using the Tavily API directly.
    
    Args:
        query: The search query
        max_results: Maximum number of results to return
        search_depth: Search depth ("basic" or "advanced")
    
    Returns:
        The search results as text
    """
    # Check for API key
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        print("ERROR: TAVILY_API_KEY environment variable not set.")
        print("Please set this variable in your .env file or export it before running this script.")
        return None
    
    # First try using LangChain's Tavily integration
    try:
        from langchain_community.tools import TavilySearchResults
        
        # Set the API key explicitly in environment for LangChain
        os.environ["TAVILY_API_KEY"] = api_key
        
        # Create the TavilySearchResults instance
        tavily_search = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=True,
            include_raw_content=True,
            include_images=False,
        )
        
        # Use the tool directly
        print(f"Searching for: {query}")
        print(f"Using LangChain's TavilySearchResults with max_results={max_results}, search_depth={search_depth}")
        
        results = tavily_search.invoke(query)
        return results
    except ImportError:
        print("LangChain's TavilySearchResults not available. Trying direct API...")
    
    # If LangChain's integration is not available, try using tavily-python directly
    try:
        from tavily import TavilyClient
        
        # Create a client
        client = TavilyClient(api_key=api_key)
        print(f"Searching for: {query}")
        print(f"Using Tavily API directly with max_results={max_results}, search_depth={search_depth}")
        
        response = client.search(
            query=query,
            search_depth=search_depth,
            max_results=max_results,
            include_answer=True,
            include_raw_content=True,
            include_images=False
        )
        
        # Format the response to match LangChain's output format
        formatted_result = ""
        if "answer" in response:
            formatted_result += f"Answer: {response['answer']}\n\n"
        
        formatted_result += "Search Results:\n\n"
        for i, result in enumerate(response.get("results", [])):
            formatted_result += f"{i+1}. {result.get('title', 'No Title')}\n"
            formatted_result += f"URL: {result.get('url', 'No URL')}\n"
            formatted_result += f"Content: {result.get('content', 'No Content')}\n\n"
        
        return formatted_result
    except ImportError:
        print("ERROR: Neither LangChain nor tavily-python are available.")
        print("Please install the required packages with: pip install 'tavily-python>=0.3.8' 'langchain-community>=0.2.16'")
        return None
    except Exception as e:
        print(f"ERROR searching: {e}")
        return None

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Perform a direct search using the Tavily API.")
    parser.add_argument("query", help="The search query")
    parser.add_argument("--max-results", type=int, default=3, help="Maximum number of results to return")
    parser.add_argument("--search-depth", choices=["basic", "advanced"], default="advanced", help="Search depth")
    
    args = parser.parse_args()
    
    # Perform the search
    results = search_tavily(args.query, args.max_results, args.search_depth)
    
    # Print the results
    if results:
        print("\nSearch Results:")
        print("=" * 80)
        print(results)
        print("=" * 80)
        return 0
    else:
        print("Search failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
