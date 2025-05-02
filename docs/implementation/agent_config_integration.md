# RaderBot Agent and ConfigManager Integration

This document outlines the integration between the `RaderBotAgent` class and the `ConfigManager` in the RaderBot framework.

## Overview

The integration allows the agent system to load configuration from centralized settings managed by the `ConfigManager`. This provides several benefits:

1. Centralized configuration management
2. Easy switching between models (main vs. sub-agent models)
3. Loading instructions from external files
4. Environment-based configuration 
5. Consistent settings across the application

## Implementation Details

### Agent Configuration

The `RaderBotAgent` class now accepts a `ConfigManager` instance as an optional parameter. If not provided, it falls back to the global instance. The agent uses the ConfigManager for:

- Loading the appropriate model name (`get_main_model()`)
- Loading instruction prompts (`get_instruction(instruction_name)`)
- Checking environment settings (`is_using_vertex_ai()`)

### Factory Methods

The `AgentFactory` class has been updated to support the `ConfigManager` for both root agents and sub-agents:

- `create_root_agent()` uses the config for model selection and instruction loading
- `create_sub_agent()` uses a different model intended for simpler agents (`get_sub_agent_model()`)

### Instruction Loading

Instructions are loaded from the configuration directory by name:

```python
instruction = config.get_instruction(instruction_name)
```

This allows storing agent instructions in external files for better organization and easier updates. If the instruction file is not found, a default fallback instruction is used.

### Dynamic Configuration

The agent now supports updating its configuration at runtime:

- `update_instruction(instruction_name)` - Changes the agent's instruction using a named file
- `update_model(new_model)` - Changes the model being used by the agent
- `get_configuration()` - Returns a dict with the current configuration, including config details

## Usage Examples

### Creating an Agent with Custom Config

```python
from raderbot.config.settings import ConfigManager
from raderbot.agent.agent import create_agent

# Create a custom config manager
custom_config = ConfigManager(config_dir=Path("/path/to/custom/configs"))

# Create agent with the custom config
agent = create_agent(
    config=custom_config,
    instruction_name="specialized_agent"
)
```

### Creating a Sub-Agent with Different Model

```python
from raderbot.agent.agent import AgentFactory

# Create a sub-agent that uses the sub-agent model from config
memory_agent = AgentFactory.create_sub_agent(
    name="memory_agent",
    description="Agent responsible for memory retrieval",
    instruction_name="memory_agent_instructions"
)
```

### Updating Agent Configuration

```python
# Update agent to use a different instruction
agent.update_instruction("customer_support_agent")

# Switch to a different model
agent.update_model("gemini-2.0-flash")
```

## Testing

The integration is tested in `test_agent_config_integration.py` which validates:

1. Agent initialization with ConfigManager
2. Loading of models and instructions
3. Fallback behavior for missing files
4. Factory methods using the configuration
5. Sub-agent configuration

## Best Practices

1. Store agent instructions in the designated instructions directory
2. Use environment variables for model selection in different environments
3. Provide meaningful instruction file names
4. Consider creating specialized ConfigManager instances for different components
5. Access model configuration through the ConfigManager rather than hardcoding values

## Future Improvements

1. Support for instruction versioning
2. Dynamic reloading of instructions without restarting the agent
3. Additional configuration parameters for agent generation
4. Configuration validation and schema checking
5. Extended environment variable support