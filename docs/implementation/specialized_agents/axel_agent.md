# Axel Agent Implementation

<!-- Version: 0.4.0 | Last Updated: 2025-05-09 -->

## Overview

This document details the implementation of the "Axel" agent, a specialized execution agent designed to complement Scout's research and design capabilities. While Scout focuses on research, exploration, and design, Axel is dedicated to precise execution and implementation of specifications.

## Purpose

Axel serves as the implementation-focused counterpart to Scout in a dual-agent workflow:

1. **Scout**: Research, exploration, design planning, and specification creation
2. **Axel**: Execution, implementation, testing, and delivery of the specifications created by Scout

This separation of concerns allows for specialization, with each agent optimized for its specific role in the software development process.

## Implementation Details

### Agent Creation

The Axel agent will be implemented following a similar pattern to the Scout agent, but with a focus on execution rather than research. It will be created using a dedicated factory function in a new module:

```python
# radbot/agent/execution_agent/factory.py

def create_execution_agent(
    name: str = "axel",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True,
    enable_code_execution: bool = True,
    app_name: str = "beto"
) -> Union[ExecutionAgent, Any]:
    """
    Create an execution agent with the specified configuration.
    
    Args:
        name: Name of the agent (should be "axel" for consistent transfers)
        model: LLM model to use (defaults to config setting)
        custom_instruction: Optional custom instruction to override the default
        tools: List of tools to provide to the agent
        as_subagent: Whether to return the ExecutionAgent or the underlying ADK agent
        enable_code_execution: Whether to enable Code Execution capability
        app_name: Application name (should match the parent agent name for ADK 0.4.0+)
        
    Returns:
        Union[ExecutionAgent, Any]: The created agent instance
    """
    # Implementation similar to create_research_agent but focused on execution
    # ...
```

### Axel's Instruction

A custom instruction file will be created for Axel at:
```
/Users/perry.manuk/git/perrymanuk/radbot/radbot/config/default_configs/instructions/axel.md
```

This instruction will define Axel's persona as a precise, methodical executor focused on implementation, testing, and delivery.

### Integration with Agent System

Axel will be integrated into the agent system similar to Scout:

1. The agent will be created at startup
2. It will be added to the list of available agents for transfer
3. Users can transfer to Axel directly or from Scout when ready for implementation

### Tooling Specialization

Axel will have access to a specialized set of tools focused on execution:

1. **Code execution tools**: Shell command execution, code running, etc.
2. **File system tools**: For reading/writing code files
3. **Testing tools**: For validating implementations
4. **Deployment tools**: For packaging and deployment tasks
5. **Documentation tools**: For creating implementation documentation

### Agent-to-Agent Transfer Workflow

The typical workflow between Scout and Axel will be:

1. **User → Scout**: Initial research and design specification
2. **Scout → Axel**: Transfer of design specifications for implementation
3. **Axel → Scout**: Transfer back for design refinements if needed
4. **Axel → User**: Delivery of implemented solutions

## Code Structure

### Directory Structure

```
radbot/agent/execution_agent/
  ├── __init__.py
  ├── agent.py       # ExecutionAgent class
  ├── factory.py     # create_execution_agent function
  ├── instructions.py # Default instructions if not using axel.md
  └── tools.py       # Specialized execution tools
```

### ExecutionAgent Class

```python
# radbot/agent/execution_agent/agent.py

class ExecutionAgent:
    """Agent specialized in executing and implementing specifications."""

    def __init__(
        self,
        name: str = "axel",
        model: Optional[str] = None,
        instruction: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[List[FunctionTool]] = None,
        enable_code_execution: bool = True,
        app_name: str = "beto"
    ):
        """Initialize the execution agent."""
        # Implementation similar to ResearchAgent but focused on execution
        # ...
```

## Configuration Integration

Axel will be integrated into the configuration system:

1. **Model Configuration**: Add support for `axel_agent` model selection:
   ```python
   # In ConfigManager
   def get_agent_model(self, agent_type: str) -> str:
       """Get the model for a specific agent type."""
       if agent_type == "axel_agent" and self.model_config.get("axel_agent_model"):
           return self.model_config["axel_agent_model"]
       # Fall back to sub_agent_model or main_model
       # ...
   ```

2. **Configuration Schema**: Update schema to include Axel-specific settings:
   ```json
   "model_config": {
     "type": "object",
     "properties": {
       "axel_agent_model": {
         "type": "string",
         "description": "Model to use for the Axel execution agent"
       },
       // Existing properties...
     }
   }
   ```

## Integration with Agent Factory

Update the main `AgentFactory` to support creating the Axel agent:

```python
# In agent_factory.py

@staticmethod
def create_axel_agent(
    name: str = "axel",
    model: Optional[str] = None,
    tools: Optional[List] = None,
    instruction_name: str = "axel",
    config: Optional[ConfigManager] = None
) -> Agent:
    """Create the Axel execution agent."""
    # Implementation similar to create_research_agent
    # ...
```

## Benefits

The Axel agent provides several benefits to the overall agent architecture:

1. **Specialized Execution**: Allows for a dedicated agent optimized for implementation tasks
2. **Clear Separation of Concerns**: Research/design (Scout) vs. Execution/implementation (Axel)
3. **Improved Context Management**: Each agent maintains context relevant to its specific role
4. **Enhanced Workflow**: Natural handoff points between design and implementation phases
5. **Role-Specific Instructions**: Each agent has instructions tailored to its specific function

## Next Steps

1. Create the execution_agent directory and module structure
2. Implement the ExecutionAgent class and factory function
3. Create the axel.md instruction file
4. Update the agent system to integrate Axel
5. Test the Scout → Axel workflow
6. Document usage examples

## Conclusion

The addition of the Axel agent complements the existing Scout agent, creating a powerful dual-agent workflow that separates research and design from execution and implementation. This approach allows for better specialization, improved context management, and a more natural software development workflow.