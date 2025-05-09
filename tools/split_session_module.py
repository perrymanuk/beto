#!/usr/bin/env python3
"""
Split the web/api/session.py file into smaller modules.

This script splits the large session.py file into smaller modules
for better maintainability.
"""

import logging
import os
import sys
import re
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def create_directory_if_not_exists(path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(path):
        os.makedirs(path)
        logger.info(f"Created directory: {path}")

def split_session_module():
    """
    Split the session.py file into smaller modules.
    
    This function splits the large session.py file into smaller modules
    for better maintainability.
    """
    # Find the session.py file
    session_py_path = os.path.join(os.path.dirname(__file__), '..', 'radbot', 'web', 'api', 'session.py')
    
    if not os.path.exists(session_py_path):
        logger.error(f"Could not find session.py at {session_py_path}")
        return False
    
    logger.info(f"Found session.py at {session_py_path}")
    
    # Define the output directory
    output_dir = os.path.join(os.path.dirname(session_py_path), 'session')
    create_directory_if_not_exists(output_dir)
    
    # Read the file
    with open(session_py_path, 'r') as f:
        content = f.read()
    
    # Extract the imports section
    imports_pattern = r'^"""(?:.*?)""".*?(?=class|def)'
    imports_match = re.search(imports_pattern, content, re.DOTALL | re.MULTILINE)
    if not imports_match:
        logger.error("Could not extract imports section")
        return False
    
    imports_section = imports_match.group(0)
    
    # Split into component files
    
    # 1. session_runner.py - The main SessionRunner class
    runner_pattern = r'class SessionRunner:(?:.*?)def reset_session\(.*?\):(?:.*?)return (?:True|False)'
    runner_match = re.search(runner_pattern, content, re.DOTALL)
    if not runner_match:
        logger.error("Could not extract SessionRunner class")
        return False
    
    runner_class = runner_match.group(0)
    
    # 2. session_manager.py - SessionManager class
    manager_pattern = r'class SessionManager:(?:.*?)def remove_session\(.*?\):(?:.*?)logger\..*?'
    manager_match = re.search(manager_pattern, content, re.DOTALL)
    if not manager_match:
        logger.error("Could not extract SessionManager class")
        return False
    
    manager_class = manager_match.group(0)
    
    # 3. event_processing.py - Event processing functions
    event_processing_pattern = r'def _process_tool_call_event\(.*?\):(?:.*?)def _process_agent_transfer_event\(.*?\):(?:.*?)def _process_planner_event\(.*?\):(?:.*?)def _process_model_response_event\(.*?\):(?:.*?)def _process_generic_event\(.*?\):(?:.*?)def _get_plan_step_summary\(.*?\):(?:.*?)def _get_event_details\(.*?\):(?:.*?)'
    event_processing_match = re.search(event_processing_pattern, content, re.DOTALL)
    if not event_processing_match:
        logger.error("Could not extract event processing functions")
        return False
    
    event_processing_funcs = event_processing_match.group(0)
    
    # 4. utils.py - Utility functions - FIXED PATTERN
    utils_pattern = r'def _extract_response_from_event\(.*?\):(?:.*?)def _process_response_text\(.*?\):(?:.*?)def _get_current_timestamp\(.*?\):(?:.*?)def _get_event_type\(.*?\):(?:.*?)'
    utils_match = re.search(utils_pattern, content, re.DOTALL)
    if not utils_match:
        logger.error("Could not extract utility functions")
        return False
    
    utils_funcs = utils_match.group(0)
    
    # 5. memory_api.py - Memory API - FIXED PATTERN 
    memory_api_pattern = r'class MemoryStoreRequest\(BaseModel\):(?:.*?)memory_router = APIRouter\((?:.*?)@memory_router\.post\((?:.*?)async def store_memory\((?:.*?)\s*except Exception as e:'
    memory_api_match = re.search(memory_api_pattern, content, re.DOTALL)
    if not memory_api_match:
        logger.error("Could not extract memory API")
        return False
    
    # Get the memory API text plus the final exception handling
    memory_api_text = memory_api_match.group(0)
    
    # Add the last part of the memory API function
    memory_end_pattern = r'except Exception as e:(?:.*?)raise HTTPException\(status_code=500.*?\)'
    memory_end_match = re.search(memory_end_pattern, content, re.DOTALL)
    
    if memory_end_match:
        memory_api = memory_api_text + memory_end_match.group(0)
    else:
        memory_api = memory_api_text
    
    # 6. dependencies.py - Dependencies for FastAPI - FIXED PATTERN
    dependencies_pattern = r'def get_session_manager\(\) -> SessionManager:(?:.*?)async def get_or_create_runner_for_session\((?:.*?)\s*return runner'
    dependencies_match = re.search(dependencies_pattern, content, re.DOTALL)
    if not dependencies_match:
        logger.error("Could not extract dependencies")
        return False
    
    # Get the dependencies text plus the final exception handling
    dependencies_text = dependencies_match.group(0)
    
    # Add the last part of the get_or_create_runner_for_session function
    dependencies_end_pattern = r'return runner(?:.*?)except Exception as e:(?:.*?)raise'
    dependencies_end_match = re.search(dependencies_end_pattern, content, re.DOTALL)
    
    if dependencies_end_match:
        dependencies = dependencies_text + dependencies_end_match.group(0)
    else:
        dependencies = dependencies_text
    
    # 7. safely_serialize.py - Utility function for serialization
    serialize_pattern = r'def _safely_serialize\(.*?\):(?:.*?)return f"<Unserializable object of type {type\(obj\)\.__name__}>"'
    serialize_match = re.search(serialize_pattern, content, re.DOTALL)
    if not serialize_match:
        logger.error("Could not extract _safely_serialize function")
        return False
    
    safely_serialize_func = serialize_match.group(0)
    
    # 8. try_load_mcp_tools.py - MCP tools loading function
    mcp_tools_pattern = r'def _try_load_mcp_tools\(.*?\):(?:.*?)except Exception as e:(?:.*?)logger\.warning\(f"Error loading MCP tools: {str\(e\)}"\)'
    mcp_tools_match = re.search(mcp_tools_pattern, content, re.DOTALL)
    if not mcp_tools_match:
        logger.error("Could not extract _try_load_mcp_tools function")
        return False
    
    mcp_tools_func = mcp_tools_match.group(0)
    
    # Write the component files
    
    # 1. __init__.py
    with open(os.path.join(output_dir, '__init__.py'), 'w') as f:
        f.write(f'''"""
Session management package for RadBot web interface.

This package manages sessions for the RadBot web interface.
It creates and manages ADK Runner instances with the root agent.
"""

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
''')
    
    # 2. session_runner.py
    with open(os.path.join(output_dir, 'session_runner.py'), 'w') as f:
        f.write(f'''"""
Session runner for RadBot web interface.

This module provides the SessionRunner class for managing ADK Runner instances.
"""

import logging
import os
import sys
import json
from typing import Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import needed ADK components
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from google.genai.types import Content, Part

# Import root_agent directly from agent.py
from agent import root_agent

# Import the malformed function handler
from radbot.web.api.malformed_function_handler import extract_text_from_malformed_function

# Import utility functions
from radbot.web.api.session.utils import (
    _extract_response_from_event,
    _process_response_text,
    _get_current_timestamp,
    _get_event_type
)

# Import event processing functions
from radbot.web.api.session.event_processing import (
    _process_tool_call_event,
    _process_agent_transfer_event,
    _process_planner_event,
    _process_model_response_event,
    _process_generic_event,
    _get_plan_step_summary,
    _get_event_details
)

# Import serialization function
from radbot.web.api.session.serialization import _safely_serialize

# Import MCP tools loader
from radbot.web.api.session.mcp_tools import _try_load_mcp_tools

{runner_class}
''')
    
    # 3. session_manager.py
    with open(os.path.join(output_dir, 'session_manager.py'), 'w') as f:
        f.write(f'''"""
Session manager for RadBot web interface.

This module provides the SessionManager class for managing multiple sessions.
"""

import asyncio
import logging
from typing import Dict, Optional

from radbot.web.api.session.session_runner import SessionRunner

# Set up logging
logger = logging.getLogger(__name__)

{manager_class}

# Singleton session manager instance
_session_manager = SessionManager()

# Session manager dependency
def get_session_manager() -> SessionManager:
    """Get the session manager."""
    return _session_manager
''')
    
    # 4. event_processing.py
    with open(os.path.join(output_dir, 'event_processing.py'), 'w') as f:
        f.write(f'''"""
Event processing for RadBot web interface.

This module provides functions for processing ADK events.
"""

import logging
from typing import Dict, Any

# Import serialization function
from radbot.web.api.session.serialization import _safely_serialize

# Set up logging
logger = logging.getLogger(__name__)

{event_processing_funcs}
''')
    
    # 5. utils.py
    with open(os.path.join(output_dir, 'utils.py'), 'w') as f:
        f.write(f'''"""
Utility functions for RadBot web interface.

This module provides utility functions for the session management.
"""

import logging
import re
import json
from html import escape
from datetime import datetime
from typing import Optional, Any

# Set up logging
logger = logging.getLogger(__name__)

{utils_funcs}
''')
    
    # 6. memory_api.py
    with open(os.path.join(output_dir, 'memory_api.py'), 'w') as f:
        f.write(f'''"""
Memory API for RadBot web interface.

This module provides the Memory API for storing and retrieving memories.
"""

import logging
from typing import Dict, Any

from fastapi import Depends, APIRouter, HTTPException, Body
from pydantic import BaseModel

from radbot.web.api.session.session_manager import SessionManager, get_session_manager

# Set up logging
logger = logging.getLogger(__name__)

{memory_api}
''')
    
    # 7. dependencies.py
    with open(os.path.join(output_dir, 'dependencies.py'), 'w') as f:
        f.write(f'''"""
Dependencies for RadBot web interface.

This module provides FastAPI dependencies for the web interface.
"""

import logging
from typing import Optional

from fastapi import Depends

from radbot.web.api.session.session_runner import SessionRunner
from radbot.web.api.session.session_manager import SessionManager, get_session_manager

# Set up logging
logger = logging.getLogger(__name__)

{dependencies}
''')
    
    # 8. serialization.py
    with open(os.path.join(output_dir, 'serialization.py'), 'w') as f:
        f.write(f'''"""
Serialization utilities for RadBot web interface.

This module provides serialization utilities for the session management.
"""

import logging
import json
from typing import Any

# Set up logging
logger = logging.getLogger(__name__)

{safely_serialize_func}
''')
    
    # 9. mcp_tools.py
    with open(os.path.join(output_dir, 'mcp_tools.py'), 'w') as f:
        f.write(f'''"""
MCP tools utilities for RadBot web interface.

This module provides utilities for loading MCP tools.
"""

import logging
from typing import List, Any

# Set up logging
logger = logging.getLogger(__name__)

{mcp_tools_func}
''')
    
    # Create the new session.py that imports from the components
    with open(session_py_path, 'w') as f:
        f.write('''"""
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
''')
    
    logger.info(f"Successfully split session.py into modules in {output_dir}")
    return True

def main():
    """Split session module."""
    success = split_session_module()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())