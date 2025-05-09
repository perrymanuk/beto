# Modern ADK API Migration Guide

This document outlines how to migrate RadBot code to leverage the newer ADK API patterns instead of using backwards-compatibility workarounds.

## Key Components to Update

### 1. Session Management in Web Interface

The web interface currently relies on direct `generate_content` calls, which is incompatible with the newer ADK architecture. We need to update `radbot/web/api/session.py` to:

```python
# Current approach (problematic)
response = root_agent.generate_content(message)

# New approach (ADK 0.4.0+)
from google.genai.types import Content, Part

# Create Content object 
user_message = Content(
    parts=[Part(text=message)],
    role="user"
)

# Collect events from runner
events = list(self.runner.run(
    user_id=self.user_id, 
    session_id=session.id,
    new_message=user_message
))

# Process events to extract the final response text
for event in events:
    if hasattr(event, 'content') and event.content:
        # Extract text from content parts
```

### 2. Agent Creation Pattern

Update agent creation to use the newer pattern:

```python
# Current pattern
root_agent = Agent(
    model=model_name,
    name="beto",
    instruction=instruction,
    sub_agents=[search_agent, code_execution_agent, scout_agent],
    # Other params...
)

# Modern pattern
from google.adk.agents import LlmAgent
from google.adk.tools import ToolCollection

# Create the agent
root_agent = LlmAgent(
    name="beto",
    llm=create_llm(model_name),  # Create LLM from model name
    system_instruction=instruction,
    tools=ToolCollection([
        # Tool definitions...
    ])
)

# Add sub-agents (if needed, though ADK 0.4.0+ favors a different approach)
for sub_agent in [search_agent, code_execution_agent, scout_agent]:
    root_agent.register_sub_agent(sub_agent)
```

### 3. Tool Implementation

Change tool implementations to use the modern pattern:

```python
# Current pattern
def tool_function(param1, param2, context):
    # Implementation...
    return result

# Modern pattern (with schema)
from google.adk.tools import Schema, ToolCollection
from google.adk.tools.schema import StringType, IntegerType

def tool_function(params, context):
    param1 = params.get("param1", "")
    param2 = params.get("param2", 0)
    # Implementation...
    return result

tool = create_function_tool(
    name="tool_name",
    description="Tool description",
    function=tool_function,
    parameters=Schema([
        StringType(name="param1", description="Parameter 1"),
        IntegerType(name="param2", description="Parameter 2")
    ])
)
```

### 4. Circular Agent Reference Handling

```python
def register_axel(root_agent):
    # Create Axel agent
    axel_agent = LlmAgent(
        name="axel_agent",
        # other params...
    )
    
    # Register with root
    root_agent.register_sub_agent(axel_agent)
    
    # Find scout in root's sub_agents
    scout_agent = find_agent_by_name(root_agent.sub_agents, "scout")
    
    if scout_agent:
        # Register bi-directional references
        scout_agent.register_reference_to(axel_agent)
        axel_agent.register_reference_to(scout_agent)
```

## Implementation Strategy

1. **Incremental Migration**:
   - Update one component at a time
   - Start with the web interface session handling
   - Then update tool implementations
   - Finally update agent creation pattern

2. **Testing Strategy**:
   - Create parallel implementations for testing
   - Use feature flags to toggle between old and new code paths
   - Validate each component before moving to the next

3. **Compatibility Layer**:
   - Create helper functions to bridge old and new patterns
   - Use decorator patterns to adapt existing tools
   
## Next Steps

1. Update the session handling in web API to use the ADK's event-based model
2. Create adapters for existing tools to work with the new parameter patterns
3. Update agent creation to use the new LlmAgent class
4. Fix circular references using a registry pattern instead of direct references

## Benefits of Migration

- Better alignment with ADK's recommended patterns
- Improved stability and reduced complexity
- Support for newer ADK features
- More maintainable codebase