#!/usr/bin/env python
"""
Example script for running the voice server.

This script creates a voice-enabled agent and runs a voice server that
integrates with the ADK web interface.
"""

import argparse
import asyncio
import logging
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("voice_server_example")

def main():
    """Run the voice server with a voice-enabled agent."""
    parser = argparse.ArgumentParser(description="Run the voice server")
    parser.add_argument("--host", default=None, help="Host to bind the server to")
    parser.add_argument("--port", type=int, default=None, help="Port to bind the server to")
    args = parser.parse_args()
    
    logger.info("Creating voice-enabled agent")
    
    # Import radbot components
    from radbot.voice import create_voice_enabled_agent, run_voice_app
    from radbot.tools.basic_tools import get_current_time, get_weather
    
    try:
        from radbot.tools.web_search_tools import create_tavily_search_tool
        web_search_available = True
    except ImportError:
        web_search_available = False
    
    # Create tools for the agent
    tools = [get_current_time, get_weather]
    
    # Try to add the web search tool if available
    if web_search_available:
        try:
            web_search_tool = create_tavily_search_tool()
            if web_search_tool:
                tools.append(web_search_tool)
                logger.info("Added web search tool to voice agent")
        except Exception as e:
            logger.warning(f"Failed to create web search tool: {e}")
    
    # Create the agent
    agent = create_voice_enabled_agent(tools=tools)
    
    # Test the ElevenLabs connection
    logger.info("Testing ElevenLabs connection")
    try:
        from radbot.voice.elevenlabs_client import test_elevenlabs_connection
        import asyncio
        
        # Run the test
        result = asyncio.run(test_elevenlabs_connection())
        
        if result:
            logger.info("ElevenLabs connection successful")
        else:
            logger.warning(
                "ElevenLabs connection failed. "
                "Voice server will run in text-only mode."
            )
    except Exception as e:
        logger.warning(f"Error testing ElevenLabs connection: {e}")
    
    # Get host and port from environment if not provided
    host = args.host or os.environ.get("VOICE_SERVER_HOST", "localhost")
    port = args.port
    if not port:
        port_str = os.environ.get("VOICE_SERVER_PORT", "8000")
        try:
            port = int(port_str)
        except ValueError:
            logger.warning(f"Invalid port {port_str}, using default 8000")
            port = 8000
    
    # Run the server
    logger.info(f"Starting voice server on {host}:{port}")
    run_voice_app(agent, host=host, port=port)

if __name__ == "__main__":
    main()
