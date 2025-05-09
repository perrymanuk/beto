"""
Test script to verify Tavily and LangChain imports.
"""

import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
logger = logging.getLogger()

def test_tavily_imports():
    """Test importing Tavily components."""
    logger.info("Testing Tavily imports...")
    
    try:
        import tavily
        from tavily import TavilyClient
        logger.info(f"✓ tavily-python imported successfully (version: {getattr(tavily, '__version__', 'unknown')})")
        
        # Test creating a client (without API key)
        try:
            # This will fail without API key, but we're just testing imports
            client = TavilyClient(api_key="dummy_key")
            logger.info(f"✓ TavilyClient class can be instantiated")
        except Exception as e:
            if "API key" in str(e):
                logger.info("✓ TavilyClient raised expected API key error (this is normal)")
            else:
                logger.error(f"× TavilyClient initialization error: {e}")
    except ImportError as e:
        logger.error(f"× Failed to import tavily: {e}")
        return False
    
    return True

def test_langchain_imports():
    """Test importing LangChain imports."""
    logger.info("\nTesting LangChain imports...")
    
    try:
        from langchain_community.tools import TavilySearchResults
        logger.info("✓ langchain-community TavilySearchResults imported successfully")
        
        # Test creating a search tool (will fail without API key)
        try:
            # This will fail without API key, but we're just testing imports
            search_tool = TavilySearchResults(max_results=5)
            logger.info("✓ TavilySearchResults class can be instantiated")
        except Exception as e:
            if "API key" in str(e):
                logger.info("✓ TavilySearchResults raised expected API key error (this is normal)")
            else:
                logger.error(f"× TavilySearchResults initialization error: {e}")
    except ImportError as e:
        logger.error(f"× Failed to import langchain-community TavilySearchResults: {e}")
        return False
    
    return True

def test_adk_integration():
    """Test importing ADK components."""
    logger.info("\nTesting ADK integration imports...")
    
    try:
        from google.adk.tools.mcp_tool import MCPToolset
        logger.info("✓ google.adk.tools.mcp_tool.MCPToolset imported successfully")
        
        try:
            from google.adk.tools import FunctionTool
            logger.info("✓ google.adk.tools.FunctionTool imported successfully")
        except ImportError as e:
            logger.error(f"× Failed to import FunctionTool: {e}")
            return False
            
    except ImportError as e:
        logger.error(f"× Failed to import ADK components: {e}")
        return False
    
    return True

def main():
    """Run all import tests."""
    logger.info("=== Testing imports for web search tools ===\n")
    
    tavily_success = test_tavily_imports()
    langchain_success = test_langchain_imports()
    adk_success = test_adk_integration()
    
    logger.info("\n=== Import Test Results ===")
    logger.info(f"Tavily imports: {'SUCCESS' if tavily_success else 'FAILED'}")
    logger.info(f"LangChain imports: {'SUCCESS' if langchain_success else 'FAILED'}")
    logger.info(f"ADK integration: {'SUCCESS' if adk_success else 'FAILED'}")
    
    if tavily_success and langchain_success and adk_success:
        logger.info("\nAll imports successful! The warning in mcp_core.py might be a different issue.")
    else:
        logger.info("\nSome imports failed. This might be the cause of the warning in mcp_core.py.")
    
    # Print Python path to check for path issues
    logger.info("\n=== Python Path ===")
    for path in sys.path:
        logger.info(path)

if __name__ == "__main__":
    main()