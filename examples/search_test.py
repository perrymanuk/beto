"""
Test script for the ADK built-in Google Search tool.

This script creates a standalone agent that uses the built-in Google Search tool
and tests it with a simple search query.
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
from google.genai.types import Content, Part, GenerateContentConfig, Tool, ToolGoogleSearch

# Constants
AGENT_NAME = "search_test"
APP_NAME = "search_test"
USER_ID = "test_user"
SESSION_ID = "test_session"
# Use your desired model
MODEL_NAME = os.environ.get("RADBOT_MAIN_MODEL", "gemini-2.5-pro-preview-05-06")

def main():
    """Run the Google Search test."""
    logger.info(f"Creating Google Search test agent with model {MODEL_NAME}")
    
    # Create a simple agent with Google Search configured directly
    agent = Agent(
        name=AGENT_NAME,
        model=MODEL_NAME,
        instruction="""
        You are a search agent. When asked about current events, news, or any information 
        that may have changed since your training, use Google Search to find the most 
        up-to-date information.
        
        Always cite your sources and provide accurate information based on search results.
        """,
        description="An agent that can search the web using Google Search."
    )
    
    # Configure Google Search explicitly
    agent.config = GenerateContentConfig()
    agent.config.tools = [Tool(google_search=ToolGoogleSearch())]
    logger.info("Configured Google Search explicitly")
    
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
    
    # Test query - use something that would require current information
    test_query = "What is the current weather in New York City?"
    
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
