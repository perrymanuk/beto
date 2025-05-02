#!/usr/bin/env python3
"""
Check MCP fileserver environment variables.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    """Check MCP fileserver environment variables."""
    print("MCP Fileserver Environment Check")
    print("===============================")
    
    # Check MCP_FS_ROOT_DIR
    mcp_fs_root_dir = os.environ.get("MCP_FS_ROOT_DIR")
    if mcp_fs_root_dir:
        print(f"✅ MCP_FS_ROOT_DIR is set to: {mcp_fs_root_dir}")
        
        # Check if directory exists
        if os.path.isdir(mcp_fs_root_dir):
            print(f"✅ Directory exists")
        else:
            print(f"❌ Directory does not exist: {mcp_fs_root_dir}")
    else:
        print("❌ MCP_FS_ROOT_DIR is not set")
        print("   Fileserver tools will not be available to the agent")
        print("\n   To fix this, set the environment variable before running:")
        print("   export MCP_FS_ROOT_DIR=/path/to/accessible/directory")
    
    # Check MCP_FS_ALLOW_WRITE
    mcp_fs_allow_write = os.environ.get("MCP_FS_ALLOW_WRITE", "false").lower()
    is_write_enabled = mcp_fs_allow_write in ("true", "yes", "1", "t", "y")
    print(f"\nMCP_FS_ALLOW_WRITE: {mcp_fs_allow_write} ({is_write_enabled})")
    
    # Check MCP_FS_ALLOW_DELETE
    mcp_fs_allow_delete = os.environ.get("MCP_FS_ALLOW_DELETE", "false").lower()
    is_delete_enabled = mcp_fs_allow_delete in ("true", "yes", "1", "t", "y")
    print(f"MCP_FS_ALLOW_DELETE: {mcp_fs_allow_delete} ({is_delete_enabled})")
    
    # Check for nest_asyncio
    try:
        import nest_asyncio
        print("\n✅ nest_asyncio is installed (required for MCP fileserver)")
    except ImportError:
        print("\n❌ nest_asyncio is not installed")
        print("   This package is required for the MCP fileserver to work")
        print("   Run: pip install nest_asyncio")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())