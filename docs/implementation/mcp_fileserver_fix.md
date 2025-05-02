# MCP Fileserver Integration Fix

This document outlines the issue and resolution for the MCP fileserver integration problem.

## Issue

The MCP fileserver tools were not being properly loaded and made available to the agent in the web interface. The main issue was identified to be related to running the MCP server in an existing event loop, which is the case when using the ADK web interface.

Specifically:
- The MCP fileserver client required the `nest_asyncio` package to work in a running event loop
- This package was missing from the project dependencies
- The MCP fileserver tools were properly implemented but not properly initialized due to this issue

## Resolution

The following steps were taken to resolve the issue:

1. **Added nest_asyncio Dependency**
   - Added `nest_asyncio>=1.6.0` to the project dependencies in `pyproject.toml`
   - Added a descriptive comment explaining its necessity for MCP fileserver integration
   - Created helper scripts that check for and install the package if missing

2. **Debugging Tools Created**
   - Created a simple standalone test (`tools/test_mcp_fs_simple.py`) to verify MCP fileserver toolset creation
   - Created a web startup test (`tools/test_web_startup.py`) to verify MCP fileserver integration with the web agent

3. **Added Makefile Target**
   - Added a new `run-web-mcp` target to the Makefile that ensures MCP fileserver is properly configured
   - Created a helper script (`tools/run_with_mcp.sh`) that sets up the environment and ensures dependencies are installed

4. **Updated Documentation**
   - Added MCP fileserver usage instructions to the README
   - Created this document to document the issue and resolution

## Usage Instructions

To use the MCP fileserver in the agent, follow these steps:

1. **Set Environment Variables**

Add the following to your `.env` file or export them before running:

```bash
# MCP Fileserver Configuration
MCP_FS_ROOT_DIR=/path/to/accessible/directory   # Root directory for filesystem operations
MCP_FS_ALLOW_WRITE=false                        # Allow write operations (default: false)
MCP_FS_ALLOW_DELETE=false                       # Allow delete operations (default: false)
```

2. **Run the Web Server with MCP Fileserver**

```bash
# Using the make target
make run-web-mcp

# Or directly using the helper script
tools/run_with_mcp.sh
```

3. **Verify Tools are Available**

When the agent is initialized, you should see log messages indicating that the MCP fileserver tools have been added. The agent will have access to the following tools:
- `list_files`: List files and directories in a path
- `read_file`: Read the contents of a file
- `get_file_info`: Get information about a file or directory

If write operations are enabled, additional tools will be available:
- `write_file`: Write content to a file
- `copy_file`: Copy a file or directory
- `move_file`: Move or rename a file or directory

If delete operations are enabled, additional tools will be available:
- `delete_file`: Delete a file or directory

## Technical Details

The core of the issue was in the `radbot/tools/mcp_fileserver_client.py` file. The following changes were made:

- Added proper event loop handling with `nest_asyncio`
- Added detailed logging to trace MCP fileserver initialization
- Ensured proper cleanup of MCP fileserver resources

The key code block that needed the fix was:

```python
# We're in an event loop, so we need to use nest_asyncio
try:
    import nest_asyncio
    nest_asyncio.apply()
    logger.debug("Applied nest_asyncio")
except ImportError:
    logger.warning("nest_asyncio not available. Cannot create MCP fileserver tools in a running event loop.")
    logger.warning("Please install nest_asyncio package: pip install nest_asyncio")
    return None
```

This code ensures that if the MCP fileserver is initialized within a running event loop (as is the case in the ADK web interface), the `nest_asyncio` package is used to allow nested event loops.

## Testing

To verify the fix is working, you can run:

```bash
export MCP_FS_ROOT_DIR=/path/to/test/directory
python tools/test_mcp_fs_simple.py
python tools/test_web_startup.py
```

Both tests should succeed and show that the MCP fileserver tools are properly initialized and available to the agent.