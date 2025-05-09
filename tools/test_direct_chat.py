#!/usr/bin/env python
"""
Test the chat conversation flow with Crawl4AI tool directly.

This script simulates a chat conversation with the model and
checks if the Crawl4AI tool is being handled correctly.
"""

import os
import sys
import logging
import json

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def test_chat_with_crawl4ai():
    """
    Test a chat conversation that uses the Crawl4AI tool.
    
    This simulates what happens when a chat message triggers
    the Crawl4AI tool.
    """
    # Import the necessary components
    from google.genai.types import Content, Part
    from agent import root_agent
    
    logger.info("Setting up the test conversation...")
    
    # Print the agent's tools
    tool_names = []
    for tool in root_agent.tools:
        tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
        tool_names.append(tool_name)
    
    logger.info(f"Available tools: {tool_names}")
    
    # Directly invoke the Crawl4AI tool handler if it exists
    if "crawl4ai_crawl" in tool_names:
        logger.info("Found crawl4ai_crawl tool, invoking it directly...")
        
        for tool in root_agent.tools:
            tool_name = getattr(tool, "name", None) or getattr(tool, "__name__", str(tool))
            if tool_name == "crawl4ai_crawl":
                result = tool(url="https://github.com/google/adk-samples")
                logger.info(f"Direct tool invocation result: {json.dumps(result, indent=2)[:1000]}...")
                break
    else:
        logger.warning("crawl4ai_crawl tool not found")

if __name__ == "__main__":
    test_chat_with_crawl4ai()