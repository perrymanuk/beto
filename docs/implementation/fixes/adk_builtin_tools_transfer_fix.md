# ADK Built-in Tools Transfer Fix

## Overview

This document describes fixes for the agent transfer functionality between the main agent (beto), research agent (scout), and the ADK built-in agents (search_agent and code_execution_agent). The fixes ensure proper bidirectional transfers between all agents in the system.

## Issues Addressed

1. The scout agent was unable to transfer back to the beto agent
2. Transfers to and from the code_execution_agent weren't working properly
3. Transfers to and from the search_agent weren't working properly

These issues occurred after migrating to ADK 0.4.0, which changed how agent transfers work by requiring agents to be in each other's sub_agents lists.

## Implementation Details

For a detailed implementation description, see [ADK Built-in Tools Fix](adk_builtin_tools_fix.md).

For testing information, see [ADK Built-in Tools Transfer Test](adk_builtin_tools_transfer_test.md).

### Key Changes

1. Added backward compatibility for AgentTransferTool in `radbot/tools/agent_transfer.py`
2. Fixed the scout agent factory to include beto in scout's sub-agents list
3. Enhanced built-in agent registration to ensure bidirectional transfers
4. Fixed LlmAgent configuration issues for Vertex AI
5. Modified agent tools for Vertex AI limitations (only one tool per agent)
6. Added comprehensive testing for agent transfers

## Testing the Fix

The fix can be tested with the dedicated test script:

```bash
# Run validation tests
python -m tools.test_adk_builtin_transfers --validate

# Run web application for manual testing
python -m tools.test_adk_builtin_transfers --web
```

## Lessons Learned

1. **ADK 0.4.0 Changes**: In ADK 0.4.0+, for agent A to transfer to agent B, agent B must be in agent A's sub_agents list
2. **Bidirectional Transfers**: For bidirectional transfers, agents must be in each other's sub_agents lists
3. **Agent Naming**: Agent names must be consistent for transfers to work properly
4. **Tool Availability**: All agents must have the transfer_to_agent tool available
5. **Proxy Agents**: For complex relationships, proxy agents can be used to establish proper parent-child relationships