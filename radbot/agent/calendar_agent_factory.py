"""Google Calendar agent factory."""

from typing import Dict, Optional

from google.adk.agents import Agent 
from google.adk.sessions import InMemorySessionService
from google.adk.tools import FunctionTool

from radbot.agent.agent import RadBotAgent
from radbot.config.settings import ConfigManager
from radbot.tools.calendar.calendar_manager import CalendarManager
from radbot.tools.calendar.calendar_tools import (
    check_calendar_availability_tool,
    create_calendar_event_tool,
    delete_calendar_event_tool,
    list_calendar_events_tool,
    update_calendar_event_tool,
)


def create_calendar_agent(
    model: Optional[str] = None,
    config_manager: Optional[ConfigManager] = None,
    calendar_manager: Optional[CalendarManager] = None,
    additional_tools: Optional[Dict[str, FunctionTool]] = None,
    instruction_name: str = "main_agent",
) -> RadBotAgent:
    """Create a Google Calendar enabled agent.
    
    Args:
        model: LLM model name. If None, uses the default from config.
        config_manager: ConfigManager instance. If None, creates a new one.
        calendar_manager: CalendarManager instance. If None, creates a new one.
        additional_tools: Additional function tools to add to the agent.
        instruction_name: Name of instruction to load from config.
        
    Returns:
        RadBotAgent: An initialized agent with Google Calendar capabilities.
    """
    # Create config manager if not provided
    if config_manager is None:
        config_manager = ConfigManager()
    
    # Create calendar manager if not provided
    if calendar_manager is None:
        calendar_manager = CalendarManager()
        # Authenticate with personal account
        calendar_manager.authenticate_personal()
    
    # Create list of calendar tools
    calendar_tools = [
        list_calendar_events_tool,
        create_calendar_event_tool,
        update_calendar_event_tool,
        delete_calendar_event_tool,
        check_calendar_availability_tool,
    ]
    
    # Build the tools list
    all_tools = calendar_tools
    
    # Add any additional tools
    if additional_tools:
        all_tools.extend(additional_tools.values())
    
    # Create the agent using the agent factory from radbot.agent.agent
    from radbot.agent.agent import create_agent
    
    agent = create_agent(
        tools=all_tools,
        model=model,
        instruction_name=instruction_name,
        config=config_manager
    )
    
    return agent