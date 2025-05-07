"""
ADK built-in tools integration.

This module provides integration with Google ADK's built-in tools 
like google_search and built_in_code_execution.
"""

from .search_tool import create_search_agent, register_search_agent
from .code_execution_tool import create_code_execution_agent, register_code_execution_agent

__all__ = [
    'create_search_agent',
    'register_search_agent',
    'create_code_execution_agent',
    'register_code_execution_agent'
]
