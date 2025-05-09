#!/usr/bin/env python3
"""
Test script for Claude CLI MCP integration with web interface.

This script tests the Claude CLI MCP integration by running the web server
and checking if the Claude CLI tools are properly attached to the agent.
"""

import os
import sys
import logging
import time
import subprocess
import requests
import json
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants
WEB_SERVER_URL = "http://localhost:8000"
SESSION_ID = "test-claude-cli-session"

def test_claude_cli_connection():
    """Test the Claude CLI MCP connection."""
    try:
        # Import the test function from claude_cli module
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from radbot.tools.mcp.claude_cli import test_claude_cli_connection
        
        # Run the test
        logger.info("Testing Claude CLI MCP connection...")
        result = test_claude_cli_connection()
        
        if result.get("success", False):
            logger.info(f"Connection successful: {result.get('output', '')}")
            return True
        else:
            logger.error(f"Connection failed: {result.get('error', 'Unknown error')}")
            return False
            
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error testing Claude CLI connection: {e}")
        return False

def start_web_server():
    """Start the web server in a separate process."""
    try:
        logger.info("Starting web server...")
        
        # Start the server
        process = subprocess.Popen(
            ["python", "-m", "radbot.web"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        # Wait for server to start
        for _ in range(30):
            try:
                response = requests.get(f"{WEB_SERVER_URL}/api/health")
                if response.status_code == 200:
                    logger.info("Web server started successfully")
                    return process
            except requests.exceptions.ConnectionError:
                time.sleep(1)
                
        logger.error("Failed to start web server")
        process.terminate()
        return None
        
    except Exception as e:
        logger.error(f"Error starting web server: {e}")
        return None

def test_web_api_session():
    """Test creating a session via the web API."""
    try:
        # Create a session
        logger.info(f"Creating session with ID: {SESSION_ID}")
        response = requests.post(
            f"{WEB_SERVER_URL}/api/sessions",
            json={"session_id": SESSION_ID}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to create session: {response.text}")
            return False
            
        # Send a test message to check if Claude CLI tools are available
        test_message = "List all tools you have available, especially any Claude CLI tools"
        logger.info(f"Sending test message: {test_message}")
        
        response = requests.post(
            f"{WEB_SERVER_URL}/api/sessions/{SESSION_ID}/messages",
            json={"message": test_message}
        )
        
        if response.status_code != 200:
            logger.error(f"Failed to send message: {response.text}")
            return False
            
        # Get the response
        result = response.json()
        logger.info(f"Response: {result.get('response', '')[:500]}...")
        
        # Check if Claude CLI tools are mentioned in the response
        if "claude_" in result.get("response", "").lower():
            logger.info("Claude CLI tools are mentioned in the response")
            return True
        else:
            logger.warning("Claude CLI tools not found in the response")
            return False
            
    except Exception as e:
        logger.error(f"Error testing web API: {e}")
        return False

def main():
    """Main test function."""
    # Test Claude CLI connection
    if not test_claude_cli_connection():
        logger.error("Claude CLI connection test failed, aborting")
        return 1
        
    # Start web server
    web_server = start_web_server()
    if not web_server:
        logger.error("Failed to start web server, aborting")
        return 1
        
    try:
        # Test web API session
        success = test_web_api_session()
        
        if success:
            logger.info("Web API test successful!")
            logger.info("✅ Claude CLI MCP integration with web interface is working")
            return 0
        else:
            logger.error("Web API test failed")
            logger.error("❌ Claude CLI MCP integration with web interface is not working")
            return 1
            
    finally:
        # Clean up
        logger.info("Stopping web server...")
        if web_server:
            web_server.terminate()
            web_server.wait(timeout=5)

if __name__ == "__main__":
    sys.exit(main())