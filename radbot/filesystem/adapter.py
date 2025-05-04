"""
Adapter for compatibility with the previous MCP fileserver implementation.

This module provides functions that maintain compatibility with code
that was using the previous MCP fileserver implementation.
"""

import os
import logging
from typing import List, Dict, Any, Optional

from google.adk.tools import FunctionTool

from radbot.filesystem.integration import create_filesystem_tools

logger = logging.getLogger(__name__)


def get_filesystem_config() -> tuple[str, bool, bool]:
    """
    Get the filesystem configuration from environment variables.
    
    Compatible with previous MCP fileserver environment variable names.

    Returns:
        Tuple of (root_dir, allow_write, allow_delete)
    """
    root_dir = os.environ.get("MCP_FS_ROOT_DIR", os.path.expanduser("~"))
    allow_write = os.environ.get("MCP_FS_ALLOW_WRITE", "false").lower() == "true"
    allow_delete = os.environ.get("MCP_FS_ALLOW_DELETE", "false").lower() == "true"
    
    logger.info(
        f"Filesystem Config: root_dir={root_dir}, allow_write={allow_write}, allow_delete={allow_delete}"
    )
    
    return root_dir, allow_write, allow_delete


def create_fileserver_toolset() -> List[FunctionTool]:
    """
    Create the filesystem tools using previous MCP fileserver environment variables.
    
    This function maintains compatibility with code that was using the
    previous MCP fileserver implementation.

    Returns:
        List of FunctionTool instances
    """
    root_dir, allow_write, allow_delete = get_filesystem_config()
    
    logger.info(
        f"Creating filesystem tools with root_dir={root_dir}, "
        f"allow_write={allow_write}, allow_delete={allow_delete}"
    )
    
    # Create the tools with the configured directories and permissions
    return create_filesystem_tools(
        allowed_directories=[root_dir],
        enable_write=allow_write,
        enable_delete=allow_delete
    )
