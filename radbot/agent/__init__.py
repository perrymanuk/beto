"""
Agent package for the RadBot framework.
"""

import logging
import sys
logger = logging.getLogger(__name__)

# Import agent classes and factories from the proper modules
from radbot.agent.agent import (
    RadBotAgent, 
    AgentFactory, 
    create_agent as internal_create_agent,  # Renamed to avoid confusion
    create_runner
)
from radbot.agent.memory_agent_factory import create_memory_enabled_agent
from radbot.agent.web_search_agent_factory import (
    create_websearch_agent,
    create_websearch_enabled_root_agent
)

# Import the root_agent from the root-level agent.py module
logger.info("Importing root_agent from the root-level agent.py module")
try:
    # We need to import the root-level agent module
    import agent
    root_agent = agent.root_agent
    
    # Also use its create_agent function
    create_agent = agent.create_agent
    
    logger.info("Successfully imported root_agent from root-level agent.py")
except Exception as e:
    logger.error(f"Error importing root_agent from root-level agent.py: {str(e)}")
    # Fallback to our internal create_agent
    create_agent = internal_create_agent
    # Create a minimal root_agent as fallback
    from google.adk.agents import Agent
    root_agent = Agent(
        name="radbot_web",
        description="Fallback agent (error loading root_agent)",
        tools=[]
    )

# Export classes and functions
__all__ = [
    'RadBotAgent',
    'AgentFactory',
    'create_agent',
    'create_runner',
    'create_memory_enabled_agent',
    'create_websearch_agent',
    'create_websearch_enabled_root_agent',
    'root_agent'  # Export this for ADK web to use
]