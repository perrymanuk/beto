#!/usr/bin/env python3
"""
Test script for Claude CLI MCP Integration.

This script verifies that the Claude CLI MCP server configuration is valid
and tests executing a simple command through this integration.
"""

import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import required modules
from radbot.config.config_loader import config_loader
from radbot.tools.mcp.mcp_client_factory import MCPClientFactory
from radbot.tools.shell.shell_tool import execute_command_with_claude

def test_config_loading():
    """Test that the configuration loads correctly with Claude CLI MCP server."""
    try:
        # Get the MCP server configuration
        server_config = config_loader.get_mcp_server("claude-cli")
        
        if server_config:
            logger.info("✅ Config loaded successfully!")
            logger.info(f"Claude CLI MCP server config: {server_config}")
            return True
        else:
            logger.error("❌ Claude CLI MCP server not found in configuration!")
            return False
    except Exception as e:
        logger.exception(f"Error loading configuration: {e}")
        return False

def test_client_creation():
    """Test creating a Claude CLI MCP client."""
    try:
        # Get the client
        client = MCPClientFactory.get_client("claude-cli")
        
        if client:
            logger.info("✅ Client created successfully!")
            return True
        else:
            logger.error("❌ Failed to create Claude CLI MCP client!")
            return False
    except Exception as e:
        logger.exception(f"Error creating client: {e}")
        return False

def test_command_execution():
    """Test executing a simple command via Claude CLI."""
    try:
        # Execute a simple echo command
        result = execute_command_with_claude("echo 'Hello from Claude CLI MCP!'")
        
        if result and result.get("return_code", -1) == 0:
            logger.info("✅ Command executed successfully!")
            logger.info(f"Output: {result.get('stdout', '').strip()}")
            return True
        else:
            logger.error("❌ Command execution failed!")
            logger.error(f"Error: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        logger.exception(f"Error executing command: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("Testing Claude CLI MCP Integration")
    
    tests = [
        ("Config Loading", test_config_loading),
        ("Client Creation", test_client_creation),
        ("Command Execution", test_command_execution)
    ]
    
    results = []
    
    # Run each test
    for name, test_func in tests:
        logger.info(f"\n=== Testing: {name} ===")
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            logger.exception(f"Test failed with exception: {e}")
            results.append((name, False))
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    all_passed = True
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{status}: {name}")
        all_passed = all_passed and result
    
    # Clean up
    try:
        MCPClientFactory.clear_cache()
    except:
        pass
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())