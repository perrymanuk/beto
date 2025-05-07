"""
Test script for the ADK built-in code execution tool.

This script creates a standalone agent that uses the built-in code execution tool
and tests it with a simple factorial calculation.
"""

import asyncio
import logging
import os
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import ADK components
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part, GenerateContentConfig, Tool, ToolCodeExecution

# Constants
AGENT_NAME = "code_execution_test"
APP_NAME = "code_execution_test"
USER_ID = "test_user"
SESSION_ID = "test_session"
# Use your desired model
MODEL_NAME = os.environ.get("RADBOT_MAIN_MODEL", "gemini-2.5-pro-preview-05-06")

def main():
    """Run the code execution test."""
    logger.info(f"Creating code execution test agent with model {MODEL_NAME}")
    
    # Create a simple agent with code execution configured directly
    agent = Agent(
        name=AGENT_NAME,
        model=MODEL_NAME,
        instruction="""
        You are a code execution agent. When asked to calculate something, write and execute
        Python code to perform the calculation. 
        
        For example, if asked to calculate a factorial, you should:
        1. Write the Python code to calculate the factorial
        2. Execute the code using the built-in code execution capability
        3. Return the result along with an explanation
        
        Always explain your code and the results.
        """,
        description="An agent that can execute Python code."
    )
    
    # Configure code execution explicitly
    agent.config = GenerateContentConfig()
    agent.config.tools = [Tool(code_execution=ToolCodeExecution())]
    logger.info("Configured code execution explicitly")
    
    # Create session service and runner
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    
    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
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
