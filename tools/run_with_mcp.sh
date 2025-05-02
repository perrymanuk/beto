#!/bin/bash

# Script to run the ADK web server with MCP fileserver enabled
# This sets up the right environment variables and makes sure nest_asyncio is installed

echo "Setting up MCP Fileserver for ADK Web..."

# Verify virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "Virtual environment is not activated."
  echo "Please run: source .venv/bin/activate"
  exit 1
fi

# Set MCP Fileserver root directory if not already set
if [[ -z "$MCP_FS_ROOT_DIR" ]]; then
  # Default to the current project directory
  export MCP_FS_ROOT_DIR="$(pwd)"
  echo "Setting MCP_FS_ROOT_DIR to current directory: $MCP_FS_ROOT_DIR"
fi

# Ensure nest_asyncio is installed
python -c "import nest_asyncio" 2>/dev/null
if [[ $? -ne 0 ]]; then
  echo "Installing nest_asyncio (required for MCP fileserver)..."
  pip install nest_asyncio
fi

echo "MCP Fileserver Configuration:"
echo "  Root Directory: $MCP_FS_ROOT_DIR"
echo "  Allow Write: ${MCP_FS_ALLOW_WRITE:-false}"
echo "  Allow Delete: ${MCP_FS_ALLOW_DELETE:-false}"

# Start the ADK web server
echo -e "\nStarting ADK web server with MCP fileserver enabled..."
exec adk web "$@"