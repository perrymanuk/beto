"""Specialized toolsets for different agent types.

This package contains modules that define toolsets for specialized agents,
focusing on specific domains to reduce token usage and improve performance.
"""

from typing import Dict, List, Any, Optional

# Export utility functions for specialized toolsets
from .base_toolset import (
    create_specialized_toolset,
    register_toolset,
    get_toolset,
    get_all_toolsets,
)