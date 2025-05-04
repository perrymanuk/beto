"""
Web search tools package.

This package provides the functionality for web search capabilities.
"""

from radbot.tools.web_search.web_search_tools import (
    create_tavily_search_tool,
    create_tavily_search_enabled_agent
)
# Importing from the fixed version as it might be the preferred one
from radbot.tools.web_search.web_search_tools_fixed import (
    TavilySearchResults,
    HAVE_TAVILY
)

__all__ = [
    "create_tavily_search_tool",
    "create_tavily_search_enabled_agent",
    "TavilySearchResults",
    "HAVE_TAVILY",
]
