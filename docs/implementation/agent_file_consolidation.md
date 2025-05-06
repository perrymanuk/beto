# Agent Implementation Consolidation Plan

## Current Structure

Currently, RadBot has three separate agent.py files that serve different purposes:

1. **/agent.py** (root level)
   - Entry point for ADK web interface
   - Referenced directly in adk.config.json
   - Creates a comprehensive agent with all tools
   - Exposes `root_agent` variable used by web API
   - Focused on web integration with all features

2. **/radbot/agent.py** (module level)
   - Simpler implementation with function-based approach
   - Handles prompt caching and specialized tools
   - Used when directly importing from `radbot.agent`
   - Manages custom tool handlers for file/crawl operations

3. **/radbot/agent/agent.py** (agent package)
   - Core OOP implementation with `RadBotAgent` class and `AgentFactory`
   - Foundation for all agent functionality
   - Used by CLI and specialized agent factories
   - Provides proper encapsulation and extensibility

## Dependencies and Requirements

The following dependencies need to be maintained during refactoring:

1. **ADK web interface** depends on:
   - Root-level `/agent.py` being referenced in adk.config.json
   - `root_agent` variable being exposed for direct import

2. **Web API session management** depends on:
   - Direct import of `root_agent` from root-level agent.py
   - Specific app_name consistency ("beto")

3. **CLI interface** depends on:
   - `RadBotAgent` class from `/radbot/agent/agent.py`
   - Agent factory functions

4. **Specialized agent factories** depend on:
   - Core implementation in `/radbot/agent/agent.py`
   - Extensibility of `RadBotAgent` class

## Consolidation Strategy

We will use a phased approach to consolidate these files while maintaining all dependencies:

### Phase 1: Consolidate Core Implementation

1. Make `/radbot/agent/agent.py` the single source of truth for all core functionality:
   - Ensure `RadBotAgent` class has all necessary functionality
   - Ensure `AgentFactory` can create both web and CLI agents
   - Add a standardized approach for tool registration
   - Add proper session and memory management
   - Standardize on agent names (use "beto" for web, configurable for CLI)

2. Update `/radbot/agent.py` to be a thin wrapper:
   - Import functionality from `/radbot/agent/agent.py`
   - Maintain backwards compatibility for any imports
   - Add deprecation warnings for direct use
   - Forward/delegate all functionality to core implementation

3. Update root `/agent.py` to use consolidated implementation:
   - Import from `/radbot/agent/agent.py` instead of redefining
   - Keep `create_agent()` function for ADK web compatibility
   - Keep exposing `root_agent` variable for web API
   - Focus only on web-specific configuration

### Phase 2: Streamline Agent Creation

1. Standardize agent creation patterns:
   - Create a unified factory approach in `/radbot/agent/agent.py`
   - Support both ADK web and CLI interfaces
   - Handle all common configuration options

2. Update root `/agent.py` to use new factory approach:
   - Replace current implementation with factory calls
   - Add web-specific configuration
   - Ensure backward compatibility with ADK web

3. Update import patterns in dependent code:
   - Encourage importing from `radbot.agent.agent` directly
   - Provide backward compatibility for existing imports

### Phase 3: Final Integration

1. Simplify root `/agent.py` to bare minimum:
   - Keep only what's needed for ADK web compatibility
   - Keep `root_agent` variable
   - All implementation details should be in core files

2. Update documentation:
   - Document new agent structure
   - Document import patterns
   - Update examples

3. Update tests:
   - Ensure all functionality is properly tested
   - Verify backward compatibility

## Implementation Details

### Core Structure in `/radbot/agent/agent.py`

This file should contain:

1. `RadBotAgent` class - Complete implementation with:
   - Session management
   - Tool registration
   - Message processing
   - Memory integration
   - Sub-agent management

2. `AgentFactory` class - Complete factory with methods for:
   - Creating web agents
   - Creating CLI agents
   - Creating specialized agents

3. Helper functions:
   - `create_agent()` - Main entry point for simple agent creation
   - `create_runner()` - Runner creation helper
   - Configuration utilities

### Module Interface in `/radbot/agent.py`

This file should:

1. Import all functionality from `/radbot/agent/agent.py`
2. Re-export necessary components
3. Provide backward compatibility
4. Add any module-specific functionality (like caching)

### Web Entry Point in root `/agent.py`

This file should:

1. Import core functionality from `/radbot/agent/agent.py`
2. Configure web-specific settings
3. Create and expose `root_agent` variable
4. Maintain ADK web compatibility
5. Handle web-specific logging and setup

## Code Examples

### Updated `/radbot/agent/agent.py` (core functionality)

