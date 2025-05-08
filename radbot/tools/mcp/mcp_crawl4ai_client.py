#!/usr/bin/env python3
"""
MCP Crawl4AI Client - Migration Notice

IMPORTANT: The direct Crawl4AI integration has been deprecated in favor of using the
MCP server for Crawl4AI. This file remains as a compatibility layer but all the 
actual functionality has been removed.
"""

import logging

logger = logging.getLogger(__name__)

def create_crawl4ai_toolset():
    """
    DEPRECATED - Creates a toolset for Crawl4AI.
    
    This function is deprecated and will now return an empty list. Please use 
    the Crawl4AI MCP server instead via the standard MCP integration.
    
    Returns:
        An empty list to maintain API compatibility
    """
    logger.warning(
        "The direct Crawl4AI integration has been deprecated. "
        "Please use the Crawl4AI MCP server integration instead. "
        "Configure your MCP server in the 'integrations.mcp.servers' section of config.yaml."
    )
    return []

def create_crawl4ai_enabled_agent(*args, **kwargs):
    """
    DEPRECATED - Adds Crawl4AI tools to an agent.
    
    This function is deprecated and will now return the agent as-is.
    Please use the Crawl4AI MCP server instead.
    
    Returns:
        The agent as provided without adding any tools
    """
    logger.warning(
        "The direct Crawl4AI integration has been deprecated. "
        "Please use the Crawl4AI MCP server integration instead."
    )
    
    # Just call the agent factory with the original args
    if args and callable(args[0]):
        agent_factory = args[0]
        base_tools = args[1] if len(args) > 1 else kwargs.get('base_tools')
        return agent_factory(tools=base_tools, **kwargs)
    return None

def test_crawl4ai_connection():
    """
    DEPRECATED - Tests the connection to Crawl4AI.
    
    This function is deprecated and will return a failure result.
    
    Returns:
        A dictionary indicating the connection test failed
    """
    logger.warning(
        "The direct Crawl4AI integration has been deprecated. "
        "Please use the Crawl4AI MCP server integration instead."
    )
    return {
        "success": False,
        "status": "deprecated",
        "message": "The direct Crawl4AI integration has been deprecated. Please use the MCP server integration."
    }

def handle_crawl4ai_tool_call(tool_name, params):
    """
    DEPRECATED - Handle direct tool calls to Crawl4AI.
    
    This function is kept for backward compatibility but will return
    a deprecation message.
    
    Args:
        tool_name: The name of the tool being called
        params: Parameters for the tool call
        
    Returns:
        A deprecation message
    """
    logger.warning(
        f"Tool call to {tool_name} failed: The direct Crawl4AI integration has been deprecated. "
        "Please use the Crawl4AI MCP server integration instead."
    )
    return {
        "success": False,
        "status": "deprecated",
        "message": f"Tool {tool_name} is deprecated. Please use the MCP server implementation.",
        "error": "DEPRECATED_INTEGRATION"
    }

def main():
    """DEPRECATED command line entry point."""
    print("⚠️  DEPRECATED: The direct Crawl4AI integration has been deprecated.")
    print("Please use the Crawl4AI MCP server integration instead.")
    print("Configure your MCP server in the 'integrations.mcp.servers' section of config.yaml.")
    return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())