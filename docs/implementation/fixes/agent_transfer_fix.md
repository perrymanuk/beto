# Agent Transfer Fix Implementation

This document details the implementation and fixes for agent transfer functionality in radbot, which allows transferring control between the main agent and specialized sub-agents.

## Overview

Agent transfer enables a dynamic conversation handoff between different specialized agents. The main use case is transferring from the main agent ("beto") to a research agent ("scout") when answering complex research questions, and then transferring back once the research is complete.

## Issue Description

The agent transfer system initially experienced several issues with transfers failing between the main agent and scout agent. The most common error was:

```
ValueError: Agent main not found in the agent tree
```

This resulted in incomplete conversations and users ending up at an agent with missing prompts.

## Root Cause Analysis

The transfer issues stemmed from three key problems:

### 1. Agent Name Mismatch

- The scout agent was trying to transfer back using `transfer_to_agent(agent_name='main')`
- The actual registered name of the main agent was `'beto'`
- The ADK transfer system uses exact name matching, causing the error

### 2. App Name vs Agent Name Confusion

The ADK agent transfer mechanism differentiates between:
- **Agent name** (e.g., `'beto'`) - Used to identify the agent in the agent tree
- **app_name parameter** (e.g., `'radbot'`) - Used by the Runner for session management

For transfers to work correctly, the `app_name` parameter must match the agent name that other agents use to refer to it.

### 3. Agent Tree Registration Issues

- Simply appending a sub-agent to the parent's sub_agents list wasn't sufficient
- The parent-child relationship must be bidirectional for transfers to work reliably
- The ADK 0.4.0 engine has stricter requirements for agent tree registration

## Fix Implementation

The fix involved a comprehensive approach to ensure consistency across the agent framework:

### 1. Name Consistency

- Updated the scout agent's instructions to use the correct name when transferring:
  ```python
  # Changed from
  transfer_to_agent(agent_name='main')
  # To
  transfer_to_agent(agent_name='beto')
  ```
- Renamed the agent for consistency:
  - Changed from `name="research_agent"` to `name="scout"` in agent.py
  - Updated all references throughout the codebase

### 2. App Name Consistency

- Changed the Runner's app_name from "radbot" to "beto" to match the agent name:
  ```python
  # Changed from
  runner = Runner(agent=root_agent, app_name="radbot", session_service=session_service)
  # To
  runner = Runner(agent=root_agent, app_name="beto", session_service=session_service)
  ```
- Updated all session service calls to use "beto" as the app_name:
  ```python
  session = self.session_service.get_session(app_name="beto", user_id=user_id, session_id=session_id)
  ```

### 3. Bidirectional Relationships

- Implemented bidirectional parent-child relationship for agents:
  ```python
  # Clear existing list to force re-registration
  agent.sub_agents = []
  
  # Add the sub-agent
  agent.sub_agents.append(research_agent)
  
  # Establish bidirectional relationship
  if hasattr(research_agent, 'parent'):
      research_agent.parent = agent
  ```

### 4. Runtime Verification

- Added runtime verification of agent names:
  ```python
  # CRITICAL: Ensure root_agent name is explicitly set
  if hasattr(root_agent, 'name'):
      if root_agent.name != 'beto':
          logger.warning(f"ROOT AGENT NAME MISMATCH: '{root_agent.name}' != 'beto', fixing...")
          root_agent.name = 'beto'
  ```

### 5. Additional Fixes for ADK 0.4.0

ADK 0.4.0 has stricter requirements for agent transfers. We added comprehensive verification:

