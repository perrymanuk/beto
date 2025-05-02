#!/bin/bash

# This is a wrapper script to run the ADK web UI with MCP environment variables explicitly set

# Set the root directory for MCP filesystem access
if [ -z "$MCP_FS_ROOT_DIR" ]; then
  export MCP_FS_ROOT_DIR="/Users/perry.manuk/git"
  echo "Setting MCP_FS_ROOT_DIR=${MCP_FS_ROOT_DIR}"
else
  echo "Using existing MCP_FS_ROOT_DIR=${MCP_FS_ROOT_DIR}"
fi

# Optional write/delete permissions (default to false)
export MCP_FS_ALLOW_WRITE="false"
export MCP_FS_ALLOW_DELETE="false"

# Set additional environment variables to help with debugging
export LOG_LEVEL=DEBUG
export PYTHONUNBUFFERED=1  # Make sure Python output is not buffered

# Run ADK web with all environment variables explicitly set
echo "Starting ADK web with MCP environment variables set..."
exec adk web