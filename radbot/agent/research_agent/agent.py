"""
Research agent implementation.

This module provides the implementation of the research agent, a specialized
agent for technical research and design collaboration.
"""

import logging
import os
from typing import List, Optional, Dict, Any, Union

# Set up logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

# Import project components
from radbot.agent.research_agent.instructions import get_full_research_agent_instruction
from radbot.agent.research_agent.tools import get_research_tools
from radbot.config import config_manager

class ResearchAgent:
    """
    A specialized agent for technical research and design collaboration.
    
    This agent is designed to:
    1. Perform technical research using web scraping, internal knowledge search, and GitHub
    2. Engage in design discussions as a "rubber duck"
    
    The agent is meant to be used as a sub-agent within a multi-agent system,
    typically receiving tasks from a main coordinator agent.
    """
    
    def __init__(
        self,
        name: str = "technical_research_agent",
        model: Optional[str] = None,
        instruction: Optional[str] = None,
        description: Optional[str] = None,
        tools: Optional[List[FunctionTool]] = None,
        output_key: Optional[str] = "research_summary"
    ):
        """
        Initialize the ResearchAgent.
        
        Args:
            name: Name of the agent
            model: LLM model to use (defaults to config setting)
            instruction: Agent instruction (defaults to standard research instruction)
            description: Agent description (defaults to standard description)
            tools: List of tools to provide to the agent (defaults to standard research tools)
            output_key: Session state key to store the agent's output (default: "research_summary")
        """
        logger.info(f"Initializing ResearchAgent with name: {name}")
        
        # Use default model from config if not specified
        if model is None:
            model = config_manager.get_main_model()
            logger.info(f"Using model from config: {model}")
        
        # Use default instruction if not specified
        if instruction is None:
            instruction = get_full_research_agent_instruction()
            logger.info("Using default research agent instruction")
        
        # Use default description if not specified
        if description is None:
            description = (
                "A specialized sub-agent for conducting technical research "
                "(web, internal docs, GitHub) and facilitating technical design "
                "discussions (rubber ducking)."
            )
            logger.info("Using default research agent description")
        
        # Use default research tools if not specified
        if tools is None:
            tools = get_research_tools()
            logger.info(f"Using default research tools: {len(tools)} tools loaded")
        
        # Create the LlmAgent instance
        self.agent = LlmAgent(
            name=name,
            model=model,
            instruction=instruction,
            description=description,
            tools=tools,
            output_key=output_key
        )
        
        logger.info(f"ResearchAgent successfully initialized with {len(tools)} tools")
    
    def get_adk_agent(self):
        """
        Get the underlying ADK agent instance.
        
        Returns:
            LlmAgent: The ADK agent instance
        """
        return self.agent
