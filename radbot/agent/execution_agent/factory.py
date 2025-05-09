"""
Factory function for creating the Axel execution agent.

This module provides the factory function for creating the Axel execution agent,
which is specialized for implementation tasks and complements the Scout agent.
"""

import logging
from typing import Any, List, Optional, Union

from google.adk.agents import Agent

from radbot.agent.agent_initializer import config_manager
from radbot.agent.execution_agent.agent import ExecutionAgent, AxelExecutionAgent

# Set up logging
logger = logging.getLogger(__name__)


def create_execution_agent(
    name: str = "axel",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True,
    enable_code_execution: bool = True,
    app_name: str = "beto"
) -> Union[ExecutionAgent, Any]:
    """
    Create an execution agent with the specified configuration.
    
    Args:
        name: Name of the agent (should be "axel" for consistent transfers)
        model: LLM model to use (defaults to config setting)
        custom_instruction: Optional custom instruction to override the default
        tools: List of tools to provide to the agent
        as_subagent: Whether to return the ExecutionAgent or the underlying ADK agent
        enable_code_execution: Whether to enable Code Execution capability
        app_name: Application name (should match the parent agent name for ADK 0.4.0+)
        
    Returns:
        Union[ExecutionAgent, Any]: The created agent instance
    """
    # Use agent-specific model from config or fall back to default
    if model is None:
        model = config_manager.get_agent_model("axel_agent")
        logger.info(f"Using model from config for axel_agent: {model}")
    
    # Get the instruction file or use the provided custom instruction
    if custom_instruction:
        instruction = custom_instruction
        logger.info("Using provided custom instruction for Axel agent")
    else:
        try:
            instruction = config_manager.get_instruction("axel")
            logger.info("Using 'axel.md' instruction file for Axel agent")
        except FileNotFoundError:
            logger.warning("Instruction 'axel.md' not found, using minimal instruction")
            instruction = "You are Axel, a specialized execution agent focused on implementing specifications."
    
    # Create the tool list
    agent_tools = []
    if tools:
        agent_tools.extend(tools)
    
    # Add code execution tool if enabled
    if enable_code_execution:
        # This would be implemented to add code execution tools
        # from radbot.tools.shell import shell_command_tool
        # agent_tools.append(shell_command_tool)
        logger.info("Code execution capability enabled for Axel agent")
    
    # Create the ExecutionAgent instance
    execution_agent = ExecutionAgent(
        name=name,
        model=model,
        instruction=instruction,
        tools=agent_tools,
        enable_code_execution=enable_code_execution,
        app_name=app_name
    )
    
    logger.info(f"Created Axel execution agent with {len(agent_tools)} tools")
    
    # Return either the ExecutionAgent or the underlying ADK agent
    if as_subagent:
        # Create and return the ADK agent for use as a subagent
        adk_agent = Agent(
            name=name,
            model=model,
            instruction=instruction,
            tools=agent_tools
        )
        
        # Store the execution_agent reference on the ADK agent for later access
        adk_agent._execution_agent = execution_agent
        
        logger.info(f"Returning ADK agent for {name} to use as subagent")
        return adk_agent
    else:
        # Return the ExecutionAgent wrapper
        logger.info(f"Returning ExecutionAgent wrapper for {name}")
        return execution_agent