```python
def _verify_agent_structure(self):
    """Verify and fix agent tree structure issues for ADK 0.4.0+ compatibility."""
    logger.info("STARTING COMPREHENSIVE AGENT TREE VERIFICATION")
    
    # CRITICAL: Re-verify root agent name - MUST be 'beto'
    if hasattr(root_agent, 'name') and root_agent.name != 'beto':
        logger.warning(f"ROOT AGENT NAME MISMATCH: '{root_agent.name}' should be 'beto' - fixing")
        root_agent.name = 'beto'
    
    # Verify sub-agent registration and maintain bidirectional relationships
    if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
        for i, sa in enumerate(root_agent.sub_agents):
            # 1. Verify sub-agent name - MUST be 'scout'
            if hasattr(sa, 'name') and sa.name != 'scout':
                logger.warning(f"SUB-AGENT NAME MISMATCH: '{sa.name}' should be 'scout' - fixing")
                sa.name = 'scout'
                
            # 2. Verify bidirectional relationship
            if hasattr(sa, 'parent'):
                if sa.parent is not root_agent:
                    logger.warning(f"SUB-AGENT PARENT MISMATCH: sub-agent[{i}].parent is wrong - fixing")
                    sa.parent = root_agent
```

This verification is called at critical points in the session lifecycle to ensure consistency.

## Additional Issues and Fixes

### Malformed Function Call Issue (May 2025)

A later issue was discovered where agent transfers were failing with a "Malformed function call: transfer_to_agent" error. This was fixed by changing how the tool is registered:

```python
# Instead of using FunctionTool wrapper
basic_tools.append(transfer_to_agent)  # Add function directly

# Also add the TRANSFER_TO_AGENT_TOOL constant for redundancy
from google.adk.tools.transfer_to_agent_tool import TRANSFER_TO_AGENT_TOOL
if TRANSFER_TO_AGENT_TOOL:
    basic_tools.append(TRANSFER_TO_AGENT_TOOL)
```

### Research Agent Parameter Fix (July 2025)

An issue was discovered where the app_name parameter wasn't being properly passed through the research agent factory:

```python
# In agent.py - the call had an app_name parameter
research_agent = create_research_agent(
    name="scout",
    model=model_name,
    tools=research_tools,
    as_subagent=False, 
    app_name="beto"  # This parameter was causing the issue
)

# But the function in factory.py didn't accept app_name
def create_research_agent(
    name: str = "technical_research_agent",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True
) -> Union[ResearchAgent, Any]:
    # No app_name parameter here
```

We fixed this by adding the `app_name` parameter throughout the research agent creation chain.

## Testing and Validation

To validate agent transfers:

1. Start a conversation with the main agent
2. Ask a research question to trigger a transfer to the scout agent
3. After the scout agent completes its task, ask it to return to the main agent
4. Verify the transfer back works without errors

## Debugging Tools

For troubleshooting agent transfer issues, several logging techniques are useful:

```python
# Check agent tree structure
if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
    sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
    logger.info(f"Agent tree structure - Root: '{root_agent.name}', Sub-agents: {sub_agent_names}")

# Verify app_name matches agent names
logger.info(f"ROOT AGENT NAME: '{root_agent.name}'")
logger.info(f"RUNNER APP_NAME: '{runner.app_name}'")

# Check transfer tool availability
has_transfer_tool = False
for tool in agent.tools:
    tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
    if tool_name == 'transfer_to_agent':
        has_transfer_tool = True
        break
logger.info(f"Agent has transfer_to_agent tool: {has_transfer_tool}")

# Verify bidirectional relationship
if hasattr(sub_agent, 'parent') and hasattr(sub_agent.parent, 'name'):
    logger.info(f"Sub-agent's parent name: '{sub_agent.parent.name}'")
```

## ADK 0.4.0 Requirements

For transfers to work in ADK 0.4.0, the system must satisfy:

1. The agent tree is searched starting from the root agent
2. Agents must have unique names across the entire tree
3. Bidirectional parent-child relationships must be established
4. The `app_name` parameter must match the agent name used in transfers
5. Both agents involved in a transfer must have the `transfer_to_agent` tool available
6. Session operations must use consistent app_name matching the agent name

## Future Improvements

To prevent similar issues in the future:

1. Create a centralized agent name registry to ensure consistent naming
2. Add explicit logging around agent transfers
3. Implement a more robust transfer mechanism
4. Add unit tests specifically for agent transfer functionality
5. Create a helper function for registering sub-agents
6. Implement automated testing of agent transfers during startup
7. Create a dedicated class for managing the agent tree structure