#!/usr/bin/env python3
"""
Test MCP Fileserver

This script tests the MCP fileserver functionality by creating a temporary directory,
starting the MCP fileserver server, and performing various filesystem operations.
"""

import os
import sys
import tempfile
import shutil
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

# Import our MCP fileserver modules
from radbot.tools.mcp_fileserver_server import start_server
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_fileserver_operations():
    """
    Test various filesystem operations using the MCP fileserver.
    """
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    logger.info(f"Created temporary directory: {temp_dir}")
    
    try:
        # Create some test files
        test_file1 = os.path.join(temp_dir, "test1.txt")
        test_file2 = os.path.join(temp_dir, "test2.txt")
        test_subdir = os.path.join(temp_dir, "subdir")
        
        # Create the files
        with open(test_file1, "w") as f:
            f.write("This is test file 1")
        with open(test_file2, "w") as f:
            f.write("This is test file 2")
        
        # Create the subdirectory
        os.makedirs(test_subdir)
        
        # Create environment variables
        os.environ["MCP_FS_ROOT_DIR"] = temp_dir
        os.environ["MCP_FS_ALLOW_WRITE"] = "true"
        os.environ["MCP_FS_ALLOW_DELETE"] = "true"
        
        # Create the MCPToolset
        logger.info("Creating MCP fileserver toolset...")
        tools, exit_stack = await create_fileserver_toolset_async()
        
        if not tools or not exit_stack:
            logger.error("Failed to create MCP fileserver toolset")
            return
        
        # Log the available tools
        logger.info(f"Available tools: {[tool.name for tool in tools]}")
        
        # Test list_files
        logger.info("\nTesting list_files...")
        list_files_tool = next((tool for tool in tools if tool.name == "list_files"), None)
        if list_files_tool:
            result = await list_files_tool.run_async(args={"path": ""}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"list_files result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing list_files result: {str(e)}")
        else:
            logger.error("list_files tool not found")
        
        # Test read_file
        logger.info("\nTesting read_file...")
        read_file_tool = next((tool for tool in tools if tool.name == "read_file"), None)
        if read_file_tool:
            result = await read_file_tool.run_async(args={"path": "test1.txt"}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"read_file result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing read_file result: {str(e)}")
        else:
            logger.error("read_file tool not found")
        
        # Test write_file
        logger.info("\nTesting write_file...")
        write_file_tool = next((tool for tool in tools if tool.name == "write_file"), None)
        if write_file_tool:
            result = await write_file_tool.run_async(
                args={
                    "path": "test3.txt",
                    "content": "This is test file 3"
                },
                tool_context=None
            )
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"write_file result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing write_file result: {str(e)}")
        else:
            logger.error("write_file tool not found")
        
        # Test get_file_info
        logger.info("\nTesting get_file_info...")
        get_file_info_tool = next((tool for tool in tools if tool.name == "get_file_info"), None)
        if get_file_info_tool:
            result = await get_file_info_tool.run_async(args={"path": "test1.txt"}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"get_file_info result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing get_file_info result: {str(e)}")
        else:
            logger.error("get_file_info tool not found")
        
        # Test copy_file
        logger.info("\nTesting copy_file...")
        copy_file_tool = next((tool for tool in tools if tool.name == "copy_file"), None)
        if copy_file_tool:
            result = await copy_file_tool.run_async(
                args={
                    "source": "test1.txt",
                    "destination": "subdir/test1_copy.txt"
                },
                tool_context=None
            )
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"copy_file result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing copy_file result: {str(e)}")
        else:
            logger.error("copy_file tool not found")
        
        # Test move_file
        logger.info("\nTesting move_file...")
        move_file_tool = next((tool for tool in tools if tool.name == "move_file"), None)
        if move_file_tool:
            result = await move_file_tool.run_async(
                args={
                    "source": "test2.txt",
                    "destination": "test2_renamed.txt"
                },
                tool_context=None
            )
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"move_file result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing move_file result: {str(e)}")
        else:
            logger.error("move_file tool not found")
        
        # Test list_files again to see changes
        logger.info("\nTesting list_files after changes...")
        if list_files_tool:
            result = await list_files_tool.run_async(args={"path": ""}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"list_files result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing list_files result: {str(e)}")
            
            # List subdirectory
            result = await list_files_tool.run_async(args={"path": "subdir"}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"list_files subdir result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing list_files subdir result: {str(e)}")
        
        # Test delete_file
        logger.info("\nTesting delete_file...")
        delete_file_tool = next((tool for tool in tools if tool.name == "delete_file"), None)
        if delete_file_tool:
            result = await delete_file_tool.run_async(args={"path": "test3.txt"}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"delete_file result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing delete_file result: {str(e)}")
        else:
            logger.error("delete_file tool not found")
        
        # Test list_files again after deletion
        logger.info("\nTesting list_files after deletion...")
        if list_files_tool:
            result = await list_files_tool.run_async(args={"path": ""}, tool_context=None)
            try:
                if hasattr(result, 'contents') and result.contents:
                    result_str = result.contents[0].text
                else:
                    result_str = str(result)
                logger.info(f"list_files result: {result_str}")
            except Exception as e:
                logger.error(f"Error processing list_files result: {str(e)}")
        
        # Close the exit stack
        logger.info("\nClosing MCP fileserver connection...")
        await exit_stack.aclose()
        logger.info("MCP fileserver connection closed")
        
    except Exception as e:
        logger.error(f"Error during test: {str(e)}")
    finally:
        # Clean up the temporary directory
        logger.info(f"Cleaning up temporary directory: {temp_dir}")
        shutil.rmtree(temp_dir)

def main():
    """Command line entry point."""
    print("=" * 60)
    print(" MCP Fileserver Test ".center(60, "="))
    print("=" * 60)
    
    try:
        # Run the test
        asyncio.run(test_fileserver_operations())
        print("\n✅ Test completed")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
