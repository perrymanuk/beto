# ADK 0.4.0 FunctionTool Parameter Fix

## Issue

With the upgrade to ADK 0.4.0, a parameter name in the `FunctionTool` class changed from `function` to `func`. This change caused errors when trying to create function tools using the old parameter name:

```
2025-05-09 00:06:07,548 - radbot.tools.claude_prompt - WARNING - Error creating tool with function_schema: FunctionTool.__init__() got an unexpected keyword argument 'function', using basic tool
2025-05-09 00:06:07,548 - radbot.web.api.session - WARNING - Error loading Claude prompt tool: FunctionTool.__init__() got an unexpected keyword argument 'function'
```

## Analysis

The ADK 0.4.0 `FunctionTool` class constructor signature has changed and now requires a `func` parameter instead of the previous `function` parameter. This change was verified by examining the signature of `FunctionTool.__init__` method:

```python
FunctionTool init signature: (self, func: Callable[..., Any])
```

When we attempted to use the old parameter name, the error was triggered, but our code had a fallback mechanism which allowed basic operation to continue.

## Fix

The fix consisted of updating the following files:

1. `radbot/tools/claude_prompt.py` - Updated to use the correct `func` parameter when creating a FunctionTool instance:

```python
# Old code
prompt_tool = FunctionTool(
    function=prompt_claude,
    function_schema=prompt_claude_schema
)

# New code
prompt_tool = FunctionTool(
    func=prompt_claude
)
```

2. `radbot/web/api/session.py` - Updated the tool name detection logic to be more robust and handle multiple ways of getting the tool name:

```python
# Try multiple approaches to get the tool name
tool_name = None
# Try to get name attribute
if hasattr(claude_prompt_tool, "name"):
    tool_name = claude_prompt_tool.name
# Try to get __name__ attribute
elif hasattr(claude_prompt_tool, "__name__"):
    tool_name = claude_prompt_tool.__name__
# Try to get name from _get_declaration().name
elif hasattr(claude_prompt_tool, "_get_declaration"):
    try:
        declaration = claude_prompt_tool._get_declaration()
        if hasattr(declaration, "name"):
            tool_name = declaration.name
    except:
        pass
# Fallback to string representation
if not tool_name:
    tool_name = str(claude_prompt_tool)
```

## Testing

A test script (`test_functiontool.py`) was created to verify the correct parameter name for FunctionTool in ADK 0.4.0. The test confirmed that `func` is the correct parameter name, and attempts to use `function` resulted in errors.

The fix was then tested by running the code that creates a Claude prompt tool, which successfully created the tool without errors:

```
Successfully created tool: <google.adk.tools.function_tool.FunctionTool object at 0x1049e7ad0>
...
2025-05-09 00:19:35,916 - radbot.tools.claude_prompt - INFO - Created Claude prompt tool with proper ADK 0.4.0 parameters
```

## Lessons Learned

1. API changes in dependencies can break existing code - always check for parameter name changes when upgrading libraries
2. It's helpful to have fallback mechanisms in place for error cases
3. When creating abstraction layers over third-party libraries, consider wrapping the initialization code to isolate parameter changes
4. Using direct parameter inspection (via `inspect.signature()`) is a useful way to diagnose these issues

## Related Documentation

- [ADK 0.4.0 Release Notes](https://github.com/google/adk-python/releases/tag/v0.4.0)
- [ADK Function Tools Documentation](https://google.github.io/adk-docs/tools/function-tools/)