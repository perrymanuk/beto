#!/usr/bin/env python
"""
Test script for the new AgentTool approach.

This script demonstrates using the AgentTool approach to interact with sub-agents
rather than using transfer_to_agent.

Usage:
    python -m tools.test_agent_tools
"""

import os
import sys
import logging
import asyncio
from typing import Optional, Any

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Make sure radbot is in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Enable the AgentTool approach
os.environ["RADBOT_USE_AGENT_TOOL"] = "true"

# Ensure code execution and search are enabled
os.environ["RADBOT_ENABLE_ADK_SEARCH"] = "true"
os.environ["RADBOT_ENABLE_ADK_CODE_EXEC"] = "true"

def test_synchronous_tools():
    """Test the synchronous AgentTool wrapper functions."""
    from radbot.tools.agent_tools import search, execute_code, research
    
    # Test search function
    logger.info("Testing search function...")
    try:
        result = search("What is the capital of France?", max_results=2)
        logger.info(f"Search result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing search: {str(e)}")
    
    # Test code execution function
    logger.info("Testing code execution function...")
    try:
        result = execute_code("print('Hello from code execution agent!')", description="Simple test")
        logger.info(f"Code execution result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing code execution: {str(e)}")
    
    # Test research function
    logger.info("Testing research function...")
    try:
        result = research("Python programming best practices")
        logger.info(f"Research result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing research: {str(e)}")

async def test_async_tools():
    """Test the asynchronous AgentTool functions."""
    from radbot.tools.agent_tools import call_search_agent, call_code_execution_agent, call_scout_agent
    
    # Test search agent
    logger.info("Testing async call_search_agent...")
    try:
        result = await call_search_agent("What is the capital of France?", max_results=2)
        logger.info(f"Search result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing async search: {str(e)}")
    
    # Test code execution agent
    logger.info("Testing async call_code_execution_agent...")
    try:
        result = await call_code_execution_agent("print('Hello from code execution agent!')", description="Simple test")
        logger.info(f"Code execution result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing async code execution: {str(e)}")
    
    # Test scout agent
    logger.info("Testing async call_scout_agent...")
    try:
        result = await call_scout_agent("Python programming best practices")
        logger.info(f"Research result length: {len(result) if result else 0} characters")
    except Exception as e:
        logger.error(f"Error testing async research: {str(e)}")

def interactive_test():
    """Interactive test using real prompts."""
    from radbot.tools.agent_tools import search, execute_code, research
    
    print("\n===== INTERACTIVE AGENT TOOL TEST =====\n")
    
    while True:
        print("\nOptions:")
        print("1. Search the web")
        print("2. Execute Python code")
        print("3. Research a topic")
        print("q. Quit")
        
        choice = input("\nEnter your choice (1-3, q): ").strip().lower()
        
        if choice == 'q':
            break
        
        if choice == '1':
            query = input("Enter search query: ")
            print(f"\nSearching for: {query}...")
            result = search(query)
            print("\nSEARCH RESULTS:")
            print("--------------")
            print(result)
            
        elif choice == '2':
            code = input("Enter Python code to execute: ")
            print("\nExecuting code...")
            result = execute_code(code)
            print("\nEXECUTION RESULTS:")
            print("-----------------")
            print(result)
            
        elif choice == '3':
            topic = input("Enter research topic: ")
            print(f"\nResearching: {topic}...")
            result = research(topic)
            print("\nRESEARCH RESULTS:")
            print("----------------")
            print(result)
            
        else:
            print("Invalid choice. Please try again.")

def main():
    """Run the AgentTool tests."""
    logger.info("Running AgentTool tests...")
    
    # Import the agent registry to ensure agents are initialized
    try:
        from radbot.agent.agents import search_agent, code_execution_agent, scout_agent
        
        if search_agent:
            logger.info("Search agent is available")
        else:
            logger.warning("Search agent is not available")
        
        if code_execution_agent:
            logger.info("Code execution agent is available")
        else:
            logger.warning("Code execution agent is not available")
        
        if scout_agent:
            logger.info("Scout agent is available")
        else:
            logger.warning("Scout agent is not available")
    except Exception as e:
        logger.error(f"Error initializing agent registry: {str(e)}")
    
    # Choose test mode based on args
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        interactive_test()
    else:
        # Run synchronous tests
        test_synchronous_tools()
        
        # Run async tests in event loop
        try:
            asyncio.run(test_async_tools())
        except RuntimeError as e:
            if "asyncio.run() cannot be called from a running event loop" in str(e):
                # Handle case where we already have an event loop
                loop = asyncio.get_event_loop()
                loop.run_until_complete(test_async_tools())
            else:
                raise

if __name__ == "__main__":
    main()