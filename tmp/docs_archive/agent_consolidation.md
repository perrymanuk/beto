# Agent Framework Consolidation

## Overview

This document explains the consolidation of the agent implementation files in the RadBot framework. Previously, there were three separate agent.py files with overlapping functionality but different purposes:

1. **/agent.py** (root): Entry point for ADK web interface
2. **/radbot/agent.py**: Module-level implementation with caching functionality
3. **/radbot/agent/agent.py**: Core implementation with class structure

The consolidation refactors these files to have a single source of truth while maintaining backward compatibility.

## Consolidated Architecture

The new architecture follows a layered approach:

### 1. Core Implementation (`/radbot/agent/agent.py`)

This file contains the fundamental agent implementation:
- `RadBotAgent` class - Complete OOP implementation with:
  - Session management
  - Tool registration
  - Message processing
  - Memory integration
  - Sub-agent management
- `AgentFactory` class - Factory methods for different agent types:
  - `create_root_agent()` - Creates a base agent
  - `create_sub_agent()` - Creates specialized sub-agents
  - `create_web_agent()` - Creates agents for web interface
- Helper functions:
  - `create_agent()` - Main entry point for agent creation
  - `create_runner()` - Creates ADK Runners
  - `create_core_agent_for_web()` - Special function for web interface

### 2. Module Interface (`/radbot/agent.py`)

This file serves as a wrapper around the core implementation:
- Imports core functionality from `/radbot/agent/agent.py`
- Re-exports necessary components for backward compatibility
- Provides module-specific functionality (like caching)
- Offers simplified interface through a `create_agent()` function that delegates to the core implementation

### 3. Web Entry Point (`/agent.py`)

This file remains as the ADK web entry point:
- Imports the core functionality from `/radbot/agent/agent.py`
- Configures web-specific tools and settings
- Exposes the `create_agent()` function for ADK web compatibility
- Creates and exposes the `root_agent` variable used by the web API

## Benefits of Consolidation

1. **Single Source of Truth**: Core agent functionality lives in one place
2. **Reduced Code Duplication**: No repeated implementation across files
3. **Better Maintainability**: Changes only need to be made in one place
4. **Improved Organization**: Clear separation of core, module, and web interfaces
5. **Future Extensibility**: Easier to add new agent types or features

## Usage Guidelines

### For General Usage

Import from the module-level package:

```python
from radbot.agent import create_agent

agent = create_agent(
    name="my_agent",
    tools=[my_tool1, my_tool2],
    instruction_name="custom_instruction"
)
```

### For Direct ADK Web Interface

The root agent.py file is used automatically by the ADK web interface through adk.config.json. No changes to import patterns are needed.

### For Advanced Usage

Import specific components from the core package:

```python
from radbot.agent.agent import RadBotAgent, AgentFactory

# Create a specialized agent with the factory
agent = AgentFactory.create_sub_agent(
    name="specialized_agent",
    description="A specialized agent for specific tasks",
    instruction_name="specialized_instruction",
    tools=[specialized_tool1, specialized_tool2]
)
```

## Technical Implementation Details

### Import Structure

The import structure maintains backward compatibility:

1. Core implementation defines all classes and functions
2. Module interface re-exports everything needed for existing code
3. Web entry point imports only what it needs

### Tool Registration

Tool registration is standardized across all agent types:

1. Core implementation defines a `register_tool_handlers()` method
2. Web agents register tools through the factory
3. Custom tools can be registered through the `add_tool()` method

### Memory Service

Memory handling is centralized:

1. Memory service creation is part of the `RadBotAgent` initialization
2. Web agents get memory service configured automatically
3. Tool contexts are configured consistently

## Future Improvements

- Further standardization of tool registration
- Enhanced factory methods for different agent types
- Better error handling and recovery
- Improved type hints and documentation