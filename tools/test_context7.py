#!/usr/bin/env python3
"""
Test script for Context7 integration.

This script tests the Context7 MCP server integration, including
library resolution and documentation retrieval.
"""

import logging
import sys
import os
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path to allow importing radbot modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from radbot.tools.mcp.context7_client import (
    test_context7_connection,
    resolve_library_id,
    get_library_docs,
    create_context7_tools
)

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Popular libraries to test resolution
TEST_LIBRARIES = [
    "react", 
    "python", 
    "tensorflow", 
    "nodejs", 
    "express"
]

def test_library_resolution():
    """
    Test library resolution for multiple libraries.
    
    Returns:
        Dict with test results
    """
    results = {}
    
    for library in TEST_LIBRARIES:
        logger.info(f"Testing resolution for: {library}")
        
        result = resolve_library_id(library)
        success = result.get("success", False)
        
        if success:
            logger.info(f"✅ Successfully resolved {library} to {result.get('library_id', '')}")
        else:
            logger.error(f"❌ Failed to resolve {library}: {result.get('error', 'Unknown error')}")
            
        results[library] = result
        
    return results

def test_documentation_retrieval(library_results):
    """
    Test documentation retrieval for successfully resolved libraries.
    
    Args:
        library_results: Dict of library resolution results
        
    Returns:
        Dict with test results
    """
    results = {}
    
    for library, resolution in library_results.items():
        if not resolution.get("success", False):
            logger.info(f"Skipping {library} (resolution failed)")
            continue
            
        library_id = resolution.get("library_id", "")
        if not library_id:
            logger.info(f"Skipping {library} (no library ID)")
            continue
            
        logger.info(f"Testing documentation retrieval for: {library} ({library_id})")
        
        result = get_library_docs(library_id)
        success = result.get("success", False)
        
        if success:
            doc_length = len(result.get("documentation", ""))
            logger.info(f"✅ Successfully retrieved documentation for {library} ({doc_length} chars)")
        else:
            logger.error(f"❌ Failed to retrieve documentation for {library}: {result.get('error', 'Unknown error')}")
            
        results[library] = result
        
    return results

def main():
    """Main test function."""
    print("\n🔬 Testing Context7 MCP Integration\n")
    
    # Test connection
    print("Testing connection to Context7 MCP server...")
    connection_result = test_context7_connection()
    
    if connection_result.get("success", False):
        print(f"✅ Connection successful!")
        print(f"Library ID: {connection_result.get('library_id', '')}")
    else:
        print(f"❌ Connection failed: {connection_result.get('message', 'Unknown error')}")
        print(f"Error: {connection_result.get('error', '')}")
        return 1
        
    # Get tools
    print("\nCreating Context7 tools...")
    tools = create_context7_tools()
    print(f"✅ Created {len(tools)} tools")
    
    # Test library resolution
    print("\nTesting library resolution...")
    resolution_results = test_library_resolution()
    
    successful_resolutions = sum(1 for r in resolution_results.values() if r.get("success", False))
    print(f"\n📊 Library Resolution: {successful_resolutions}/{len(resolution_results)} successful")
    
    # Test documentation retrieval
    print("\nTesting documentation retrieval...")
    docs_results = test_documentation_retrieval(resolution_results)
    
    successful_docs = sum(1 for r in docs_results.values() if r.get("success", False))
    if docs_results:
        print(f"\n📊 Documentation Retrieval: {successful_docs}/{len(docs_results)} successful")
    
    # Summary
    print("\n📋 Summary:")
    print(f"- Connection: {'✅' if connection_result.get('success', False) else '❌'}")
    print(f"- Tool Creation: {'✅' if tools else '❌'}")
    print(f"- Library Resolution: {'✅' if successful_resolutions > 0 else '❌'} ({successful_resolutions}/{len(resolution_results)})")
    print(f"- Documentation Retrieval: {'✅' if successful_docs > 0 else '❌'} ({successful_docs}/{len(docs_results) if docs_results else 0})")
    
    success = (
        connection_result.get("success", False) and 
        tools and 
        successful_resolutions > 0 and 
        successful_docs > 0
    )
    
    if success:
        print("\n✅ All tests passed! Context7 integration is working properly.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the logs above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())