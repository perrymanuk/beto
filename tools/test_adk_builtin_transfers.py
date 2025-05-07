#!/usr/bin/env python
"""
Test script for verifying ADK built-in agent transfers.

This script starts the web application with the ADK built-in tools
(Google Search and Code Execution) enabled and configured to test
agent transfers to and from these built-in agents.
"""

import os
import sys
import logging
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure the radbot package is importable
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def setup_environment():
    """Set up the environment variables for testing."""
    logger.info("Setting up environment for ADK built-in agent tests")
    
    # Enable Google Search
    os.environ["RADBOT_ENABLE_ADK_SEARCH"] = "true"
    logger.info("Enabled ADK Search tool")
    
    # Enable Code Execution
    os.environ["RADBOT_ENABLE_ADK_CODE_EXEC"] = "true"
    logger.info("Enabled ADK Code Execution tool")
    
    # Set verbose logging for agent transfers
    os.environ["LOG_LEVEL"] = "DEBUG"
    logger.info("Set log level to DEBUG for detailed transfer logs")

def run_web_app():
    """Start the web application."""
    logger.info("Starting web application with ADK built-in agents")
    
    try:
        from radbot.web import app
        
        # Import necessary modules for startup
        from agent import root_agent
        
        logger.info(f"Root agent name: {root_agent.name if hasattr(root_agent, 'name') else 'unnamed'}")
        
        # Get sub-agents
        sub_agents = getattr(root_agent, 'sub_agents', [])
        sub_agent_names = [sa.name for sa in sub_agents if hasattr(sa, 'name')]
        logger.info(f"Sub-agents: {sub_agent_names}")
        
        # Check for search and code execution agents
        has_search = "search_agent" in sub_agent_names
        has_code_exec = "code_execution_agent" in sub_agent_names
        logger.info(f"Has search agent: {has_search}")
        logger.info(f"Has code execution agent: {has_code_exec}")
        
        # Report success
        logger.info(f"Web application started. Please navigate to http://localhost:8080")
        logger.info(f"Test agent transfers by:")
        logger.info(f" - Asking the agent to search Google for something")
        logger.info(f" - Asking the agent to execute some Python code")
        logger.info(f" - Check the logs for transfer events and debugging information")
        logger.info(f"Press Ctrl+C to exit when testing is complete")
        
        # Run the application
        # Note: This will block until manually terminated
        app.run(host='0.0.0.0', port=8080)
        
    except ImportError as e:
        logger.error(f"Failed to import required modules: {e}")
    except Exception as e:
        logger.error(f"Error starting web application: {e}", exc_info=True)

if __name__ == "__main__":
    logger.info("Starting ADK Built-in Agent Transfer Test")
    
    # Setup environment
    setup_environment()
    
    # Run the web application
    run_web_app()