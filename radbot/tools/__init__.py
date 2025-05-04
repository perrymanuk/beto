"""
Tools package for Radbot.

This package provides various tools for the Radbot agent.
"""

# Re-export tools from subpackages
from radbot.tools.basic import get_current_time, get_weather, get_weather_details
from radbot.tools.homeassistant import (
    get_ha_client,
    HomeAssistantRESTClient,
    search_ha_entities,
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
)
from radbot.tools.memory import search_past_conversations, store_important_information
from radbot.tools.mcp import (
    create_fileserver_toolset,
    FileServerMCP,
    get_available_mcp_tools,
    convert_to_adk_tool,
)
from radbot.tools.crawl4ai import (
    create_crawl4ai_toolset,
    test_crawl4ai_connection,
    get_crawl4ai_vector_store,
    Crawl4AIVectorStore,
    crawl4ai_two_step,
)
from radbot.tools.shell import execute_shell_command, ALLOWED_COMMANDS, get_shell_tool
from radbot.tools.web_search import (
    create_tavily_search_tool,
    create_tavily_search_enabled_agent,
    TavilySearchResults,
    HAVE_TAVILY,
)

# Keep todo tools as-is since they're already in a directory

__all__ = [
    # Basic tools
    "get_current_time",
    "get_weather",
    "get_weather_details",
    
    # Home Assistant tools
    "get_ha_client",
    "HomeAssistantRESTClient",
    "search_ha_entities",
    "list_ha_entities",
    "get_ha_entity_state",
    "turn_on_ha_entity",
    "turn_off_ha_entity",
    "toggle_ha_entity",
    
    # Memory tools
    "search_past_conversations",
    "store_important_information",
    
    # MCP tools
    "create_fileserver_toolset",
    "FileServerMCP",
    "get_available_mcp_tools", 
    "convert_to_adk_tool",
    
    # Crawl4AI tools
    "create_crawl4ai_toolset",
    "test_crawl4ai_connection",
    "get_crawl4ai_vector_store",
    "Crawl4AIVectorStore",
    "crawl4ai_two_step",
    
    # Shell tools
    "execute_shell_command",
    "ALLOWED_COMMANDS",
    "get_shell_tool",
    
    # Web search tools
    "create_tavily_search_tool",
    "create_tavily_search_enabled_agent",
    "TavilySearchResults",
    "HAVE_TAVILY",
]
