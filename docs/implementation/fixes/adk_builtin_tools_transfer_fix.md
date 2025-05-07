# ADK Built-in Tools Transfer Fix

## Issue

After adding the Google search and code execution tools from ADK, transfers to these built-in agents were not working. The logs showed that the agent subagent list had entries for these agents, but they were not being found in the agent tree during transfer attempts.

## Root Causes

1. **Agent Resolution Bug**: The `patched_llm_get_agent_to_run` function in `session.py` was not looking for built-in agents like `search_agent` and `code_execution_agent` by name.

2. **Parameter Order Mismatch**: The `patched_llm_get_agent_to_run` function had incorrect parameter ordering:
   - Our implementation: `(self, agent_name, invocation_context)`
   - ADK's implementation: `(self, invocation_context, agent_name)`

3. **Missing Transfer Tools**: The built-in agents were added to the sub-agent tree but were not given the `transfer_to_agent` tool, which is required for transfers to work.

4. **Agent Tree Rebuilding**: During the `_verify_agent_structure` method, only the scout agent was being preserved and re-added to the tree, causing built-in agents to be lost.

## Implemented Fixes

1. **Fixed Parameter Order**: Corrected the order of parameters in the `patched_llm_get_agent_to_run` method to match ADK's expected order.

2. **Added Built-in Agent Recognition**: Updated the agent lookup code to explicitly handle `search_agent` and `code_execution_agent` names.

3. **Enhanced Agent Tree Verification**: Modified the `_verify_agent_structure` method to preserve and properly reattach all sub-agents, including built-in tool agents.

4. **Added Transfer Tools**: Added the `transfer_to_agent` tool to all agents, including the built-in tool agents, to enable bidirectional transfers.

5. **Improved Debugging**: Added more detailed logging for the agent tree structure, explicitly showing information about built-in tool agents.

## Implementation Details

The changes were made in the following areas:

1. `radbot/web/api/session.py`:
   - Updated parameter order in `patched_llm_get_agent_to_run`
   - Added explicit handling for `search_agent` and `code_execution_agent` in the agent lookup
   - Modified `_verify_agent_structure` to detect and properly restore all types of sub-agents
   - Enhanced the logging to show more details about the agent tree

2. Agent Tool Management:
   - Added code to ensure the `transfer_to_agent` tool is available to all agents
   - Added fallback to recreate tool lists for built-in agents if they're missing

## Testing

To verify the fix works:
1. Enable built-in tools with `RADBOT_ENABLE_ADK_SEARCH=true` and `RADBOT_ENABLE_ADK_CODE_EXEC=true`
2. Check the logs when the application starts to confirm all agents are properly registered
3. Test transfers to both the search agent and code execution agent
4. Verify that transfers back to the main agent also work correctly

## Future Considerations

- Add more explicit checks for built-in agents to avoid similar issues in the future
- Consider enhancing the agent structure validation to detect and fix missing tools automatically
- Add comprehensive logging about the agent tree structure at application startup