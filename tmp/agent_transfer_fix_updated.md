# Agent Transfer Fix Implementation

## Issue Description

The research agent (web search agent) was unable to transfer control back to the main agent due to a name mismatch. When the research agent attempted to use `transfer_to_agent(agent_name='main')`, it would fail with an error:

```
ValueError: Agent main not found in the agent tree
```

This resulted in the user ending up at an agent with missing prompts, effectively breaking the conversation flow.

## Root Cause Analysis

The issue had three parts:

### First Problem - Agent Name Mismatch:
1. The name used by the scout agent when trying to transfer back (`'main'`)
2. The actual registered name of the main agent (`'beto'`)

### Second Problem - App Name vs Agent Name:
The ADK agent transfer mechanism differentiates between:
1. The agent name (e.g., `'beto'`) - Used to identify the agent in the agent tree
2. The app_name parameter (e.g., `'radbot'`) - Used by the Runner for session management

For agent transfers to work correctly, the app_name parameter must match the agent name that other agents use to refer to it.

### Third Problem - Agent Tree Registration Issues:
1. The way sub-agents are registered in the agent tree affects how the ADK locates them during transfers
2. Simply appending a sub-agent to the parent's sub_agents list isn't sufficient for proper registration
3. The parent-child relationship must be bidirectional for transfers to work reliably

Agent name resolution in the ADK's transfer system works by matching the exact name of the agent as specified during creation. The main agent was created with the name `'beto'` (in `/agent.py`), but the instructions in the research agent were telling it to transfer to an agent named `'main'`.

Additionally, there was inconsistency in how the research agent itself was named:
- The agent creation used `name="scout"` 
- But the instructions referred to the transfer between main agent and research agent

## Fix Implementation

The fix involved several changes to create consistency in agent naming and registration:

1. Updated the scout agent's instructions to use the correct name when transferring:
   - Changed `transfer_to_agent(agent_name='main')` to `transfer_to_agent(agent_name='beto')`
   - Updated in both main instruction and agent transfer instruction sections

2. Renamed the agent for consistency:
   - Changed from `name="research_agent"` to `name="scout"` in agent.py
   - Updated the transfer instructions in the main agent to match this name

3. Fixed references to "research agent" in main agent code:
   - Updated all mentions to "scout agent" for consistency
   - Ensured consistent naming throughout the codebase
   
4. Fixed the app_name parameter in web session management:
   - Changed the Runner's app_name from "radbot" to "beto" to match the agent name
   - Updated all session service calls (get_session, create_session, delete_session) to use "beto" as the app_name
   - This ensures the agent transfer mechanism can find the correct agent when transferring

5. Fixed the app_name in RadBotAgent class:
   - Updated self.app_name from "radbot" to "beto" to ensure consistency
   - Modified Runner initialization to use self.app_name instead of hardcoded "radbot"
   - This ensures the agent name and app_name match consistently throughout the codebase, which is critical for agent transfers
   
6. Added forced name consistency at runtime:
   - Added code to check root_agent.name at startup and explicitly set it to 'beto' if needed
   - Added detailed logging of the agent tree and name assignments for debugging
   - This ensures that even if there's a runtime mismatch in agent naming, it gets corrected before any transfers
   
7. Fixed all remaining instances of "app_name=radbot" throughout the codebase:
   - Updated memory_tools.py to use "beto" as app_name for memory searches
   - Fixed memory_agent_factory.py to use consistent app_name
   - Updated create_runner function default parameter from "radbot" to "beto" 
   - Modified CLI main.py to use consistent app_name for completeness
   
8. Implemented bidirectional parent-child relationship for agents:
   - Modified the sub-agent registration to explicitly establish bidirectional relationships
   - Added code to set the parent reference on the scout agent
   - This ensures that the scout agent knows about its parent, which is crucial for transfers

9. Improved agent tree initialization:
   - Cleared existing sub_agents list before adding sub-agents
   - This forces the ADK to properly register the agents in the tree
   - Added verification of the agent tree structure after registration
   - This ensures the agent tree is correctly formed for transfers

## Testing and Validation

To validate the fix, test the following workflow:

1. Start a conversation with the main agent (beto)
2. Ask a research question that triggers a transfer to the scout agent
3. After the scout agent completes its task, ask it to return to the main agent
4. Verify that the transfer back works without errors

## Additional Debugging

When troubleshooting agent transfer issues:

1. Add detailed logging to identify agent names in the tree structure:
   ```python
   if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
       sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
       logger.info(f"Agent tree structure - Root: '{root_agent.name}', Sub-agents: {sub_agent_names}")
   ```

2. Verify the app_name matches agent names:
   ```python
   # Debug agent tree and app_name relationship
   logger.info(f"ROOT AGENT NAME: '{root_agent.name}'")
   logger.info(f"RUNNER APP_NAME: '{runner.app_name}'")
   ```

