"""
Test the dual agent fix for streaming vs non-streaming models.
This script verifies that our implementation properly prevents streaming-only
models from being used with the text chat endpoint, which requires generateContent API.
"""
import os
import sys
import logging
import pprint

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import needed components
from google.genai.types import Content, Part
from google.adk.agents import Agent
from radbot.web.api.session import SessionRunner

def test_session_model_override():
    """Test that the session.py model override mechanism works correctly."""
    logger.info("=== TESTING SESSION MODEL OVERRIDE ===")
    
    # Create a user ID and session ID
    user_id = "test_user_1"
    session_id = "test_session_1"
    
    # Create a new SessionRunner
    logger.info(f"Creating new SessionRunner with user_id={user_id}, session_id={session_id}")
    runner = SessionRunner(user_id=user_id, session_id=session_id)
    
    # Check the initial model of the agent_instance
    logger.info(f"Initial agent model: {runner.agent_instance.model}")
    
    # Simulate a streaming model by manually overriding it
    logger.info("Simulating a streaming model by manually setting agent_instance.model")
    streaming_model = "gemini-2.0-flash-live-preview-04-09"  # Known streaming-only model
    runner.agent_instance.model = streaming_model
    logger.info(f"Modified agent model to streaming model: {runner.agent_instance.model}")
    
    # Process a test message to trigger the model override
    logger.info("Processing a test message to trigger model override...")
    response = runner.process_message("Hello, this is a test message.")
    
    # Check the model after processing
    logger.info(f"Agent model after processing: {runner.agent_instance.model}")
    logger.info(f"Runner agent model after processing: {runner.runner.agent.model}")
    
    # Check if the response is valid
    logger.info(f"Response received: {response['response'][:100]}...")
    logger.info(f"Number of events: {len(response['events'])}")
    
    # Print event summaries
    logger.info("Event summaries:")
    for event in response['events']:
        logger.info(f"  - {event.get('type')} | {event.get('summary', 'N/A')}")
    
    # Check if the model was properly overridden
    if "gemini-2.0-flash-live" in runner.agent_instance.model:
        logger.error("TEST FAILED: Streaming model was not properly overridden!")
        return False
    
    # If we got here, the test passed
    logger.info("TEST PASSED: Session runner properly overrode the streaming model with a text-compatible model.")
    return True

if __name__ == "__main__":
    logger.info("Starting dual agent fix test...")
    test_result = test_session_model_override()
    logger.info(f"Test result: {'PASS' if test_result else 'FAIL'}")