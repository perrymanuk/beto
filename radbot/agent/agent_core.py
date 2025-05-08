"""
Core agent creation and configuration for RadBot.

This module provides the main agent creation and configuration functionality 
for the RadBot agent system, creating the root agent with all needed tools.
"""

import logging
from typing import Optional, Any, List
from datetime import date

# Import from our initialization and tools setup modules
from radbot.agent.agent_initializer import (
    logger,
    Agent,
    types,
    config_manager
)

from radbot.agent.agent_tools_setup import (
    tools,
    setup_before_agent_call,
    search_agent,
    code_execution_agent,
    scout_agent
)

# Get the instruction from the config manager
instruction = config_manager.get_instruction("main_agent")

# Add AgentTool instructions
instruction += """
## Specialized Agent Tools

You have access to specialized agents through these tools:

1. `call_search_agent(query, max_results=5)` - Perform web searches using Google Search.
   Example: call_search_agent(query="latest news on quantum computing")

2. `call_code_execution_agent(code, description="")` - Execute Python code.
   Example: call_code_execution_agent(code="print('Hello world')", description="Simple test")

3. `call_scout_agent(research_topic)` - Research a topic using a specialized agent.
   Example: call_scout_agent(research_topic="environmental impact of electric vehicles")

Use these tools when you need specialized capabilities.
"""

# Get the model name from config
model_name = config_manager.get_main_model()
logger.info(f"Using model: {model_name}")

# Get today's date for the global instruction
today = date.today()

# Create the root agent
root_agent = Agent(
    model=model_name,
    name="beto",
    instruction=instruction,
    global_instruction=f"""
    You are an intelligent agent for handling various tasks.
    Today's date: {today}
    """,
    sub_agents=[search_agent, code_execution_agent, scout_agent],
    tools=tools,
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

# Log agent creation
logger.info(f"Created root agent 'beto' with {len(tools)} tools and {len(root_agent.sub_agents)} sub-agents")

def create_agent(tools: Optional[List[Any]] = None, app_name: str = "beto"):
    """
    Create the agent with all necessary tools.
    
    This is the entry point used by ADK web to create the agent.
    
    Args:
        tools: Optional list of additional tools to include
        app_name: Application name to use, defaults to "beto"
        
    Returns:
        An ADK BaseAgent instance
    """
    # If additional tools are provided, add them to the agent
    if tools:
        all_tools = list(root_agent.tools) + list(tools)
        root_agent.tools = all_tools
        logger.info(f"Added {len(tools)} additional tools to agent")
    
    return root_agent