"""
Agent registry module for RadBot system.

This module exports all available agents to be used in the multi-agent system.
It follows the pattern used in Google's ADK samples for agent registration.
"""

import logging
import os
from typing import Optional, Dict, Any

from google.adk.agents import Agent
from radbot.config import config_manager

# Set up logging
logger = logging.getLogger(__name__)

# Import agent factories
from radbot.tools.adk_builtin.search_tool import create_search_agent
from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent
from radbot.agent.research_agent.factory import create_research_agent

# Main model to use for all agents (can be overridden)
MODEL_NAME = os.environ.get("RADBOT_MAIN_MODEL", config_manager.get_main_model())

# Create and export the search agent
try:
    search_agent = create_search_agent(
        name="search_agent",
        model=MODEL_NAME,
        config=config_manager,
        instruction_name="search_agent"
    )
    logger.info(f"Created search_agent with model {MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to create search_agent: {str(e)}")
    search_agent = None

# Create and export the code execution agent
try:
    code_execution_agent = create_code_execution_agent(
        name="code_execution_agent",
        model=MODEL_NAME,
        config=config_manager,
        instruction_name="code_execution_agent"
    )
    logger.info(f"Created code_execution_agent with model {MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to create code_execution_agent: {str(e)}")
    code_execution_agent = None

# Create and export the scout agent
try:
    scout_agent = create_research_agent(
        name="scout",
        model=MODEL_NAME,
        as_subagent=False,  # Get the ADK agent directly
        enable_google_search=False,  # We'll handle these separately
        enable_code_execution=False
    )
    logger.info(f"Created scout agent with model {MODEL_NAME}")
except Exception as e:
    logger.error(f"Failed to create scout_agent: {str(e)}")
    scout_agent = None

# Export all agents
__all__ = ["search_agent", "code_execution_agent", "scout_agent"]

# Log available agents
available_agents = []
if search_agent:
    available_agents.append("search_agent")
if code_execution_agent:
    available_agents.append("code_execution_agent")
if scout_agent:
    available_agents.append("scout_agent")

logger.info(f"Available agents in registry: {', '.join(available_agents)}")