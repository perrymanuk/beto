# Base Agent Structure Implementation

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document details the implementation of the core agent structure using Google's Agent Development Kit (ADK).

## Core Agent Components

The agent framework consists of several key components:

1. Main Coordinator Agent
2. ADK Runner
3. Session Management
4. Initial Tool Integration

## Consolidated Agent Implementation

RadBot has undergone an agent consolidation process to streamline the agent structure across the codebase. Previously, the system had three separate agent.py files in different locations that served different purposes. Now, the agent implementation has been consolidated into a more coherent structure:

1. `/radbot/agent/agent.py`: The primary implementation and single source of truth
2. `/radbot/agent.py`: A module-level wrapper providing backward compatibility
3. `/agent.py` (root level): A specialized web entry point for ADK integration

This consolidated structure provides better maintainability, reduces code duplication, and clarifies responsibility boundaries while maintaining backward compatibility.

### Core Implementation in `/radbot/agent/agent.py`

The core implementation file contains the main `RadBotAgent` class, an `AgentFactory` class, and various helper functions:

```python
# radbot/agent/agent.py (excerpt)

"""
Core agent implementation for RadBot.

This module defines the essential RadBotAgent class and factory functions for the RadBot framework.
It serves as the single source of truth for all agent functionality.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from google.protobuf.json_format import MessageToDict

# Type alias for backward compatibility
SessionService = InMemorySessionService  

# Load environment variables
load_dotenv()

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

class RadBotAgent:
    """
    Main agent class for the RadBot framework.
    
    This class encapsulates the ADK agent, runner, and session management.
    It provides a unified interface for interacting with the agent system.
    """
    
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        tools: Optional[List[Any]] = None,
        model: Optional[str] = None,
        name: str = "beto",
        instruction: Optional[str] = None,
        instruction_name: Optional[str] = "main_agent",
        config: Optional[ConfigManager] = None,
        memory_service: Optional[Any] = None,
        app_name: str = "beto"
    ):
        """
        Initialize the RadBot agent.
        
        Args:
            session_service: Optional custom session service for conversation state
            tools: Optional list of tools to provide to the agent
            model: Optional model name (defaults to config's main_model if not provided)
            name: Name for the agent (default: beto)
            instruction: Optional explicit instruction string (overrides instruction_name)
            instruction_name: Optional name of instruction to load from config
            config: Optional ConfigManager instance (uses global if not provided)
            memory_service: Optional custom memory service (tries to create one if None)
            app_name: Application name for session management (default: beto)
        """
        # Implementation details...
    
    def add_tool(self, tool: Any) -> None:
        """Add a tool to the agent's capabilities."""
        # Implementation details...
    
    def add_tools(self, tools: List[Any]) -> None:
        """Add multiple tools to the agent's capabilities."""
        # Implementation details...
    
    def process_message(self, user_id: str, message: str) -> str:
        """Process a user message and return the agent's response."""
        # Implementation details...

    def add_sub_agent(self, sub_agent: Agent) -> None:
        """Add a sub-agent to the main agent."""
        # Implementation details...
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get the current configuration of the agent."""
        # Implementation details...
    
    def update_instruction(self, new_instruction: str = None, instruction_name: str = None) -> None:
        """Update the agent's instruction."""
        # Implementation details...
    
    def update_model(self, new_model: str) -> None:
        """Update the agent's model."""
        # Implementation details...
    
    def reset_session(self, user_id: str) -> None:
        """Reset a user's session."""
        # Implementation details...
    
    def register_tool_handlers(self):
        """Register common tool handlers for the agent."""
        # Implementation details...


class AgentFactory:
    """Factory class for creating and configuring agents."""

    @staticmethod
    def create_root_agent(
        name: str = "beto",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        instruction_name: str = "main_agent",
        config: Optional[ConfigManager] = None
    ) -> Agent:
        """Create the main root agent."""
        # Implementation details...

    @staticmethod
    def create_sub_agent(
        name: str,
        description: str,
        instruction_name: str,
        tools: Optional[List] = None,
        model: Optional[str] = None,
        config: Optional[ConfigManager] = None
    ) -> Agent:
        """Create a sub-agent with appropriate model and configuration."""
        # Implementation details...

    @staticmethod
    def create_web_agent(
        name: str = "beto",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        instruction_name: str = "main_agent",
        config: Optional[ConfigManager] = None,
        register_tools: bool = True
    ) -> Agent:
        """Create an agent specifically for the ADK web interface."""
        # Implementation details...


def create_runner(
    agent: Agent, 
    app_name: str = "beto",
    session_service: Optional[SessionService] = None
) -> Runner:
    """Create an ADK Runner with the specified agent."""
    # Implementation details...


def create_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    model: Optional[str] = None,
    instruction_name: str = "main_agent",
    name: str = "beto",
    config: Optional[ConfigManager] = None,
    include_memory_tools: bool = True,
    for_web: bool = False,
    register_tools: bool = True,
    app_name: str = "beto"
) -> Union[RadBotAgent, Agent]:
    """Create a configured RadBot agent."""
    # Implementation details...


def create_core_agent_for_web(tools: Optional[List[Any]] = None, name: str = "beto", app_name: str = "beto") -> Agent:
    """
    Create an ADK Agent for web interface with all necessary configurations.
    This is the function used by the root agent.py.
    """
    # Implementation details...
```

