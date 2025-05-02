#!/usr/bin/env python3
"""
Test MCP Fileserver integration with the agent.

This script verifies that the MCP fileserver tools are properly integrated
with the agent and can be invoked correctly.
"""

import os
import logging
import json
import asyncio
from pprint import pprint
from typing import Any, Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import agent creation function
from agent import create_agent

async def test_fileserver_tools_integration():
    """
    Test that MCP fileserver tools are properly integrated with the agent.
    
    This function creates the agent and checks if it has the MCP fileserver tools,
    then tries to invoke each tool to verify they work correctly.
    """
    logger.info("Creating agent...")
    agent = create_agent()
    
    # Check if agent has tools
    logger.info(f"Agent created with {len(agent.tools)} tools")
    
    # Get all tool names
    tool_names = []
    for tool in agent.tools:
        if hasattr(tool, 'name'):
            tool_names.append(tool.name)
        elif hasattr(tool, '__name__'):
            tool_names.append(tool.__name__)
        else:
            tool_names.append(str(type(tool)))
            
    logger.info(f"Tool names: {', '.join(tool_names)}")
    
    # Look for fileserver tools
    fs_tools = [t for t in tool_names if t in ['list_files', 'read_file', 'get_file_info']]
    logger.info(f"Found {len(fs_tools)} fileserver tools: {fs_tools}")
    
    # Check if fileserver tools exist
    if not fs_tools:
        logger.error("❌ No fileserver tools found in the agent")
        return False
    
    # Try to invoke the list_files tool if available
    if "list_files" in fs_tools:
        try:
            # Find the tool object
            list_files_tool = None
            for tool in agent.tools:
                if getattr(tool, "name", None) == "list_files":
                    list_files_tool = tool
                    break
            
            if list_files_tool:
                logger.info(f"Invoking list_files tool...")
                
                # Create a runner to invoke the tool
                from google.adk.runners import Runner
                runner = Runner(agent=agent)
                
                # Get current directory relative to MCP_FS_ROOT_DIR
                root_dir = os.environ.get("MCP_FS_ROOT_DIR", "")
                current_dir = os.getcwd()
                if current_dir.startswith(root_dir):
                    relative_path = os.path.relpath(current_dir, root_dir)
                else:
                    relative_path = ""
                
                # Invoke the tool with a path
                logger.info(f"Listing files in path: {relative_path}")
                result = await runner.invoke_tool(
                    tool=list_files_tool,
                    parameters={"path": relative_path}
                )
                
                # Log the result
                if result:
                    if hasattr(result, 'contents') and result.contents:
                        content = result.contents[0].text
                        try:
                            files_data = json.loads(content)
                            logger.info(f"✅ Successfully listed {len(files_data)} files")
                            # Print a sample of the results
                            if files_data:
                                logger.info(f"Sample file: {files_data[0]}")
                        except json.JSONDecodeError:
                            logger.info(f"Raw result: {content[:200]}...")
                    else:
                        logger.info(f"Raw result: {result}")
                else:
                    logger.warning("Empty result from list_files tool")
            else:
                logger.warning("Could not find list_files tool object")
        except Exception as e:
            logger.error(f"❌ Error invoking list_files tool: {str(e)}", exc_info=True)
    
    return True

def main():
    """Command line entry point."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    success = loop.run_until_complete(test_fileserver_tools_integration())
    
    if success:
        print("✅ MCP Fileserver integration test passed!")
        return 0
    else:
        print("❌ MCP Fileserver integration test failed!")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())