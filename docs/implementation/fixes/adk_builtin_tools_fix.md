# ADK Built-in Tools Fix

## Issue

After integrating Google Search and Code Execution tools from ADK 0.4.0, an error occurred:

```python
async for event in self._postprocess_handle_function_calls_async(
  File "/Users/perry.manuk/git/perrymanuk/radbot/.venv/lib/python3.11/site-packages/google/adk/flows/llm_flows/base_llm_flow.py", line 416, in _postprocess_handle_function_calls_async
    agent_to_run = self._get_agent_to_run(
                   ^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/perry.manuk/git/perrymanuk/radbot/radbot/web/api/session.py", line 224, in patched_llm_get_agent_to_run
    agent = invocation_context.agent
            ^^^^^^^^^^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'agent'
```

## Root Cause Analysis

1. The issue occurred in the `patched_llm_get_agent_to_run` function in `/radbot/web/api/session.py`.

2. The problem was a parameter order mismatch between our monkey-patched function and the ADK's actual implementation:

   - **Our implementation:** `def patched_llm_get_agent_to_run(self, agent_name: str, invocation_context: Any)`
   - **ADK implementation:** `def _get_agent_to_run(self, invocation_context: InvocationContext, transfer_to_agent)`

3. When the ADK called our patched function, it passed:
   - The `invocation_context` object as the first parameter (which our code interpreted as `agent_name`)
   - The agent name string as the second parameter (which our code interpreted as `invocation_context`)

4. This caused the error when our code tried to access `invocation_context.agent` since the `invocation_context` parameter was actually a string.

## Fix Implementation

1. Fixed the parameter order in our monkey-patched function to match the ADK's implementation:
   ```python
   def patched_llm_get_agent_to_run(self, invocation_context: Any, agent_name: str) -> BaseAgent:
   ```

2. Added defensive checks to handle unexpected parameter types:
   - Verifying if `agent_name` is a string
   - Handling cases where `invocation_context` is a string
   - Adding detailed logging for debugging

3. Updated the call to the original method to use the correct parameter order:
   ```python
   result = original_llm_get_agent_to_run(self, invocation_context, agent_name)
   ```

## Validation

This fix ensures compatibility with the ADK built-in tools like Google Search and Code Execution, while maintaining our custom agent transfer functionality.

## Additional Resources

- [ADK 0.4.0 Agent Transfer Guide](/docs/implementation/adk_agent_transfer_guide.md)
- [ADK Built-in Tools Documentation](/docs/implementation/adk_builtin_tools.md)