### Module Interface in `/radbot/agent.py`

The module-level agent.py serves as a wrapper around the core implementation, providing backward compatibility:

```python
# radbot/agent.py (excerpt)

"""
Module-level agent implementation for RadBot.

This module provides a simplified interface for agent creation.
It delegates to the core implementation in radbot.agent.agent.
"""
import logging
import os
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Import core components from the agent package
from radbot.agent.agent import (
    RadBotAgent, 
    AgentFactory,
    create_agent as _create_agent,
    create_runner,
    SessionService
)

# Import useful ADK components for direct use
from google.adk.agents import Agent, QueryResponse
from google.adk.tools.tool_context import ToolContext
from google.protobuf.json_format import MessageToDict

# Define agent error handler for convenience
def agent_error_handler(e: Exception) -> Dict[str, Any]:
    """Handle agent errors by returning a user-friendly error message."""
    # Implementation details...


def create_agent(
    model: str = None,
    tools: Optional[List[Any]] = None,
    session_service: Optional[SessionService] = None,
    instruction_name: str = "main_agent",
    name: str = "beto",
    include_memory_tools: bool = True,
    register_tools: bool = True,
    for_web: bool = False
) -> Union[RadBotAgent, Agent]:
    """
    Create a RadBot agent with all necessary tools and configuration.
    
    This function is a wrapper around the core implementation in radbot.agent.agent.
    """
    # We delegate the implementation to the core function
    return _create_agent(
        session_service=session_service,
        tools=tools,
        model=model,
        instruction_name=instruction_name,
        name=name,
        include_memory_tools=include_memory_tools,
        register_tools=register_tools,
        for_web=for_web,
        app_name="beto"
    )


# Module-specific functions for caching
def register_cache_callbacks(agent: RadBotAgent) -> RadBotAgent:
    """Register prompt caching callbacks with the agent."""
    # Implementation details...

# Re-export these components for backward compatibility
from radbot.agent.agent import RadBotAgent, AgentFactory, create_runner
```

### Web Entry Point in root `/agent.py`

The root-level agent.py file serves as the entry point for the ADK web interface:

```python
# agent.py (root level) (excerpt)

"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
The ADK web interface uses this file directly based on the adk.config.json setting.
"""

import logging
import os
from typing import Optional, Any, List, Dict, Union

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import ADK components
from google.adk.agents import Agent
from radbot.config import config_manager

# Import the core agent implementation
from radbot.agent.agent import create_core_agent_for_web

# Import the ADK's built-in transfer_to_agent tool
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

# Import various tools...

def create_agent(tools: Optional[List[Any]] = None, app_name: str = "beto"):
    """
    Create the agent with all necessary tools.
    
    This is the entry point used by ADK web to create the agent.
    """
    logger.info("Creating agent for ADK web interface")
    
    # Add various tools...
    
    # Use the core implementation to create the web agent with explicit app_name
    agent = create_core_agent_for_web(tools=all_tools, name="beto", app_name="beto")
    
    # Customize the agent for web interface...
    
    return agent

# Create a root_agent instance for ADK web to use directly with explicit app_name
root_agent = create_agent(app_name="beto")
logger.info(f"Created root_agent instance for ADK web with name '{root_agent.name}'")
```