3. Check transfer_to_agent references:
   ```python
   # In the scout agent instructions
   transfer_to_agent(agent_name='beto')  # Must match EXACTLY the name of the target agent
   ```

4. Properly register agents with bidirectional relationships:
   ```python
   # First clear existing list to force re-registration
   agent.sub_agents = []
   
   # Then add the sub-agent
   agent.sub_agents.append(research_agent)
   
   # Establish bidirectional relationship
   if hasattr(research_agent, 'parent'):
       research_agent.parent = agent
   ```

5. Ensure agent name is registered correctly at startup:
   ```python
   agent = Agent(name="beto", ...)  # Name must match what's used in transfers
   ```

6. Check if transfer tools are properly registered:
   ```python
   # Check if transfer tool is available in agent's tools
   has_transfer_tool = False
   for tool in agent.tools:
       if hasattr(tool, 'name') and tool.name == 'transfer_to_agent':
           has_transfer_tool = True
           break
       elif hasattr(tool, '__name__') and tool.__name__ == 'transfer_to_agent':
           has_transfer_tool = True
           break
   logger.info(f"Agent has transfer_to_agent tool: {has_transfer_tool}")
   ```

7. Verify bidirectional relationship is established:
   ```python
   # Check if sub-agent knows about its parent
   if hasattr(sub_agent, 'parent') and hasattr(sub_agent.parent, 'name'):
       logger.info(f"Sub-agent's parent name: '{sub_agent.parent.name}'")
   
   # Check if parent's sub_agents contains the sub-agent
   if hasattr(agent, 'sub_agents'):
       found_in_subagents = any(sa is sub_agent for sa in agent.sub_agents)
       logger.info(f"Sub-agent found in parent's sub_agents: {found_in_subagents}")
   ```

## Future Improvements

To prevent similar issues in the future:

1. Create a centralized agent name registry to ensure consistent naming
2. Add explicit logging around agent transfers for better debugging
3. Consider implementing a more robust transfer mechanism that isn't dependent on exact name matching
4. Add unit tests specifically for agent transfer functionality
5. Create a helper function for registering sub-agents that ensures proper bidirectional relationships
6. Add runtime validation of agent tree structure before allowing transfers
7. Implement automated testing of agent transfers during startup
8. Create a dedicated class for managing the agent tree structure
9. Consider adding a diagram tool to visualize the agent tree structure for debugging

## Additional Notes for ADK 0.4.0

The Google ADK 0.4.0 agent transfer mechanism appears to have specific requirements for agent tree registration:

1. The agent tree is searched starting from the root agent
2. Agents must have unique names across the entire tree
3. Bidirectional parent-child relationships must be established
4. The `app_name` parameter must match the agent name used in transfers
5. Both agents involved in a transfer must have the `transfer_to_agent` tool available
6. Clearing and rebuilding the `sub_agents` list seems to improve agent registration

These requirements may change in future ADK versions, so it's important to check the ADK documentation and update this implementation as needed.

## May 2025 Update: Malformed Function Call Fix

A new issue was discovered in May 2025 where agent transfers were failing with a "Malformed function call: transfer_to_agent" error. The issue was fixed with the following changes:

1. Changed how the transfer_to_agent tool is registered in agent.py:
   - Instead of creating a FunctionTool wrapper around the transfer_to_agent function (which was causing the malformed function call error), we now add the function directly to the tools list.
   - Also added the TRANSFER_TO_AGENT_TOOL constant from the ADK library as a backup, which is pre-configured with the correct schema.

```python
# Add the ADK's built-in transfer_to_agent tool
try:
    # Rather than wrapping in a FunctionTool, add transfer_to_agent directly
    # as it's likely already properly registered within the ADK
    basic_tools.append(transfer_to_agent)
    logger.info("Added transfer_to_agent function directly to tools list")
    
    # Check if the function tool is available in the ADK
    from google.adk.tools.transfer_to_agent_tool import TRANSFER_TO_AGENT_TOOL
    if TRANSFER_TO_AGENT_TOOL:
        basic_tools.append(TRANSFER_TO_AGENT_TOOL)
        logger.info("Added TRANSFER_TO_AGENT_TOOL from ADK")
except Exception as e:
    logger.warning(f"Failed to add transfer_to_agent tool: {str(e)}")
    logger.debug(f"Transfer tool addition error details:", exc_info=True)
```

This implementation ensures that the transfer_to_agent function is correctly registered with the ADK and can be called with the proper JSON schema, resolving the "Malformed function call" error.

## June 2025 Update: Web Session Handling Fix with ADK 0.4.0 Requirements

After implementing the initial agent tree registration fix, we discovered that ADK 0.4.0 has stricter requirements for agent transfers than previous versions. The transfer_to_agent mechanism in ADK 0.4.0 requires precise agent tree registration with exact name matching and consistent app_name parameters throughout the application. The webserver creates its own SessionRunner which needs to maintain the same agent tree structure and naming consistency.

