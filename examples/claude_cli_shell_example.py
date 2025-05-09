#!/usr/bin/env python3
"""
Claude CLI MCP Integration Example

This example demonstrates how to execute shell commands using Claude CLI's MCP server.
"""

import logging
import sys
import os
import time

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Radbot modules
from radbot.tools.mcp.mcp_client_factory import MCPClientFactory
from radbot.tools.shell.shell_tool import get_shell_tool, execute_command_with_claude
from radbot.config.config_loader import config_loader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main example function.
    """
    logger.info("Claude CLI MCP Integration Example")
    
    # Check if Claude CLI MCP server is configured
    server_config = config_loader.get_mcp_server("claude-cli")
    if not server_config:
        logger.error("Claude CLI MCP server not configured. Please add it to your config.yaml.")
        return 1
        
    logger.info(f"Using Claude CLI MCP server config: {server_config}")
    
    logger.info("Claude CLI MCP server configured. Testing connection...")
    
    try:
        # Get the Claude CLI MCP client
        client = MCPClientFactory.get_client("claude-cli")
        if not client:
            logger.error("Failed to create Claude CLI MCP client")
            return 1
            
        # Verify the client is initialized
        if not getattr(client, "initialized", False):
            logger.warning("Client not initialized. Initializing...")
            if not client.initialize():
                logger.error("Failed to initialize client")
                return 1
        
        logger.info("Client initialized successfully")
        
        # Test connection with a simple echo command
        logger.info("Testing shell command execution with Claude CLI...")
        result = execute_command_with_claude("echo 'Hello from Claude CLI!'")
        
        if result.get("return_code", -1) == 0:
            logger.info(f"Command executed successfully: {result.get('stdout', '').strip()}")
        else:
            logger.error(f"Command execution failed: {result.get('stderr', '')}")
            return 1
        
        # Get available tools
        logger.info("\nAvailable tools from Claude CLI MCP server:")
        for tool in client.get_tools():
            tool_name = getattr(tool, 'name', str(tool))
            logger.info(f"- {tool_name}")
        
        # Create and use shell tool
        logger.info("\nCreating shell tool with Claude CLI backend...")
        shell_tool = get_shell_tool(strict_mode=True, use_claude_cli=True)
        
        # Execute commands via the shell tool
        logger.info("\nExecuting commands via shell tool...")
        
        commands = [
            "pwd",
            "ls -la",
            "echo 'Current time:' && date",
            "python --version"
        ]
        
        for cmd in commands:
            logger.info(f"\nExecuting: {cmd}")
            
            # Parse command and arguments
            parts = cmd.split()
            command = parts[0]
            arguments = parts[1:] if len(parts) > 1 else []
            
            # Call the tool
            result = shell_tool(command=command, arguments=arguments, timeout=30)
            
            # Display result
            if result.get("return_code", -1) == 0:
                logger.info(f"Success! Output:\n{result.get('stdout', '').strip()}")
            else:
                logger.error(f"Failed! Error:\n{result.get('stderr', '')}")
        
        logger.info("\nExample completed successfully!")
        return 0
        
    except Exception as e:
        logger.exception(f"Error in example: {e}")
        return 1
    finally:
        # Clean up
        MCPClientFactory.clear_cache()
        logger.info("Cleaned up resources")

if __name__ == "__main__":
    sys.exit(main())