```python
"""
Core agent implementation for RadBot.

This module defines the essential RadBotAgent class and factory functions.
"""
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
SessionService = InMemorySessionService  # Type alias for backward compatibility

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Load environment variables
load_dotenv()

# Standard class implementation...
class RadBotAgent:
    """
    Main agent class for the RadBot framework.
    
    This class encapsulates the ADK agent, runner, and session management.
    It provides a unified interface for interacting with the agent system.
    """
    # Implementation details...

class AgentFactory:
    """Factory class for creating and configuring agents."""
    
    @staticmethod
    def create_web_agent(
        name: str = "beto",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        # Other parameters...
    ) -> Agent:
        """Create an agent specifically for the ADK web interface.
        
        This creates the agent expected by ADK web with proper configuration.
        """
        # Implementation details...
        
    @staticmethod
    def create_cli_agent(
        # Parameters...
    ) -> RadBotAgent:
        """Create an agent for CLI use."""
        # Implementation details...
    
    # Other factory methods...

# Helper functions
def create_agent(
    for_web: bool = False,
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    # Other parameters...
) -> Union[Agent, RadBotAgent]:
    """
    Create a configured RadBot agent.
    
    Args:
        for_web: If True, creates an agent for ADK web interface
        # Other parameters...
        
    Returns:
        Either an ADK Agent (for web) or RadBotAgent instance
    """
    if for_web:
        return AgentFactory.create_web_agent(tools=tools, ...)
    else:
        return AgentFactory.create_cli_agent(tools=tools, ...)
```

### Updated `/radbot/agent.py` (module wrapper)

```python
"""
Module-level agent implementation for RadBot.

This module provides a simplified interface for agent creation.
It delegates to the core implementation in radbot.agent.agent.
"""
# Import from core implementation
from radbot.agent.agent import (
    RadBotAgent, 
    AgentFactory,
    create_agent as _create_agent,
    # Other imports...
)

# Module-specific functionality (like caching)
# ...

# Wrapper function with backward compatibility
def create_agent(tools=None, model=None, **kwargs):
    """
    Create a RadBot agent with necessary tools and configuration.
    
    This function delegates to the core implementation in radbot.agent.agent.
    """
    # Add module-specific functionality like caching
    # ...
    
    # Delegate to core implementation
    return _create_agent(for_web=False, tools=tools, model=model, **kwargs)
```

### Updated root `/agent.py` (web entry point)

```python
"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
The ADK web interface uses this file directly based on the adk.config.json setting.
"""
import logging
import os
from typing import Optional, Any, List

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import core functionality
from radbot.agent.agent import AgentFactory, create_agent as _create_agent

# Import necessary tools
from radbot.tools.basic import get_current_time, get_weather
# Other imports...

# Function required by ADK web interface
def create_agent(tools: Optional[List[Any]] = None):
    """
    Create the agent with all necessary tools.
    
    This is the entry point used by ADK web to create the agent.
    """
    logger.info("Creating agent for ADK web interface")
    
    # Configure web-specific tools
    all_tools = [get_current_time, get_weather]
    # Add other tools...
    
    # Use core factory to create the agent
    return _create_agent(
        for_web=True,
        tools=all_tools,
        name="beto",
        # Other parameters...
    )

# Create a root_agent instance for ADK web to use directly
root_agent = create_agent()
logger.info("Created root_agent instance for direct use by ADK web")
```

## Migration Steps

1. Update `/radbot/agent/agent.py` first:
   - Ensure it has all necessary functionality
   - Add factory methods for different use cases
   - Standardize naming and interfaces

2. Update `/radbot/agent.py` to delegate:
   - Import from core implementation
   - Add backward compatibility
   - Maintain module-specific features

3. Update root `/agent.py` last:
   - Import from core implementation
   - Focus only on web interface
   - Ensure ADK compatibility

4. Test thoroughly:
   - Web interface
   - CLI
   - All specialized agents

5. Update documentation:
   - Update import patterns
   - Document new structure

## Benefits of Consolidation

1. **Single Source of Truth**: Core agent functionality in one place
2. **Reduced Code Duplication**: No repeated implementation across files
3. **Better Maintainability**: Changes only need to be made in one place
4. **Improved Organization**: Clear separation of core, module, and web interfaces
5. **Future Extensibility**: Easier to add new agent types or features

## Challenges and Mitigations

1. **Backward Compatibility**:
   - Keep existing interfaces functioning
   - Add deprecation warnings for future transitions

2. **ADK Web Integration**:
   - Maintain root agent.py for compatibility
   - Ensure root_agent variable is properly exposed

3. **Circular Dependencies**:
   - Carefully design import structure
   - Use late binding where necessary

4. **Testing**:
   - Extensive testing of all use cases
   - Verify backward compatibility