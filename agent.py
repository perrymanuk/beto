"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
The ADK web interface uses this file directly based on the adk.config.json setting.
"""

import logging
import os
from typing import Optional, Any, List
from datetime import date

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import ADK components
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types
from radbot.config import config_manager

# Import calendar tools
from radbot.tools.calendar.calendar_tools import (
    list_calendar_events_tool,
    create_calendar_event_tool,
    update_calendar_event_tool,
    delete_calendar_event_tool,
    check_calendar_availability_tool
)

# Log basic info
logger.info(f"Config manager loaded. Model config: {config_manager.model_config}")
logger.info(f"Main model from config: '{config_manager.get_main_model()}'")

# Import tools
from google.adk.tools import load_artifacts
from radbot.tools.basic import get_current_time, get_weather
from radbot.tools.memory import search_past_conversations, store_important_information
from radbot.tools.web_search import create_tavily_search_tool
from radbot.tools.mcp import create_fileserver_toolset
from radbot.tools.mcp import create_crawl4ai_toolset
from radbot.tools.shell import get_shell_tool
from radbot.tools.todo import ALL_TOOLS, init_database

# Import Home Assistant tools
from radbot.tools.homeassistant import (
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
    search_ha_entities,
    get_ha_client
)

# Import agent factory functions
from radbot.tools.adk_builtin.search_tool import create_search_agent
from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent
from radbot.agent.research_agent.factory import create_research_agent

# Import the AgentTool functions for sub-agent interactions
from radbot.tools.agent_tools import (
    call_search_agent,
    call_code_execution_agent,
    call_scout_agent
)

# Create all the sub-agents we'll need
search_agent = create_search_agent(name="search_agent")
code_execution_agent = create_code_execution_agent(name="code_execution_agent")
scout_agent = create_research_agent(name="scout", as_subagent=False)

# Log startup
logger.info("ROOT agent.py loaded - this is the main implementation loaded by ADK web")
print(f"SPECIAL DEBUG: agent.py loaded with MCP_FS_ROOT_DIR={os.environ.get('MCP_FS_ROOT_DIR', 'Not set')}")


def setup_before_agent_call(callback_context: CallbackContext):
    """Setup agent before each call."""
    # Initialize Todo database schema if needed
    if "todo_init" not in callback_context.state:
        try:
            init_database()
            callback_context.state["todo_init"] = True
            logger.info("Todo database schema initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Todo database: {str(e)}")
            callback_context.state["todo_init"] = False
    
    # Initialize Home Assistant client if not already done
    if "ha_client_init" not in callback_context.state:
        try:
            ha_client = get_ha_client()
            if ha_client:
                try:
                    entities = ha_client.list_entities()
                    if entities:
                        logger.info(f"Successfully connected to Home Assistant. Found {len(entities)} entities.")
                        callback_context.state["ha_client_init"] = True
                    else:
                        logger.warning("Connected to Home Assistant but no entities were returned")
                        callback_context.state["ha_client_init"] = False
                except Exception as e:
                    logger.error(f"Error testing Home Assistant connection: {e}")
                    callback_context.state["ha_client_init"] = False
            else:
                logger.warning("Home Assistant client could not be initialized")
                callback_context.state["ha_client_init"] = False
        except Exception as e:
            logger.error(f"Error initializing Home Assistant client: {e}")
            callback_context.state["ha_client_init"] = False


# Create all the tools we'll use
tools = []

# Add AgentTool functions first (high priority)
tools.extend([
    call_search_agent,
    call_code_execution_agent,
    call_scout_agent
])

# Add Tavily web search tool
try:
    web_search_tool = create_tavily_search_tool(
        max_results=3,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True
    )
    if web_search_tool:
        tools.append(web_search_tool)
        logger.info("Added web_search tool")
except Exception as e:
    logger.warning(f"Failed to create Tavily search tool: {e}")

# Add basic tools
tools.extend([
    get_current_time,
    get_weather
])

# Add calendar tools
tools.extend([
    list_calendar_events_tool,
    create_calendar_event_tool,
    update_calendar_event_tool,
    delete_calendar_event_tool,
    check_calendar_availability_tool
])

# Add Home Assistant tools
tools.extend([
    search_ha_entities,
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity
])

# Add filesystem tools
try:
    fs_tools = create_fileserver_toolset()
    if fs_tools:
        tools.extend(fs_tools)
        logger.info(f"Added {len(fs_tools)} filesystem tools")
except Exception as e:
    logger.warning(f"Failed to create filesystem tools: {e}")

# Add Crawl4AI tools
try:
    crawl4ai_tools = create_crawl4ai_toolset()
    if crawl4ai_tools:
        tools.extend(crawl4ai_tools)
        logger.info(f"Added {len(crawl4ai_tools)} Crawl4AI tools")
except Exception as e:
    logger.warning(f"Failed to create Crawl4AI tools: {e}")

# Add Shell Command Execution tool
try:
    # Default to strict mode
    shell_tool = get_shell_tool(strict_mode=True)
    tools.append(shell_tool)
    logger.info("Added shell command execution tool in STRICT mode")
except Exception as e:
    logger.warning(f"Failed to create shell command execution tool: {e}")

# Add Todo Tools
try:
    tools.extend(ALL_TOOLS)
    logger.info(f"Added {len(ALL_TOOLS)} Todo tools")
except Exception as e:
    logger.warning(f"Failed to add Todo tools: {e}")

# Add memory tools
tools.extend([
    search_past_conversations,
    store_important_information
])

# Add artifacts loading tool
tools.append(load_artifacts)

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