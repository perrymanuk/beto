"""
Tools package for the radbot agent framework.
"""

from radbot.tools.basic_tools import get_current_time, get_weather as get_mock_weather
from radbot.tools.memory_tools import search_past_conversations, store_important_information
from radbot.tools.mcp_tools import (
    create_home_assistant_toolset,
    create_ha_mcp_enabled_agent
)
from radbot.tools.mcp_utils import (
    test_home_assistant_connection,
    check_home_assistant_entity,
    list_home_assistant_domains
)
from radbot.tools.weather_connector import (
    WeatherConnector,
    get_weather,
    get_forecast,
    format_weather_response,
    format_forecast_response
)
from radbot.tools.web_search_tools import (
    create_tavily_search_tool,
    create_tavily_search_enabled_agent
)
from radbot.tools.mcp_crawl4ai_client import (
    create_crawl4ai_toolset,
    create_crawl4ai_enabled_agent,
    test_crawl4ai_connection
)
from radbot.tools.todo.todo_tools import (
    ALL_TOOLS as TODO_TOOLS,
    add_task_tool,
    list_tasks_tool,
    complete_task_tool,
    remove_task_tool,
    init_database as init_todo_database
)

# Export tools for easy import
__all__ = [
    # Basic tools
    'get_current_time', 
    'get_mock_weather',
    'get_weather',
    
    # Memory tools
    'search_past_conversations',
    'store_important_information',
    
    # MCP tools
    'create_home_assistant_toolset',
    'create_ha_mcp_enabled_agent',
    'test_home_assistant_connection',
    'check_home_assistant_entity',
    'list_home_assistant_domains',
    
    # Web search tools
    'create_tavily_search_tool',
    'create_tavily_search_enabled_agent',
    
    # Weather connector
    'WeatherConnector',
    'get_forecast',
    'format_weather_response',
    'format_forecast_response',
    
    # Crawl4AI tools
    'create_crawl4ai_toolset',
    'create_crawl4ai_enabled_agent',
    'test_crawl4ai_connection',
    
    # Todo tools
    'TODO_TOOLS',
    'add_task_tool',
    'list_tasks_tool',
    'complete_task_tool',
    'remove_task_tool',
    'init_todo_database',
]