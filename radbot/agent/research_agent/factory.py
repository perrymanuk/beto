"""
Research agent factory.

This module provides factory functions for creating research agents.
"""

import logging
import os
from typing import Optional, List, Dict, Any, Union

# Set up logging
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

# Import ADK components
from google.adk.tools import FunctionTool

# Import project components
from radbot.agent.research_agent.agent import ResearchAgent
from radbot.config import config_manager
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

def create_research_agent(
    name: str = "scout",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True,
    enable_google_search: bool = False,
    enable_code_execution: bool = False,
    app_name: str = "beto"
) -> Union[ResearchAgent, Any]:
    """
    Create a research agent with the specified configuration.
    
    Args:
        name: Name of the agent (should be "scout" for consistent transfers)
        model: LLM model to use (defaults to config setting)
        custom_instruction: Optional custom instruction to override the default
        tools: List of tools to provide to the agent
        as_subagent: Whether to return the ResearchAgent or the underlying ADK agent
        enable_google_search: Whether to enable Google Search capability
        enable_code_execution: Whether to enable Code Execution capability
        app_name: Application name (should match the parent agent name for ADK 0.4.0+)
        
    Returns:
        Union[ResearchAgent, Any]: The created agent instance
    """
    # Ensure agent name is always "scout" for consistent transfers
    if name != "scout":
        logger.warning(f"Agent name '{name}' changed to 'scout' for consistent transfers")
        name = "scout"
        
    # Use default model from config if not specified
    if model is None:
        model = config_manager.get_main_model()
        logger.info(f"Using model from config: {model}")
    
    # Create the research agent with explicit name and app_name
    research_agent = ResearchAgent(
        name=name,
        model=model,
        instruction=custom_instruction,  # Will use default if None
        tools=tools,
        enable_sequential_thinking=True,
        enable_google_search=enable_google_search,
        enable_code_execution=enable_code_execution,
        app_name=app_name  # Should match parent agent name
    )
    
    # Import required components for agent transfers
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Get the ADK agent
    adk_agent = research_agent.get_adk_agent()
    
    # Ensure agent has transfer_to_agent tool
    if hasattr(adk_agent, 'tools'):
        # Check if tool already exists
        has_transfer_tool = False
        for tool in adk_agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
            if tool_name == 'transfer_to_agent':
                has_transfer_tool = True
                break
                
        if not has_transfer_tool:
            adk_agent.tools.append(transfer_to_agent)
            logger.info("Added transfer_to_agent tool to scout agent")
    
    # Create built-in tool sub-agents if requested
    sub_agents = []
    
    if enable_google_search or enable_code_execution:
        try:
            from radbot.tools.adk_builtin import create_search_agent, create_code_execution_agent
            
            if enable_google_search:
                try:
                    search_agent = create_search_agent(name="search_agent")
                    # Make sure search_agent has transfer_to_agent
                    if hasattr(search_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in search_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            search_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(search_agent)
                    logger.info("Created search_agent as sub-agent for scout")
                except Exception as e:
                    logger.warning(f"Failed to create search agent for scout: {str(e)}")
            
            if enable_code_execution:
                try:
                    code_agent = create_code_execution_agent(name="code_execution_agent")
                    # Make sure code_agent has transfer_to_agent
                    if hasattr(code_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in code_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            code_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(code_agent)
                    logger.info("Created code_execution_agent as sub-agent for scout")
                except Exception as e:
                    logger.warning(f"Failed to create code execution agent for scout: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to import built-in tool factories for scout: {str(e)}")
    
    # Add parent agent (beto) to sub-agents list for proper backlinks
    # This ensures that scout can transfer back to beto
    try:
        from google.adk.agents import Agent
        
        # Create a proxy agent for beto (parent) to allow transfers back
        beto_agent = Agent(
            name="beto",  # Must be exactly "beto" for transfers back
            model=model or config_manager.get_main_model(),
            instruction="Main coordinating agent",  # Simple placeholder
            description="Main coordinating agent that handles user requests",
            tools=[transfer_to_agent]  # Essential to have transfer_to_agent
        )
        
        # Add beto to the list of sub-agents even if we have other sub-agents
        if not sub_agents:
            sub_agents = []
        
        # Check if we already have beto in the list
        beto_already_added = False
        for sa in sub_agents:
            if hasattr(sa, 'name') and sa.name == "beto":
                beto_already_added = True
                break
                
        if not beto_already_added:
            sub_agents.append(beto_agent)
            logger.info("Added 'beto' agent to scout's sub_agents list for proper back-transfers")
    except Exception as e:
        logger.error(f"Failed to create beto proxy agent for scout's sub_agents: {str(e)}")
    
    # Set sub-agents list on the scout agent
    if sub_agents and hasattr(adk_agent, 'sub_agents'):
        adk_agent.sub_agents = sub_agents
        logger.info(f"Added {len(sub_agents)} sub-agents to scout agent")
        
        # Log the agent tree for debugging
        sub_agent_names = [sa.name for sa in adk_agent.sub_agents if hasattr(sa, 'name')]
        logger.info(f"Scout agent tree: root='scout', sub_agents={sub_agent_names}")
    
    # Return either the ResearchAgent wrapper or the underlying ADK agent
    if as_subagent:
        return research_agent
    else:
        # Double-check agent name before returning
        if hasattr(adk_agent, 'name') and adk_agent.name != name:
            logger.warning(f"ADK Agent name mismatch: '{adk_agent.name}' not '{name}' - fixing")
            adk_agent.name = name
            
        return adk_agent