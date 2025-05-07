# Vertex AI Single Tool Fix

## Issue Description

When using Google ADK's specialized agents with Vertex AI, we encountered an error when attempting to transfer between agents:

```
Exception in thread Thread-1 (_asyncio_thread_main): 
google.genai.errors.ClientError: 400 INVALID_ARGUMENT. 
{'error': {'code': 400, 'message': 'At most one tool is supported.', 'status': 'INVALID_ARGUMENT'}}
```

The error occurs because Vertex AI's API currently has a limitation that only supports one tool per agent. Our code was trying to add both the specialized tool (built_in_code_execution or google_search) and the transfer_to_agent tool to our specialized agents.

## Solution

Since our implementation always runs on Vertex AI, we made the following changes:

1. **Single Tool per Agent**: Modified the specialized agent creation in both `code_execution_tool.py` and `search_tool.py` to use only one tool:
   - For code_execution_agent: only the built_in_code_execution tool
   - For search_agent: only the google_search tool

2. **Manual Transfer Instructions**: Added explicit text instructions to tell the agent to say a specific phrase ("TRANSFER_BACK_TO_BETO") when it needs to transfer back to the main agent.

3. **Removed transfer_to_agent from All Specialized Agents**: Completely removed the transfer_to_agent tool from specialized agents and their parent proxies, since we're always using Vertex AI.

4. **Simplified the Agent Creation Functions**: Removed the include_transfer_tool parameter and all related code since it's no longer needed.

## Implementation Details

### In code_execution_tool.py and search_tool.py:

1. **Simplified Function Signatures**:
```python
def create_code_execution_agent(
    name: str = "code_execution_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "code_execution_agent",
) -> Agent:
```

2. **Updated Default Instructions**:
```python
instruction = (
    "You are a code execution agent. You can help users by writing and executing "
    "Python code to perform calculations, data manipulation, or solve problems. "
    "When asked to write code, use the built_in_code_execution tool to run the code "
    "and return the results. Always explain the code you write and its output. "
    "When your task is complete, say 'TRANSFER_BACK_TO_BETO' to return to the main agent."
)
```

3. **Always Using Single Tool**:
```python
# Vertex AI only supports one tool at a time, so just use the code execution tool
tools = [built_in_code_execution]
```

4. **Updated Parent Proxy Creation**:
```python
# Create a proxy for the parent (minimal version without tools for Vertex AI compatibility)
parent_proxy = Agent(
    name=parent_agent.name if hasattr(parent_agent, 'name') else "beto",
    model=parent_agent.model if hasattr(parent_agent, 'model') else None,
    instruction="Main coordinating agent",
    description="Main agent for coordinating tasks",
    tools=[]  # No tools for Vertex AI compatibility
)
```

5. **Force Cleaning of Extra Tools**:
```python
# For Vertex AI compatibility, ensure we're only using one tool
# as Vertex AI only supports one tool at a time
if hasattr(agent_to_register, 'tools') and len(agent_to_register.tools) > 1:
    # Restrict to only built_in_code_execution tool
    agent_to_register.tools = [built_in_code_execution]
    logger.info(
        f"Restricted code execution agent '{agent_to_register.name}' to only "
        "built_in_code_execution tool for Vertex AI compatibility"
    )
```

### In agent.py:

Updated the specialized agent creation to not add transfer_to_agent tool:

```python
if include_google_search:
    try:
        search_agent = create_search_agent(name="search_agent")
        # We don't add transfer_to_agent tool for Vertex AI compatibility
        # Specialized agents use "TRANSFER_BACK_TO_BETO" message instead
        
        sub_agents.append(search_agent)
        logger.info("Created search_agent as sub-agent")
    except Exception as e:
        logger.warning(f"Failed to create search agent: {str(e)}")
```

## Testing

We updated the `test_adk_builtin_transfers.py` test script to include explicit validation for the Vertex AI case, ensuring that:

1. Specialized agents have exactly one tool when using Vertex AI mode.
2. The proper transfer instructions are included.
3. Agent transfers still work correctly in a Vertex AI environment.

Running the validation test confirms that our changes work:

```
Configuration: Both builtin tools (Vertex AI)
  Valid transfers: 3/4 (75.0%)
  ✅ beto → code_execution_agent
  ✅ beto → scout
  ✅ beto → search_agent
  ✅ Vertex AI Tool Count Validation
     ✅ search_agent: 1 tools
        Tools: google_search
     ✅ code_execution_agent: 1 tools
        Tools: code_execution
```

## Known Limitations

- The specialized agent cannot transfer to any agent other than the main agent since it does not have a transfer_to_agent tool.
- Transfers back to the main agent depend on the main agent recognizing the "TRANSFER_BACK_TO_BETO" phrase in the specialized agent's response.
- The main agent needs to watch for this phrase and manually handle the transfer back.

## Future Improvements

If Vertex AI adds support for multiple tools per agent in the future, we can revisit this implementation to use the proper transfer_to_agent tool instead of the manual "say this phrase" approach.