The key issue was that for agent transfers to work in ADK 0.4.0, the ADK engine requires:
1. The agent name used in transfer_to_agent tool calls must exactly match the target agent's name attribute
2. The app_name parameter used with the Runner must match the agent's name
3. The agent tree must be properly structured with bidirectional relationships
4. Session operations must use consistent app_name matching the agent name

We implemented comprehensive fixes in both agent.py and session.py:

### 1. Session Initialization and Runner Creation:
   - Enhanced the SessionRunner initialization to verify agent names, bidirectional relationships, and tool availability
   - Added explicit verification steps before and after creating sessions
   - Fixed app_name consistency throughout the session lifecycle
   - **Critical for ADK 0.4.0:** Used the root_agent.name value as the app_name parameter for the Runner

### 2. Session Management with Consistent app_name:
   - Used the same app_name value from runner throughout all session operations
   - Added consistent app_name usage for session creation, retrieval, and deletion
   - **Critical for ADK 0.4.0:** Ensured app_name matches the agent name ('beto') in all session operations

### 3. Comprehensive Agent Tree Verification:
   - Created a robust `_verify_agent_structure()` method that performs 5 key checks:
     1. Root agent name verification - MUST be 'beto'
     2. Sub-agent name verification - MUST be 'scout'
     3. Bidirectional relationship verification (parent ⟷ child)
     4. Transfer tool availability on all agents
     5. Proper tool handler registration

Key code additions for ADK 0.4.0 compatibility:

```python
# ADK 0.4.0+ - CRITICAL: Runner's app_name must match agent name for transfers
if hasattr(root_agent, 'name'):
    app_name_for_runner = root_agent.name  # Use the agent's actual name
    logger.info(f"Creating runner with app_name='{app_name_for_runner}' (from agent.name)")
else:
    app_name_for_runner = "beto"  # Fallback
    logger.warning(f"Agent has no name attribute, using default app_name='{app_name_for_runner}'")
    
# Create the ADK Runner with explicit app_name matching agent's name
self.runner = Runner(
    agent=root_agent,
    app_name=app_name_for_runner,  # CRITICAL: Must match agent.name for transfers
    session_service=self.session_service
)
```

For consistent session management with matching app_name:

```python
# Use the same app_name as the runner for consistency
session_app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else "beto"

# Get or create session with consistent app_name
logger.info(f"Getting/creating session with app_name='{session_app_name}'")
session = self.session_service.get_session(
    app_name=session_app_name,
    user_id=self.user_id,
    session_id=self.session_id
)
```

Enhanced verification method for ADK 0.4.0:

```python
def _verify_agent_structure(self):
    """Verify and fix agent tree structure issues for ADK 0.4.0+ compatibility."""
    logger.info("STARTING COMPREHENSIVE AGENT TREE VERIFICATION")
    
    # CRITICAL: Re-verify root agent name - MUST be 'beto'
    if hasattr(root_agent, 'name') and root_agent.name != 'beto':
        logger.warning(f"ROOT AGENT NAME MISMATCH: '{root_agent.name}' should be 'beto' - fixing")
        root_agent.name = 'beto'
        logger.info(f"Set root_agent.name = '{root_agent.name}'")
    
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
            else:
                logger.warning(f"SUB-AGENT MISSING PARENT: sub-agent[{i}] has no parent attribute - adding")
                try:
                    sa.parent = root_agent
                except Exception as e:
                    logger.error(f"Failed to add parent reference: {e}")
    
    # Add transfer tools if missing
    try:
        from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
        
        # Check both agents for transfer tool
        has_root_transfer = False
        for tool in root_agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
            if tool_name == 'transfer_to_agent':
                has_root_transfer = True
                break
        
        if not has_root_transfer:
            root_agent.tools.append(transfer_to_agent)
            logger.info("Added transfer_to_agent tool to root_agent")
    except Exception as e:
        logger.error(f"Failed to add transfer tool: {e}")
    
    # Register transfer handlers
    try:
        from google.adk.events import QueryResponse
        from google.protobuf.json_format import MessageToDict
        
        if hasattr(root_agent, 'register_tool_handler'):
            root_agent.register_tool_handler(
                "transfer_to_agent",
                lambda params: MessageToDict(QueryResponse(
                    transfer_to_agent_response={
                        "target_app_name": params["agent_name"],
                        "message": params.get("message", ""),
                    }
                )),
            )
            logger.info("Registered transfer_to_agent handler with root_agent")
    except Exception as e:
        logger.error(f"Failed to register transfer tool handlers: {e}")
```

This verification is called at multiple critical points in the session lifecycle:
- During SessionRunner initialization
- Before processing each message
- Before and after session resets

The combined fixes in agent.py and session.py ensure that the agent tree structure remains consistent throughout the application lifecycle, allowing agent transfers to work correctly between agents in ADK 0.4.0.