"""
Tools package for the RaderBot agent framework.
"""

from raderbot.tools.basic_tools import get_current_time, get_weather as get_mock_weather
from raderbot.tools.memory_tools import search_past_conversations, store_important_information
from raderbot.tools.mcp_tools import (
    create_home_assistant_toolset,
    create_ha_mcp_enabled_agent
)
from raderbot.tools.mcp_utils import (
    test_home_assistant_connection,
    check_home_assistant_entity,
    list_home_assistant_domains
)
from raderbot.tools.weather_connector import (
    WeatherConnector,
    get_weather,
    get_forecast,
    format_weather_response,
    format_forecast_response
)
from raderbot.tools.web_search_tools import (
    create_tavily_search_tool,
    create_tavily_search_enabled_agent
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
]