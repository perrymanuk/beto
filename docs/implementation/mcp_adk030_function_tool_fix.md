# MCP ADK 0.3.0 FunctionTool Constructor Fix

## Issue

After fixing the async context and file server integration issues, a new error appeared:

```
FunctionTool.__init__() got an unexpected keyword argument 'name'
```

This error occurs when using Google ADK 0.3.0+ which has a different API for creating FunctionTool objects. The constructor no longer accepts named parameters like `name`, `description`, and `parameters`.

## Root Cause

In ADK versions prior to 0.3.0, FunctionTool could be instantiated with named parameters:

```python
tool = FunctionTool(
    name="tool_name",
    description="Tool description",
    parameters={...schema...}
)
```

However, in ADK 0.3.0 and later, the constructor only accepts a function directly:

```python
tool = FunctionTool(func=my_function)
```

The schema, name, and description are now automatically extracted from the function's type hints and docstring.

We were still using the old constructor format despite having upgraded to ADK 0.3.0 as indicated in the project's `pyproject.toml`:

```toml
dependencies = [
    "google-adk>=0.3.0",
    # ... other dependencies ...
]
```

## Solution

The solution was to update the `mcp_fileserver_client.py` file to create FunctionTool objects using the function-based approach:

1. Changed the stub tool creation in `create_fileserver_toolset()` to use wrapper functions instead of direct parameter passing:

```python
def list_files_func(path: str = "") -> dict:
    """List files and directories in a path."""
    return handle_fileserver_tool_call("list_files", {"path": path}).function_call_event
    
# Create the tool from the function
tools.append(FunctionTool(func=list_files_func))
```

2. Similarly updated the async tool creation to use wrapper functions:

```python
def make_tool_func(tool_name):
    # Use variable number of keyword arguments to handle any parameter schema
    def tool_func(**kwargs):
        # Forward the call to our handler
        return handle_fileserver_tool_call(tool_name, kwargs).function_call_event
    
    # Set the docstring based on the tool description
    tool_func.__doc__ = mcp_tool.description
    # Set the name to match the original tool
    tool_func.__name__ = tool_name
    
    return tool_func

# Create a FunctionTool from our wrapper function
func = make_tool_func(tool_name)
tools.append(FunctionTool(func=func))
```

This ensures compatibility with the new ADK 0.3.0 API while maintaining the same functionality.

## Benefits

1. **ADK 0.3.0 Compatibility**: The code now works correctly with the latest ADK version.
2. **Better Type Handling**: The new approach allows for better type inference and validation.
3. **More Pythonic**: The new approach feels more natural in Python, using functions directly.
4. **Docstring Integration**: Documentation is now directly tied to the function's docstring.

## Lessons Learned

1. **API Changes**: When upgrading libraries, carefully check for API changes, especially constructor signatures.
2. **Version Pinning**: Consider pinning specific versions rather than using `>=` for critical dependencies.
3. **Test After Upgrades**: Always test thoroughly after upgrading dependencies.
4. **Function-First Design**: ADK 0.3.0 encourages a function-first design approach, which is more Pythonic.
5. **Documentation Check**: Always verify the documentation for the specific version you're using.

## Related Issues

This fix relates to the previous MCP fileserver fixes:
- [MCP Fileserver Import Error Fix](mcp_fileserver_fix.md)
- [MCP Parent __init__.py Fix](mcp_parent_init_fix.md)
- [MCP Fileserver Async Fix](mcp_fileserver_async_fix.md)

Together, these fixes ensure the MCP fileserver tools work correctly in all contexts (CLI and web) and with the latest ADK version.