## Key Design Considerations of Consolidated Structure

### Single Source of Truth

The consolidated structure establishes `/radbot/agent/agent.py` as the single source of truth for all agent functionality. This eliminates code duplication and ensures that changes only need to be made in one place.

### Role Separation

Each file now has a clear, distinct role:

1. **Core Implementation** (`/radbot/agent/agent.py`):
   - Contains the complete `RadBotAgent` class implementation
   - Provides the `AgentFactory` for creating different types of agents
   - Defines core helper functions
   - Handles all low-level functionality

2. **Module Interface** (`/radbot/agent.py`):
   - Provides backward compatibility
   - Re-exports necessary components
   - Adds module-specific functionality (like caching)
   - Delegates to the core implementation

3. **Web Entry Point** (`/agent.py` at root level):
   - Referenced directly in adk.config.json
   - Focuses exclusively on web interface integration
   - Creates and exposes the `root_agent` variable required by ADK
   - Configures web-specific tools and settings

### Unified Factory Approach

The consolidated structure uses the `AgentFactory` class to standardize agent creation:

- `create_root_agent()`: Creates the main agent
- `create_sub_agent()`: Creates specialized sub-agents
- `create_web_agent()`: Creates agents for the ADK web interface

This factory approach provides consistent configuration across different agent types while allowing for specialized settings when needed.

### Backward Compatibility

The consolidation maintains backward compatibility through:

1. Wrapper functions that delegate to core implementations
2. Re-exporting necessary components
3. Maintaining the same interface and function signatures
4. Preserving the expected variables (like `root_agent`) for direct imports

## Benefits of the Consolidated Structure

- **Reduced Code Duplication**: Core functionality is defined once, eliminating redundancies
- **Improved Maintainability**: Changes only need to be made in one location
- **Clearer Responsibility Boundaries**: Each file has a well-defined purpose
- **Better Extensibility**: The factory pattern makes it easier to add new agent types
- **Consistent Configuration**: Agent settings are applied uniformly across different contexts

## Agent Components and Interactions

### RadBotAgent Class

The main `RadBotAgent` class encapsulates:

- An ADK `Agent` instance (`self.root_agent`)
- An ADK `Runner` for processing messages
- Session management via `InMemorySessionService` (or custom implementation)
- Memory service integration
- Tool registration
- Sub-agent management

### AgentFactory Class

The `AgentFactory` class provides methods for creating:

- Root agents for general use
- Sub-agents for specialized tasks
- Web agents specifically for the ADK web interface

Each factory method applies consistent configuration while allowing for customization.

### Helper Functions

Helper functions provide simplified interfaces for common operations:

- `create_agent()`: Main function for creating a properly configured agent
- `create_runner()`: Creates a runner with the specified agent and session service
- `create_core_agent_for_web()`: Creates an agent specifically for the ADK web interface

## Integration with ADK

The root-level `/agent.py` file is referenced directly in the `adk.config.json` file:

```json
{
  "agent_config": {
    "agent_module": "agent"
  }
}
```

This tells ADK to use the `root_agent` variable exported from this file as the main agent for the web interface.

## Key Features

- **Centralized Configuration**: Agent settings are managed through a unified `ConfigManager`
- **Flexible Tool Integration**: Tools can be added dynamically or at initialization
- **Memory Integration**: Built-in support for persistent memory through `memory_service`
- **Session Management**: Stateful conversations through `session_service`
- **Sub-Agent Hierarchy**: Support for specialized sub-agents with bidirectional communication
- **Error Handling**: Comprehensive error handling throughout
- **Logging**: Detailed logging for debugging and monitoring

## Next Steps

With the consolidated agent structure in place, future enhancements could include:

1. Further optimization of tool registration
2. Enhanced sub-agent communication
3. More sophisticated prompt management
4. Advanced memory integration
5. Improved agent configuration UI