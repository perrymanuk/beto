# Scout Agent Instruction Implementation

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document details the implementation of using the custom `scout.md` prompt for the "scout" subagent in RadBot.

## Overview

The "scout" subagent is a specialized agent for technical research and design collaboration. It was previously using the default research agent instruction from the `get_full_research_agent_instruction()` function. This implementation changes the agent to use the custom `scout.md` prompt file instead.

## Implementation Details

### The Scout.md Prompt File

The `scout.md` file is located in the RadBot configuration directory at:
```
/Users/perry.manuk/git/perrymanuk/radbot/radbot/config/default_configs/instructions/scout.md
```

This file defines the agent's persona as "Scout," designed to aid with technical research and serve as a rubber-ducky for technical software engineering design and execution projects.

### Integration with Agent.py

The main `agent.py` file creates a research agent and adds it as a subagent named "scout". The implementation has been updated to use the `scout.md` custom prompt instead of the default research agent instructions.

The change involves:

1. Using the ConfigManager to load the "scout" instruction
2. Passing the loaded instruction to the `create_research_agent` function as `custom_instruction`

The updated code in `agent.py`:

```python
# Create the research agent with the scout.md instruction
research_agent = create_research_agent(
    name="scout", 
    model=model_name,
    tools=research_tools,
    as_subagent=False,  # Get the ADK agent directly
    custom_instruction=config_manager.get_instruction("scout")  # Use the scout.md instruction
)
```

### Research Agent Factory

The `create_research_agent` function in `radbot/agent/research_agent/factory.py` accepts a `custom_instruction` parameter, which is then passed to the ResearchAgent constructor as `instruction`:

```python
def create_research_agent(
    name: str = "technical_research_agent",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True
) -> Union[ResearchAgent, Any]:
    # ...
    research_agent = ResearchAgent(
        name=name,
        model=model,
        instruction=custom_instruction,  # Will use default if None
        tools=tools
    )
    # ...
```

### ResearchAgent Implementation

The `ResearchAgent` class in `radbot/agent/research_agent/agent.py` correctly handles the custom instruction in its constructor:

```python
def __init__(
    self,
    name: str = "technical_research_agent",
    model: Optional[str] = None,
    instruction: Optional[str] = None,
    description: Optional[str] = None,
    tools: Optional[List[FunctionTool]] = None,
    output_key: Optional[str] = "research_summary"
):
    # ...
    # Use default instruction if not specified
    if instruction is None:
        instruction = get_full_research_agent_instruction()
        logger.info("Using default research agent instruction")
    # ...
    # Create the LlmAgent instance
    self.agent = LlmAgent(
        name=name,
        model=model,
        instruction=instruction,
        # ...
    )
```

## Benefits

This implementation provides several benefits:

1. **Personalized Agent Experience**: The scout.md prompt creates a more distinct personality for the "scout" subagent.

2. **Easier Customization**: The instruction can be changed by editing the scout.md file without modifying code.

3. **Consistent Configuration**: Uses the same ConfigManager system as other agent prompts.

4. **Better Specialization**: The scout.md prompt is specifically tailored for the technical research and rubber-ducking tasks.

## Conclusion

With this implementation, the "scout" subagent now uses the custom scout.md prompt file for its instructions, creating a more specialized and distinct personality for technical research and design collaboration tasks.
