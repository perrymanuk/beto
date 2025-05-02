# Agent Configuration Integration

This document details the integration between the RaderBot agent implementation and the configuration system, focusing on dynamic instruction loading, model selection, and flexible agent creation.

## Overview

The integration of the ConfigManager with the RaderBotAgent enables:

1. Loading agent instructions dynamically from files
2. Selecting appropriate models based on agent type and environment settings
3. Creating hierarchical agent structures with consistent configuration
4. Supporting structured input/output using schemas
5. Flexible overrides of default configurations

## Implementation Changes

### RaderBotAgent Class

The RaderBotAgent class was updated to work with the ConfigManager:

```python
class RaderBotAgent:
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        tools: Optional[List[Any]] = None,
        model: Optional[str] = None,
        name: str = "main_coordinator",
        instruction: Optional[str] = None,
        instruction_name: Optional[str] = "main_agent",
        config: Optional[ConfigManager] = None
    ):
        # Use provided config or default
        self.config = config or config_manager
        
        # Use provided session service or create an in-memory one
        self.session_service = session_service or InMemorySessionService()
        
        # Determine the model to use
        self.model = model or self.config.get_main_model()
        
        # Determine instruction to use (with fallback logic)
        # ...
```

The constructor now:
- Accepts a `config` parameter for dependency injection of a ConfigManager
- Falls back to the global instance if none is provided
- Supports loading instructions by name from the config
- Provides fallback behavior if the specified instruction is not found
- Tracks instruction names for configuration introspection

### AgentFactory Updates

The AgentFactory was enhanced to leverage the configuration system:

```python
class AgentFactory:
    @staticmethod
    def create_root_agent(
        name: str = "main_coordinator",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        instruction_name: str = "main_agent",
        config: Optional[ConfigManager] = None
    ) -> Agent:
        # Use provided config or default
        cfg = config or config_manager
        
        # Get the model name
        model_name = model or cfg.get_main_model()
        
        # Get the instruction
        try:
            instruction = cfg.get_instruction(instruction_name)
        except FileNotFoundError:
            # Fall back to default instruction
            instruction = FALLBACK_INSTRUCTION
        
        # Create the root agent
        # ...
```

A new `create_sub_agent` method was added to specifically handle sub-agents:

```python
@staticmethod
def create_sub_agent(
    name: str,
    description: str,
    instruction_name: str,
    tools: Optional[List] = None,
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None
) -> Agent:
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (use sub-agent model by default)
    model_name = model or cfg.get_sub_agent_model()
    
    # Get the instruction with fallback for sub-agents
    # ...
```

This specialization ensures that:
- Root agents use the main model by default
- Sub-agents use the faster/lighter sub-agent model by default
- Both leverage instruction files from the config system
- Both have reasonable fallbacks when configurations aren't found

### Helper Functions

The factory functions were updated to support the configuration system:

```python
def create_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    model: Optional[str] = None,
    instruction_name: str = "main_agent",
    name: str = "main_coordinator",
    config: Optional[ConfigManager] = None
) -> RaderBotAgent:
    # Create the agent with all the specified parameters
    return RaderBotAgent(
        session_service=session_service,
        tools=tools,
        model=model,
        name=name,
        instruction_name=instruction_name,
        config=config
    )
```

## Configuration Pattern

The integration follows a layered configuration pattern:

1. **Hard-coded Defaults**: Fallback values within the code
2. **File-based Configuration**: Instructions and schemas loaded from files
3. **Environment Variables**: Override via environment variables
4. **Parameter Overrides**: Direct parameter values in function calls

This approach provides sensible defaults while allowing for flexibility and customization at various levels.

## Configuration Lookup Sequence

When creating an agent, the system follows this configuration lookup sequence:

1. If an explicit value is provided (e.g., `model="gemini-2.5-pro"`), use it
2. If a specific config manager is provided, use its values
3. Otherwise, use the global config manager's values
4. If loading from config fails, use hard-coded fallbacks

## Configuration Loading Error Handling

The integration implements robust error handling for configuration loading:

1. **Missing Instructions**: Falls back to default instructions with logging
2. **Sub-agent Instructions**: Generates minimal instructions when not found
3. **Configuration Method Errors**: Raises appropriate errors with clear messages
4. **Model Selection**: Always has reasonable defaults even if environment variables are missing

## Usage Examples

### Creating a Main Agent

```python
from raderbot.agent.agent import create_agent
from raderbot.tools.basic_tools import get_current_time, get_weather

# Create main agent with default configuration
agent = create_agent(
    tools=[get_current_time, get_weather],
    instruction_name="main_agent"  # Will load from config/default_configs/instructions/
)

# Process messages
response = agent.process_message(user_id="user123", message="What's the weather in London?")
```

### Creating a Sub-Agent

```python
from raderbot.agent.agent import AgentFactory
from raderbot.tools.memory_tools import search_past_conversations

# Create memory sub-agent
memory_agent = AgentFactory.create_sub_agent(
    name="memory_agent",
    description="Specialized agent for memory operations",
    instruction_name="memory_agent",  # Will load from config/default_configs/instructions/
    tools=[search_past_conversations]
)

# Add to main agent
main_agent = create_agent()
main_agent.add_sub_agent(memory_agent)
```

### Custom Configuration

```python
from pathlib import Path
from raderbot.agent.agent import create_agent
from raderbot.config.settings import ConfigManager

# Create custom configuration
custom_config = ConfigManager(config_dir=Path("/path/to/custom/configs"))

# Use custom config
agent = create_agent(
    config=custom_config,
    instruction_name="custom_instruction"
)
```

## Benefits of the Integration

The integration of the agent system with ConfigManager provides several benefits:

1. **Separation of Concerns**: Code logic is separated from configuration details
2. **Versioned Instructions**: Instruction prompts can be version controlled as files
3. **Environment-Specific Settings**: Different environments can use different configurations
4. **Testability**: Easy to inject mock configurations for testing
5. **Consistency**: Sub-agents and main agents share configuration structure
6. **Flexibility**: Multiple configuration methods that work together

## Next Steps

Following the ConfigManager integration, the next implementation steps are:

1. Complete the memory system with Qdrant
2. Create memory-specific tools that integrate with the configured agents
3. Set up MCP integration for Home Assistant
4. Implement advanced context management