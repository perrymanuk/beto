"""
Test script for the ADK built-in code execution tool.

This script creates a standalone agent that uses the built-in code execution tool
and tests it with a simple factorial calculation.

To test: python -m examples.code_execution_test
"""

import asyncio
import logging
import os
import sys
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Make sure radbot is in the path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Make sure code execution is enabled
os.environ["RADBOT_ENABLE_ADK_CODE_EXEC"] = "true"
os.environ["RADBOT_FORCE_CODE_EXEC"] = "true"

# Import ADK components
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig, Tool

# Handle different import paths for ToolCodeExecution
try:
    # Try to import from types directly (newer versions)
    from google.genai.types import ToolCodeExecution
except ImportError:
    try:
        # Try to import from separate types classes (older versions)
        from google.genai.types.tool_types import ToolCodeExecution
    except ImportError:
        # Define a minimal wrapper if not available
        class ToolCodeExecution:
            def __init__(self):
                pass

# Constants
USER_ID = "test_user"
SESSION_ID = "test_session"
# Use your desired model
MODEL_NAME = os.environ.get("RADBOT_MAIN_MODEL", "gemini-2.5-pro-preview-05-06")

def main():
    """Run the code execution test."""
    logger.info(f"Creating code execution test agent with model {MODEL_NAME}")
    
    # Import our proper code execution agent from the tools module
    from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent
    
    # Create the agent using our standard factory function, disabling transfer_tool for standalone tests
    code_agent = create_code_execution_agent(
        name="code_execution_agent",
        model=MODEL_NAME,
        instruction_name="code_execution_agent",  # Will load from config if exists
        include_transfer_tool=False  # Disable transfer tool for standalone tests
    )
    
    logger.info(f"Created agent without transfer_to_agent tool for standalone testing")
    
    # Log the agent details
    logger.info(f"Created code execution agent with name '{code_agent.name}' using model '{code_agent.model}'")
    
    # Log the tools available
    tool_names = [getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool)) for tool in code_agent.tools]
    logger.info(f"Agent has {len(code_agent.tools)} tools: {', '.join(tool_names)}")
    
    # Create session service and runner
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=code_agent.name,  # Use agent name as app_name for ADK 0.4.0+
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    runner = Runner(
        agent=code_agent,
        app_name=code_agent.name,  # Use agent name as app_name for ADK 0.4.0+
        session_service=session_service
    )
    
    # Test query
    test_query = "Calculate the factorial of 5 using Python."
    
    # Create user message
    user_message = Content(
        parts=[Part(text=test_query)],
        role="user"
    )
    
    # Run the agent
    logger.info(f"Running test query: {test_query}")
    events = list(runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=user_message
    ))
    
    # Extract and print response
    logger.info(f"Received {len(events)} events")
    final_response = None
    for event in events:
        if hasattr(event, 'is_final_response') and event.is_final_response():
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response = part.text
                            break
    
    if final_response:
        print("\n--- AGENT RESPONSE ---")
        print(final_response)
        print("---------------------\n")
    else:
        print("\nNo response found in events\n")

if __name__ == "__main__":
    main()
