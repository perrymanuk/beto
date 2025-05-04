"""
MCP tools package.

This package provides the functionality for interacting with Model Context Protocol servers.
"""

# Import Event from ADK 0.3.0
from google.adk.events import Event

from radbot.tools.mcp.mcp_crawl4ai_client import create_crawl4ai_toolset, test_crawl4ai_connection
from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset, handle_fileserver_tool_call
from radbot.tools.mcp.mcp_fileserver_server import FileServerMCP
from radbot.tools.mcp.mcp_tools import get_available_mcp_tools
from radbot.tools.mcp.mcp_utils import convert_to_adk_tool

__all__ = [
    "Event",
    "create_crawl4ai_toolset",
    "test_crawl4ai_connection",
    "create_fileserver_toolset",
    "handle_fileserver_tool_call",
    "FileServerMCP",
    "get_available_mcp_tools",
    "convert_to_adk_tool",
]
