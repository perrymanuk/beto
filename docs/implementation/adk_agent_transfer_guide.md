# ADK 0.4.0 Agent Transfer Guide

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->

This document provides a comprehensive guide to agent transfers in ADK 0.4.0, including the challenges we encountered and the solutions we implemented.

## Overview

Agent transfers enable conversations to be handed off between different specialized agents. In RadBot, we primarily use transfers between:
- The main agent ("beto") - handles general user interactions
- The research agent ("scout") - specializes in technical research and complex queries

## ADK 0.4.0 Agent Transfer Architecture

In ADK 0.4.0, agent transfers rely on these key components:

1. **Agent Tree Structure**: 
   - Agents are organized in a hierarchical tree
   - Each agent has a unique `name` attribute 
   - Parent-child relationships are established via:
     - `parent_agent` property (child → parent reference)
     - `sub_agents` list (parent → child references)

2. **Agent Lookup Mechanism**:
   - Agents are found in the tree by name using `find_agent(name)` 
   - Traversal starts from the root agent
   - The tree is recursively searched to find the named agent

3. **Transfer Method**:
   - The `transfer_to_agent` function is used to initiate a transfer
   - It accepts the exact name of the target agent
   - Example: `transfer_to_agent(agent_name="beto")`

4. **Runner and Session Management**:
   - The `Runner` uses an `app_name` parameter matching the root agent's name
   - The `_find_agent_to_run` method locates agents based on previous events
   - The `BaseLlmFlow._get_agent_to_run` method handles finding agents during transfers

## Common Challenges and Issues

We encountered several issues with agent transfers in ADK 0.4.0:

1. **Agent Name Mismatches**:
   - Agent transfers fail if names don't match exactly 
   - Error: `ValueError: Agent beto not found in the agent tree`
   - Root cause: The LLM's function call contained the correct agent name, but the tree traversal couldn't find the agent

2. **Incomplete Tree Structure**:
   - ADK requires bidirectional parent-child relationships
   - In ADK 0.4.0, the `parent_agent` attribute is set automatically when adding to `sub_agents`
   - Manual attempts to set these attributes can cause errors due to pydantic model constraints

3. **App Name Consistency**:
   - ADK 0.4.0 requires `app_name` in the Runner to match agent names in transfers
   - Inconsistent naming causes transfer failures or message delivery to wrong agents

4. **Search Path Issues**:
   - Agent tree traversal uses a specific order that can be confusing
   - The agent lookup starts from root and searches depth-first

## Solution: Monkey Patching Critical Methods

Our solution involved monkey patching three critical methods in the ADK to ensure agent transfers work reliably:

### 1. BaseAgent.find_agent

This method is responsible for locating agents in the tree by name:

```python
def patched_find_agent(self, name: str) -> Optional[BaseAgent]:
    """Patched find_agent method that always works for our agents"""
    logger.info(f"PATCHED FIND_AGENT CALLED FOR: '{name}'")
    
    # Direct lookup for our known agents
    if name == "beto":
        return root_agent
    elif name == "scout":
        # Find the scout in sub_agents
        for sa in root_agent.sub_agents:
            if hasattr(sa, 'name') and sa.name == 'scout':
                return sa
    
    # Fall back to original method for other names
    if self.name == name:
        return self
    return self.find_sub_agent(name)
```

### 2. Runner._find_agent_to_run

This method determines which agent should handle user messages:

```python
def patched_find_agent_to_run(self, session, root_agent: BaseAgent) -> BaseAgent:
    """Patched method to ensure we always find the right agent to run"""
    # Try original logic first
    try:
        result = original_find_agent_to_run(self, session, root_agent)
        return result
    except Exception as e:
        logger.warning(f"Original _find_agent_to_run failed: {e}, using fallback")
    
    # Fallback based on recent message authors
    for event in filter(lambda e: e.author != 'user', reversed(session.events)):
        if event.author == 'beto':
            return root_agent
        elif event.author == 'scout':
            # Find scout in sub_agents
            for sa in root_agent.sub_agents:
                if hasattr(sa, 'name') and sa.name == 'scout':
                    return sa
    
    # Default to root agent
    return root_agent
```

### 3. BaseLlmFlow._get_agent_to_run

This is the most critical method, responsible for finding agents during transfers:

```python
def patched_llm_get_agent_to_run(self, agent_name: str, invocation_context: Any) -> BaseAgent:
    """Patched method to prevent the 'Agent not found' error"""
    # Direct lookup for our agents
    if agent_name == "beto":
        return root_agent
    elif agent_name == "scout":
        # Find scout in root_agent's sub_agents
        for sa in root_agent.sub_agents:
            if hasattr(sa, 'name') and sa.name == 'scout':
                return sa
    
    # Try original method with error handling
    try:
        result = original_llm_get_agent_to_run(self, agent_name, invocation_context)
        return result
    except Exception as e:
        # Fallback to root agent's tree search
        agent = invocation_context.agent
        root = agent.root_agent if hasattr(agent, 'root_agent') else agent
        
        # Try explicit lookup
        found_agent = root.find_agent(agent_name)
        if found_agent:
            return found_agent
        
        # Last resort
        return root_agent
```

## Proper Agent Tree Setup

To ensure transfers work correctly, the agent tree must be properly structured:

```python
# Ensure agent names are correct
agent.name = "beto"  # Root agent name
research_agent.name = "scout"  # Sub-agent name

# Clear existing sub-agents
agent.sub_agents = []

# Add scout as a sub-agent of beto
# This automatically sets up parent_agent internally
agent.sub_agents.append(research_agent)
```

## Implementation in RadBot

Our implementation applies these fixes at runtime when the web server starts:

1. We monkey patch the critical ADK methods
2. We ensure proper agent names and tree structure
3. We configure the Runner with consistent app_name="beto"
4. We include detailed logging for troubleshooting

## Testing Agent Transfers

To verify agent transfers are working:

1. Start a conversation with the main beto agent
2. Ask a research question to trigger a transfer to scout
3. Check logs for "PATCHED" method calls, which indicate our fixes are being used
4. Verify the scout agent's responses come through correctly
5. Ask scout to return to the main agent
6. Verify the transfer back to beto works without errors

## Troubleshooting

If transfer issues occur:

1. **Check agent names**:
   - Verify `root_agent.name == "beto"`
   - Verify research agent has `name == "scout"`

2. **Verify agent tree structure**:
   - Make sure scout is in `root_agent.sub_agents`
   - Avoid manually setting `parent` or `parent_agent` attributes

3. **Examine logs**:
   - Look for "PATCHED" method calls in logs
   - Check which agent is handling messages
   - Verify agent names in events match expected values

4. **Runner configuration**:
   - Ensure `app_name="beto"` for the Runner
   - Use consistent app_name for session operations

## Conclusion

Agent transfers in ADK 0.4.0 rely on a precise hierarchy of agents with correct naming and bidirectional relationships. Our solution using monkey patching ensures reliable transfers even when the standard ADK mechanisms have difficulties finding agents in the tree.

While this approach is more invasive than ideal, it provides robust handling of agent transfers with minimal risk of failures. As ADK evolves, we should revisit these fixes to determine if they're still necessary in future versions.