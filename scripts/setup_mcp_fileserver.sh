#!/bin/bash
# Script to set up the MCP filesystem server

echo "Installing MCP filesystem server..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "npm is not installed. Please install Node.js and npm first."
    echo "You can download from: https://nodejs.org/"
    exit 1
fi

# Try different installation approaches in order of preference
echo "Attempting direct installation from npm..."
npm install -g @modelcontextprotocol/server-filesystem

# Verify installation
if npx @modelcontextprotocol/server-filesystem --help &> /dev/null; then
    echo "MCP filesystem server installed successfully!"
    echo "Usage: npx @modelcontextprotocol/server-filesystem [--allow-write] [--allow-delete] <root_dir>"
    exit 0
fi

echo "Direct npm installation failed, trying alternate approach..."

# Alternative: Install directly from GitHub
echo "Installing from GitHub repository..."
npm install -g modelcontextprotocol/servers#main:src/filesystem

# Verify installation again
if npx mcp-server-filesystem --help &> /dev/null; then
    echo "MCP filesystem server installed successfully from GitHub!"
    echo "Usage: npx mcp-server-filesystem [--allow-write] [--allow-delete] <root_dir>"
    exit 0
fi

# If we got here, both approaches failed
echo "Installation failed through standard methods."
echo "Let's try installing from the raw GitHub files..."

# Clone the repository temporarily
TEMP_DIR=$(mktemp -d)
echo "Created temporary directory: $TEMP_DIR"
git clone https://github.com/modelcontextprotocol/servers.git "$TEMP_DIR/servers"
cd "$TEMP_DIR/servers/src/filesystem"

# Install and build locally
echo "Building from source..."
npm install
npm run build

# Install globally from local build
npm install -g .
cd -

# Clean up
rm -rf "$TEMP_DIR"

# Final verification
if command -v mcp-server-filesystem &> /dev/null || npx mcp-server-filesystem --help &> /dev/null; then
    echo "MCP filesystem server built and installed successfully from source!"
    exit 0
else
    echo "All installation attempts failed."
    echo ""
    echo "You may need to try manual installation:"
    echo "1. git clone https://github.com/modelcontextprotocol/servers.git"
    echo "2. cd servers/src/filesystem"
    echo "3. npm install"
    echo "4. npm run build"
    echo "5. npm install -g ."
    exit 1
fi
