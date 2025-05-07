# ADK Agent Tool Approach

## Overview

After analyzing the official ADK samples implementation of multi-agent systems, we've identified a more robust pattern for implementing agent transfers in RadBot. This document outlines the plan to migrate from our current `transfer_to_agent` approach to the `AgentTool` pattern used in Google's ADK samples.

## Current Issues

1. Despite implementing proper agent transfer functionality with `transfer_to_agent`, we continue to face issues with agent tree structure and reliable transfers between agents.
2. Our implementation attempts to dynamically register agents in different places, creating inconsistent agent tree structures.
3. The LLM cannot reliably transfer to specific agents despite multiple attempts to emphasize exact agent names.

## New Approach

The ADK samples demonstrate a more structured approach that avoids these issues entirely by:

1. Defining all agents at module level
2. Explicitly constructing the agent tree at initialization time
3. Using `AgentTool` for agent interactions rather than relying on LLM-driven transfers

### Step 1: Agent Declaration and Export

Define all agents at the module level in their respective files:

```python
# In radbot/tools/adk_builtin/search_tool.py
search_agent = create_search_agent(
    name="search_agent",
    model=os.getenv("SEARCH_AGENT_MODEL", config_manager.get_main_model()),
    # Other params...
)

# In radbot/tools/adk_builtin/code_execution_tool.py
code_execution_agent = create_code_execution_agent(
    name="code_execution_agent",
    model=os.getenv("CODE_EXEC_AGENT_MODEL", config_manager.get_main_model()),
    # Other params...
)

# In radbot/agent/research_agent/factory.py
scout_agent = create_research_agent(
    name="scout",
    model=os.getenv("SCOUT_AGENT_MODEL", config_manager.get_main_model()),
    # Other params...
)
```

Export these agents through `__init__.py` files for easy importing:

```python
# In radbot/agent/agents.py or similar
from radbot.tools.adk_builtin.search_tool import search_agent
from radbot.tools.adk_builtin.code_execution_tool import code_execution_agent
from radbot.agent.research_agent.factory import scout_agent

__all__ = ["search_agent", "code_execution_agent", "scout_agent"]
```

### Step 2: Root Agent Construction

Construct the root agent with an explicit sub-agents list:

```python
# In agent.py (root)
from radbot.agent.agents import search_agent, code_execution_agent, scout_agent

# Create the root agent with explicit sub-agents list
root_agent = Agent(
    name="beto",
    model=model_name,
    instruction=instruction,
    tools=[...all tools...],
    sub_agents=[search_agent, code_execution_agent, scout_agent]
)
```

### Step 3: Agent Tool Implementation

Replace LLM-driven transfers with explicit `AgentTool` function calls:

```python
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import ToolContext

async def call_code_execution(
    code: str,
    description: str = "",
    tool_context: ToolContext = None,
):
    """Execute Python code using the code execution agent."""
    from radbot.agent.agents import code_execution_agent
    
    agent_tool = AgentTool(agent=code_execution_agent)
    return await agent_tool.run_async(
        args={"code": code, "description": description},
        tool_context=tool_context
    )

async def call_search(
    query: str,
    tool_context: ToolContext = None,
):
    """Search the web using the search agent."""
    from radbot.agent.agents import search_agent
    
    agent_tool = AgentTool(agent=search_agent)
    return await agent_tool.run_async(
        args={"query": query},
        tool_context=tool_context
    )

async def call_scout(
    research_topic: str,
    tool_context: ToolContext = None,
):
    """Research a topic using the scout agent."""
    from radbot.agent.agents import scout_agent
    
    agent_tool = AgentTool(agent=scout_agent)
    return await agent_tool.run_async(
        args={"topic": research_topic},
        tool_context=tool_context
    )
```

### Step 4: Update Root Agent Instruction

Update the root agent instruction to guide the LLM to use these tool functions instead of transfers:

```python
instruction = """
You are a helpful assistant with access to specialized tools for different tasks:

1. For web searches, use the `call_search` tool with your search query
   Example: call_search(query="latest news on quantum computing")

2. For executing Python code, use the `call_code_execution` tool
   Example: call_code_execution(code="print('Hello world')", description="Simple test")

3. For in-depth research, use the `call_scout` tool
   Example: call_scout(research_topic="environmental impact of electric vehicles")

Use these tools when appropriate to handle user requests. DO NOT attempt to transfer
to other agents directly - always use the appropriate tool function instead.
"""
```

## Implementation Plan

1. **Phase 1: Core Changes (High Priority)**
   - Create the agent module exports structure
   - Implement core AgentTool functions
   - Update root agent construction with explicit sub-agents

2. **Phase 2: User Experience (Medium Priority)**
   - Update instructions and prompts
   - Add clear examples of tool usage
   - Improve error handling for agent tool calls

3. **Phase 3: Testing and Validation (High Priority)**
   - Create new test scripts for AgentTool pattern
   - Validate all agent tool functions work correctly
   - Ensure session state is properly maintained between agent calls

4. **Phase 4: Cleanup (Low Priority)**
   - Remove old transfer_to_agent code
   - Update documentation
   - Refactor any remaining code using the old pattern

## Benefits of the New Approach

1. **Reliability**: Agent interactions are explicit function calls rather than LLM-driven transfers
2. **Predictability**: Agent tree structure is defined once at initialization time
3. **Consistency**: Follows the pattern used in official ADK samples
4. **Maintainability**: Clearer separation of concerns and module structure
5. **User Experience**: No more failed transfers due to naming issues or LLM confusion

## Transition Strategy

1. Implement the new approach in parallel with the existing code
2. Add feature flags to enable/disable the new approach
3. Test thoroughly with real-world scenarios
4. Once validated, make the new approach the default
5. Eventually remove the old approach entirely

This implementation plan aligns with the patterns shown in ADK samples and should resolve our ongoing issues with agent transfers.