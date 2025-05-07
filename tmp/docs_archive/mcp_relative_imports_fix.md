# MCP Relative Imports Fix

## Issue

After the initial fix for the class name mismatch and missing functions, another error occurred:

```
No module named 'radbot.tools.mcp_tools'
```

This issue occurred because the code was looking for modules at the old import path (`radbot.tools.mcp_tools`) instead of the new path after restructuring (`radbot.tools.mcp.mcp_tools`).

## Root Cause

When the MCP tools were moved from `radbot/tools/` to `radbot/tools/mcp/`, the import statements in some files were not updated to reflect the new module structure. This led to import errors when the code tried to reference modules at their old locations.

Specific instances of outdated imports included:

1. In `mcp_utils.py`:
   - `from radbot.tools.mcp_tools import create_home_assistant_toolset`
   - `from radbot.tools.mcp_tools import _create_home_assistant_toolset_async`

2. In `mcp_tools.py`:
   - `from radbot.tools.mcp_utils import find_home_assistant_entities`

## Solution

Updated all import statements to reflect the new module structure:

1. In `mcp_utils.py`:
   - Changed `from radbot.tools.mcp_tools import create_home_assistant_toolset` to `from radbot.tools.mcp.mcp_tools import create_home_assistant_toolset`
   - Updated all instances of `from radbot.tools.mcp_tools import _create_home_assistant_toolset_async` to `from radbot.tools.mcp.mcp_tools import _create_home_assistant_toolset_async`

2. In `mcp_tools.py`:
   - Changed `from radbot.tools.mcp_utils import find_home_assistant_entities` to `from radbot.tools.mcp.mcp_utils import find_home_assistant_entities`

These changes ensure that all imports correctly reference the new module structure after the code restructuring.

## Lessons Learned

When restructuring code and moving files to new locations:

1. Be thorough in updating import statements throughout the codebase
2. Use search tools to find all instances of imports that need to be updated
3. Pay special attention to circular imports between modules
4. Check for imports in less obvious places like inside function definitions
5. Consider using relative imports for closely related modules to make restructuring easier

Testing after restructuring is essential to catch these kinds of import errors before they affect production code.
