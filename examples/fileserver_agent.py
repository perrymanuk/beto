#!/usr/bin/env python3
"""
Fileserver Agent Example

This example demonstrates using an ADK agent with filesystem access.
Previously this used the MCP fileserver - now it uses direct filesystem
implementation for better performance and reliability.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Optional

# Add the parent directory to the path so we can import radbot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.tools.function_tool import FunctionTool
from google.adk.tools.load_web_page import load_web_page

# Import direct filesystem implementation
from radbot.filesystem.adapter import create_fileserver_toolset

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Basic tool: get current time
def get_current_time() -> str:
    """Get the current time."""
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def setup_agent():
    """
    Set up the agent with tools and services.
    
    Returns:
        Agent ready to use
    """
    # Basic tools
    basic_tools = [
        FunctionTool(get_current_time),
        FunctionTool(load_web_page),
    ]
    
    # Direct filesystem tools using the compatibility adapter
    fs_tools = create_fileserver_toolset()
    
    # Combine tools
    all_tools = basic_tools
    if fs_tools:
        all_tools.extend(fs_tools)
        logger.info(f"Added {len(fs_tools)} filesystem tools")
    else:
        logger.warning("Filesystem tools not available")
    
    # Get filesystem configuration
    from radbot.filesystem.adapter import get_filesystem_config
    root_dir, allow_write, allow_delete = get_filesystem_config()
    
    # Create the agent
    agent = LlmAgent(
        model='gemini-1.5-pro',  # Update model name if needed
        name='filesystem_assistant',
        instruction=f"""
        You are a helpful assistant with access to filesystem operations.
        
        Filesystem Permissions:
        - Root directory: {root_dir}
        - Write operations: {'Enabled' if allow_write else 'Disabled'}
        - Delete operations: {'Enabled' if allow_delete else 'Disabled'}
        
        You can help users with file management tasks like listing directories,
        reading files, and searching for files. If write operations are enabled,
        you can also help with creating, editing, and copying files.
        
        Always be cautious when performing operations that modify the filesystem,
        and make sure to confirm important actions with the user first.
        """,
        tools=all_tools,
    )
    
    return agent

def main():
    """Main function to run the agent in a loop."""
    # Set up the agent
    agent = setup_agent()
    
    # Create services for the runner
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    
    # Create the runner
    runner = Runner(
        agent=agent,
        app_name='filesystem_assistant',
        session_service=session_service,
        artifact_service=artifact_service,
    )
    
    # Get configuration for display
    from radbot.filesystem.adapter import get_filesystem_config
    root_dir, allow_write, allow_delete = get_filesystem_config()
    
    # Print welcome message
    print("\nFileserver Agent\n")
    print(f"Root directory: {root_dir}")
    print(f"Write operations: {'Enabled' if allow_write else 'Disabled'}")
    print(f"Delete operations: {'Enabled' if allow_delete else 'Disabled'}\n")
    print("Type 'exit' or 'quit' to end the session.\n")
    
    # Create a session
    session_id = runner.create_session()
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("You: ")
            if user_input.lower() in ['exit', 'quit']:
                print("\nGoodbye!")
                break
            
            # Process the message
            response = runner.process_message(session_id, user_input)
            print(f"\nAgent: {response.text}\n")
            
        except KeyboardInterrupt:
            print("\n\nExiting due to keyboard interrupt.")
            break
        except Exception as e:
            logger.exception(f"Error processing message: {e}")
            print(f"\nError: {e}\n")

if __name__ == "__main__":
    main()
