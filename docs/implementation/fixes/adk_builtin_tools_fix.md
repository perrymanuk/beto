# ADK Built-in Tools Fix Implementation

## Overview

This document describes the implementation of fixes for the ADK built-in tools integration. Specifically, it addresses issues with:

1. The code execution tool registration
2. Agent transfers between the main agent (beto), research agent (scout), and built-in agents (search, code execution)
3. Bidirectional transfers between agents

## Implementation Details

### 1. Agent Transfer Compatibility Layer

Created a backward compatibility layer in `radbot/tools/agent_transfer.py` that wraps the ADK's `transfer_to_agent` function in an `AgentTransferTool` class to maintain compatibility with existing code:

```python
"""
Agent transfer functionality for backward compatibility.
"""

import logging
from typing import Optional, Any

# Import the ADK transfer_to_agent function
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

# Create a wrapper class with the same interface as expected by older code
class AgentTransferTool:
    """
    Wrapper around transfer_to_agent for backward compatibility.
    """
    
    def __init__(self):
        self.name = "transfer_to_agent"
        self.description = "Transfers control to another agent"
        self._transfer_fn = transfer_to_agent
    
    def __call__(self, agent_name: str, **kwargs) -> Any:
        """Call the transfer_to_agent function with the given agent name."""
        return self._transfer_fn(agent_name=agent_name, **kwargs)

# For backward compatibility
transfer_to_agent_tool = AgentTransferTool()
```

### 2. ADK Built-in Tools Configuration Fix

Fixed the `config` attribute handling for LlmAgent in both search and code execution tools by adding proper error handling and using the `set_config` method when available:

```python
# Enable search/code execution explicitly if using Vertex AI
if cfg.is_using_vertex_ai():
    try:
        from google.genai import types
        # Check if the agent has a config attribute already
        if not hasattr(agent, "config"):
            # For LlmAgent type in ADK 0.4.0+
            if hasattr(agent, "set_config"):
                # Use set_config method if available
                config = types.GenerateContentConfig()
                config.tools = [types.Tool(...)]
                agent.set_config(config)
            else:
                # Try to add config attribute directly
                agent.config = types.GenerateContentConfig()
                agent.config.tools = [types.Tool(...)]
        else:
            # Update existing config
            if not hasattr(agent.config, "tools"):
                agent.config.tools = []
            agent.config.tools.append(types.Tool(...))
    except Exception as e:
        logger.warning(f"Failed to configure tool for Vertex AI: {str(e)}")
```

### 3. Bidirectional Agent Transfers

Enhanced the research agent factory to correctly add the parent agent (beto) to the scout's sub-agents list and vice versa:

```python
# Add parent agent (beto) to sub-agents list for proper backlinks
try:
    from google.adk.agents import Agent
    
    # Create a proxy agent for beto (parent) to allow transfers back
    beto_agent = Agent(
        name="beto",  # Must be exactly "beto" for transfers back
        model=model or config_manager.get_main_model(),
        instruction="Main coordinating agent",  # Simple placeholder
        description="Main coordinating agent that handles user requests",
        tools=[transfer_to_agent]  # Essential to have transfer_to_agent
    )
    
    # Add beto to the list of sub-agents if not already there
    if not any(sa.name == "beto" for sa in sub_agents if hasattr(sa, 'name')):
        sub_agents.append(beto_agent)
        logger.info("Added 'beto' agent to scout's sub_agents list for proper back-transfers")
```

Similarly, added similar code to the search and code execution tools to ensure bidirectional transfers work correctly.

### 4. Validation Test Script

Created a validation test script (`tools/test_adk_builtin_transfers.py`) to verify agent transfers in different configurations:

1. No built-in tools enabled
2. Only search enabled
3. Only code execution enabled  
4. Both search and code execution enabled

The test validates:
- Agent sub-agent relationships
- Availability of transfer_to_agent tool
- All agent transfers work bidirectionally

## Issues Addressed

1. **Code Execution Registration**: Fixed the code execution tool not being properly registered with the main agent.
2. **Scout to Beto Transfers**: Fixed Scout's inability to transfer back to the Beto agent.
3. **ADK 0.4.0 Compatibility**: Updated code to work with ADK 0.4.0's agent transfer mechanism.
4. **LlmAgent Configuration**: Fixed "LlmAgent object has no field 'config'" error by adding proper configuration handling.

## Testing

The fix can be tested with:

```bash
# Run validation tests
python -m tools.test_adk_builtin_transfers --validate

# Run web application for manual testing
python -m tools.test_adk_builtin_transfers --web
```

## Future Improvements

1. Add full sub-agent relationship testing (testing transfers from non-root agents)
2. Implement automated end-to-end tests for agent transfers
3. Add validation of tool functionality in transferred contexts