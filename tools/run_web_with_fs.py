#!/usr/bin/env python3
"""
Run the ADK web server with MCP filesystem configured.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

def main():
    """Set environment variables and run ADK Web server."""
    # Check environment variables
    mcp_fs_root_dir = os.environ.get("MCP_FS_ROOT_DIR")
    if not mcp_fs_root_dir:
        print("ERROR: MCP_FS_ROOT_DIR environment variable is not set.")
        print("Please set it to a valid directory path before running.")
        print("Example: export MCP_FS_ROOT_DIR=/path/to/root/directory")
        return 1
    
    # Log configuration
    print(f"MCP Fileserver Configuration:")
    print(f"  Root Directory: {mcp_fs_root_dir}")
    print(f"  Allow Write: {os.environ.get('MCP_FS_ALLOW_WRITE', 'false')}")
    print(f"  Allow Delete: {os.environ.get('MCP_FS_ALLOW_DELETE', 'false')}")
    
    # Verify nest_asyncio is installed
    try:
        import nest_asyncio
        print("✅ nest_asyncio is available (required for MCP fileserver)")
    except ImportError:
        print("❌ ERROR: nest_asyncio is not installed")
        print("Please install it with: pip install nest_asyncio")
        return 1
    
    # Run the ADK web server
    print("\nStarting ADK web server with MCP fileserver enabled...")
    import subprocess
    
    # Apply nest_asyncio at the start
    import nest_asyncio
    nest_asyncio.apply()
    
    # Run the ADK web command
    cmd = ["adk", "web"]
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())