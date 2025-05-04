# MCP Tools Import Errors Fix

## Issues

After restructuring the tools into their own folders, two import errors occurred:

1. Class name mismatch:
```
cannot import name 'MCPFileServer' from 'radbot.tools.mcp.mcp_fileserver_server' (/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/mcp/mcp_fileserver_server.py)
```

2. Missing function:
```
cannot import name 'get_available_mcp_tools' from 'radbot.tools.mcp.mcp_tools' (/Users/perry.manuk/git/perrymanuk/radbot/radbot/tools/mcp/mcp_tools.py)
```

## Root Causes

1. **Class Name Mismatch**: The `__init__.py` file was trying to import a class called `MCPFileServer` but the actual class in the implementation file was named `FileServerMCP`.

2. **Missing Functions**: Two functions were referenced in the `__init__.py` file but were missing in their respective modules:
   - `get_available_mcp_tools` was missing from `mcp_tools.py`
   - `convert_to_adk_tool` was missing from `mcp_utils.py`

## Solutions

### 1. Fixed Class Name Import

Updated the import statement in `radbot/tools/mcp/__init__.py`:

```python
# Before
from radbot.tools.mcp.mcp_fileserver_server import MCPFileServer

# After
from radbot.tools.mcp.mcp_fileserver_server import FileServerMCP
```

Also updated the corresponding entry in the `__all__` list.

### 2. Added Missing Functions

Added the `get_available_mcp_tools` function to `mcp_tools.py`:

```python
def get_available_mcp_tools() -> List[Any]:
    """
    Get a list of all available MCP tools.
    
    This function returns a consolidated list of all available MCP tools
    including Home Assistant, FileServer, and other MCP integrations.
    
    Returns:
        List of available MCP tools
    """
    tools = []
    
    # Try to get Home Assistant tools
    try:
        ha_tools = create_home_assistant_toolset()
        if ha_tools:
            if isinstance(ha_tools, list):
                tools.extend(ha_tools)
                logger.info(f"Added {len(ha_tools)} Home Assistant MCP tools")
            else:
                tools.append(ha_tools)
                logger.info("Added Home Assistant MCP toolset")
    except Exception as e:
        logger.warning(f"Failed to get Home Assistant MCP tools: {str(e)}")
    
    # Try to get FileServer tools if available
    try:
        # Import here to avoid circular imports
        from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset
        fs_tools = create_fileserver_toolset()
        if fs_tools:
            if isinstance(fs_tools, list):
                tools.extend(fs_tools)
                logger.info(f"Added {len(fs_tools)} FileServer MCP tools")
            else:
                tools.append(fs_tools)
                logger.info("Added FileServer MCP toolset")
    except Exception as e:
        logger.warning(f"Failed to get FileServer MCP tools: {str(e)}")
        
    # Try to get Crawl4AI tools if available
    try:
        # Import here to avoid circular imports
        from radbot.tools.mcp.mcp_crawl4ai_client import create_crawl4ai_toolset
        crawl4ai_tools = create_crawl4ai_toolset()
        if crawl4ai_tools:
            if isinstance(crawl4ai_tools, list):
                tools.extend(crawl4ai_tools)
                logger.info(f"Added {len(crawl4ai_tools)} Crawl4AI MCP tools")
            else:
                tools.append(crawl4ai_tools)
                logger.info("Added Crawl4AI MCP toolset")
    except Exception as e:
        logger.warning(f"Failed to get Crawl4AI MCP tools: {str(e)}")
    
    # Add other MCP tools as they become available
    
    return tools
```

Added the `convert_to_adk_tool` function to `mcp_utils.py`:

```python
def convert_to_adk_tool(function: Callable, name: Optional[str] = None, description: Optional[str] = None) -> FunctionTool:
    """
    Convert a function to an ADK-compatible FunctionTool.
    
    This utility helps convert standard functions to ADK-compatible tools
    with appropriate schema information.
    
    Args:
        function: The function to convert
        name: Optional name for the tool (defaults to function name)
        description: Optional description for the tool
        
    Returns:
        The converted FunctionTool
    """
    # Get the function name if not provided
    if not name:
        name = function.__name__
        
    # Get description from docstring if not provided
    if not description and function.__doc__:
        description = function.__doc__.split('\n')[0].strip()
    elif not description:
        description = f"{name} function"
    
    try:
        # Try to create a tool using ADK 0.3.0+ style
        tool = FunctionTool(
            function=function,
            function_schema={
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        )
        logger.info(f"Created tool {name} using ADK 0.3.0+ style")
    except TypeError:
        # Fall back to older ADK versions
        tool = FunctionTool(
            function,
            {
                "name": name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        )
        logger.info(f"Created tool {name} using legacy FunctionTool style")
    
    return tool
```

## Testing

After implementing these changes, the import errors were resolved and the MCP tools functionality was restored.

## Lessons Learned

When restructuring code:
1. Ensure consistent class and function naming across modules
2. Check all imports and references after moving files
3. Use search tools to identify all references to renamed elements
4. Consider using find/grep tools to identify all references to renamed elements
5. When moving functionality to new modules, ensure all referenced functions are properly