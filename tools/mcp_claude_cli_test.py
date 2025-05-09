#!/usr/bin/env python3
"""
Test script for interacting with Claude CLI as an MCP server.

This script uses the MCP Python SDK to connect to Claude CLI
and list available tools or run commands.
"""

import os
import sys
import asyncio
import json
import logging
import argparse
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import MCP SDK
try:
    from mcp import ClientSession, StdioServerParameters, types
    from mcp.client.stdio import stdio_client
except ImportError:
    logger.error("MCP Python SDK not installed. Please install with: uv pip install mcp")
    sys.exit(1)

async def run_mcp_test(args):
    """
    Run the MCP test with Claude CLI.
    
    Args:
        args: Command line arguments
    """
    # Get Claude CLI command from config
    from radbot.config.config_loader import config_loader
    
    claude_config = None
    mcp_servers = config_loader.get_enabled_mcp_servers()
    for server in mcp_servers:
        if server.get("id") == "claude-cli":
            claude_config = server
            break
    
    if not claude_config:
        logger.error("Claude CLI configuration not found in config.yaml")
        return
    
    # Get command and arguments
    claude_command = claude_config.get("command", "claude")
    claude_args = claude_config.get("args", ["mcp", "serve"])
    working_dir = claude_config.get("working_directory", os.getcwd())
    
    # Create server parameters
    server_params = StdioServerParameters(
        command=claude_command,
        args=claude_args,
        env=os.environ.copy(),
        working_directory=working_dir
    )
    
    logger.info(f"Connecting to Claude CLI MCP server: {claude_command} {' '.join(claude_args)}")
    
    # Try to connect to the MCP server
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize(
                    capabilities={
                        "completions": False,
                        "prompts": False,
                        "resources": False,
                        "tools": True
                    },
                    client_info={
                        "name": "RadbotMCPTestClient",
                        "version": "1.0.0"
                    }
                )
                logger.info("Successfully initialized Claude CLI MCP session")
                
                # List available tools
                if args.list_tools:
                    logger.info("Listing available tools...")
                    tools_result = await session.list_tools()
                    
                    if hasattr(tools_result, 'tools'):
                        tools = tools_result.tools
                        print(f"\n=== {len(tools)} AVAILABLE TOOLS ===")
                        for tool in tools:
                            print(f"{tool.name}: {tool.description}")
                    else:
                        print("No tools found or unexpected response format")
                
                # Execute a command
                if args.command:
                    logger.info(f"Executing command: {args.command}")
                    result = await session.call_tool(
                        "Bash",
                        {"command": args.command}
                    )
                    
                    if hasattr(result, 'outputs') and result.outputs:
                        print("\n=== COMMAND OUTPUT ===")
                        if hasattr(result.outputs, 'stdout'):
                            print(result.outputs.stdout)
                        elif hasattr(result.outputs, 'content'):
                            # Try to parse the content
                            try:
                                content = json.loads(result.outputs.content)
                                print(f"STDOUT: {content.get('stdout', '')}")
                                if content.get('stderr'):
                                    print(f"STDERR: {content.get('stderr', '')}")
                                print(f"EXIT CODE: {content.get('exitCode', 0)}")
                            except:
                                print(result.outputs.content)
                        else:
                            print(str(result.outputs))
                    else:
                        print("No output from command or unexpected response format")
    
    except Exception as e:
        logger.error(f"Error connecting to Claude CLI MCP server: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Claude CLI MCP Test")
    parser.add_argument("--list-tools", action="store_true", help="List available tools")
    parser.add_argument("--command", type=str, help="Command to execute")
    
    args = parser.parse_args()
    
    if not args.list_tools and not args.command:
        parser.print_help()
        return 1
    
    asyncio.run(run_mcp_test(args))
    return 0

if __name__ == "__main__":
    sys.exit(main())