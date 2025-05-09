"""
Session management for RadBot web interface.

This module handles session management for the RadBot web interface.
It creates and manages ADK Runner instances directly with the root agent from agent.py.

This file has been split into smaller modules in the session/ directory.
"""

# Export components from session modules
from radbot.web.api.session.session_runner import SessionRunner
from radbot.web.api.session.session_manager import SessionManager, get_session_manager
from radbot.web.api.session.dependencies import get_or_create_runner_for_session
from radbot.web.api.session.memory_api import memory_router, MemoryStoreRequest

# Export all key components
__all__ = [
    'SessionRunner',
    'SessionManager',
    'get_session_manager',
    'get_or_create_runner_for_session',
    'memory_router',
    'MemoryStoreRequest'
]
