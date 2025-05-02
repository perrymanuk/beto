# Inter-Agent Communication Strategy

This document details the implementation of communication strategies between agents within the RaderBot framework.

## Communication Architecture Overview

The RaderBot framework supports three primary methods of inter-agent communication:

1. **Agent Tool Call**: Main agent calls a sub-agent directly as a tool
2. **Agent Transfer**: Main agent transfers control to a specialized sub-agent
3. **Shared Session State**: Agents communicate by reading/writing to shared session state

## Internal ADK Communication Implementation

### 1. Sub-Agent Classes (`agents/sub_agents.py`)

```python
# raderbot/agents/sub_agents.py

"""
Sub-agent implementations for the RaderBot framework.
"""

from typing import Optional, Dict, Any, List
import logging

from google.adk.agents import Agent
from raderbot.config import config_manager

logger = logging.getLogger(__name__)

def create_summarizer_agent() -> Agent:
    """
    Create a specialized agent for summarizing content.
    
    Returns:
        Agent: Configured summarization agent
    """
    return Agent(
        name="Summarizer",
        model=config_manager.get_sub_agent_model(),
        instruction=config_manager.get_instruction("summarizer_agent"),
        description="Specialized agent that summarizes text content into concise summaries."
    )

def create_research_agent(tools: Optional[List[Any]] = None) -> Agent:
    """
    Create a specialized agent for research tasks.
    
    Args:
        tools: Optional list of research tools (e.g., search)
        
    Returns:
        Agent: Configured research agent
    """
    return Agent(
        name="Researcher",
        model=config_manager.get_main_model(),  # Use main model for complex research
        instruction=config_manager.get_instruction("researcher_agent"),
        description="Specialized agent that performs in-depth research on topics.",
        tools=tools or []
    )

def create_home_assistant_agent(ha_tools: Optional[List[Any]] = None) -> Agent:
    """
    Create a specialized agent for Home Assistant interactions.
    
    Args:
        ha_tools: List of Home Assistant MCP tools
        
    Returns:
        Agent: Configured Home Assistant agent
    """
    return Agent(
        name="HomeAssistantController",
        model=config_manager.get_sub_agent_model(),
        instruction=config_manager.get_instruction("home_assistant_agent"),
        description="Specialized agent that controls smart home devices via Home Assistant.",
        tools=ha_tools or []
    )
```

### 2. Agent Tool Wrappers (`agents/agent_tools.py`)

```python
# raderbot/agents/agent_tools.py

"""
Agent tool wrappers for the RaderBot framework.

This module provides utilities to wrap agents as callable tools.
"""

from typing import List, Any

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

def wrap_agent_as_tool(agent: Agent) -> AgentTool:
    """
    Wrap an agent as a callable tool for use by another agent.
    
    Args:
        agent: The agent to wrap as a tool
        
    Returns:
        AgentTool: The wrapped agent as a callable tool
    """
    return AgentTool(agent=agent)

def wrap_agents_as_tools(agents: List[Agent]) -> List[AgentTool]:
    """
    Wrap multiple agents as callable tools.
    
    Args:
        agents: List of agents to wrap as tools
        
    Returns:
        List[AgentTool]: The wrapped agents as callable tools
    """
    return [wrap_agent_as_tool(agent) for agent in agents]
```

### 3. Agent Manager for Transfer (`agents/manager.py`)

```python
# raderbot/agents/manager.py

"""
Agent manager for handling agent hierarchies and transfers.
"""

from typing import Dict, Any, Optional, List
import logging

from google.adk.agents import Agent, LlmAgent
from google.adk.runners import Runner, LlmAgentRunner
from google.adk.sessions import SessionService, InMemorySessionService
from google.adk.autoflow import AutoFlow

from raderbot.config import config_manager
from raderbot.agents.sub_agents import (
    create_summarizer_agent,
    create_research_agent,
    create_home_assistant_agent
)

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Manager for agent hierarchies, creation, and transfers.
    """
    
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        tools: Optional[List[Any]] = None,
    ):
        """
        Initialize the agent manager.
        
        Args:
            session_service: Optional session service for conversation state
            tools: Optional list of tools to provide to all agents
        """
        self.session_service = session_service or InMemorySessionService()
        self.base_tools = tools or []
        
        # Create the root agent
        self.main_agent = self._create_main_agent()
        
        # Create and register sub-agents
        self.sub_agents = {}
        self._create_sub_agents()
        
        # Initialize the runner with AutoFlow for agent transfers
        self.runner = Runner(
            agent=self.main_agent,
            app_name="raderbot",
            session_service=self.session_service,
            flow=AutoFlow()  # Enable agent transfers
        )
    
    def _create_main_agent(self) -> Agent:
        """
        Create the main coordinator agent.
        
        Returns:
            Agent: The configured main agent
        """
        return Agent(
            name="MainCoordinator",
            model=config_manager.get_main_model(),
            instruction=config_manager.get_instruction("main_agent"),
            description="The main coordinating agent that handles user requests and orchestrates tasks.",
            tools=self.base_tools
        )
    
    def _create_sub_agents(self) -> None:
        """
        Create and register all sub-agents.
        """
        # Create standard sub-agents
        self.sub_agents["summarizer"] = create_summarizer_agent()
        self.sub_agents["researcher"] = create_research_agent(tools=self.base_tools)
        self.sub_agents["home_assistant"] = create_home_assistant_agent()
        
        # Add all sub-agents to the main agent
        self.main_agent.sub_agents = list(self.sub_agents.values())
    
    def process_message(self, user_id: str, message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            
        Returns:
            The agent's response as a string
        """
        # Use AutoFlow runner to support agent transfers
        events = list(self.runner.run_async(user_id=user_id, message=message))
        
        # Extract the agent's text response from the events
        for event in events:
            if event.type.name == "TEXT" and event.payload.get("author_role") == "assistant":
                return event.payload.get("text", "")
        
        # Fallback if no text response was found
        return "I apologize, but I couldn't generate a response."
    
    def add_tool_to_all_agents(self, tool: Any) -> None:
        """
        Add a tool to all agents in the hierarchy.
        
        Args:
            tool: The tool to add
        """
        # Add to main agent
        current_tools = list(self.main_agent.tools) if self.main_agent.tools else []
        current_tools.append(tool)
        self.main_agent.tools = current_tools
        
        # Add to sub-agents that accept tools
        for agent in self.sub_agents.values():
            if hasattr(agent, 'tools'):
                agent_tools = list(agent.tools) if agent.tools else []
                agent_tools.append(tool)
                agent.tools = agent_tools
```

### 4. Integration Example

```python
# Example usage

from raderbot.agents.manager import AgentManager
from raderbot.tools.basic_tools import get_current_time, get_weather
from raderbot.agents.agent_tools import wrap_agent_as_tool

# Create the agent manager with basic tools
manager = AgentManager(tools=[get_current_time, get_weather])

# Access a specific sub-agent
summarizer = manager.sub_agents["summarizer"]

# For explicit tool use, wrap the summarizer agent as a tool
# and add it to the main agent
summarizer_tool = wrap_agent_as_tool(summarizer)
manager.main_agent.tools = list(manager.main_agent.tools) + [summarizer_tool]

# Process a user message (which might cause an agent transfer or tool use)
response = manager.process_message("user123", "What's the weather in London?")
```

## Shared Session State Communication

Agents can communicate implicitly through the shared session state:

```python
# raderbot/tools/state_tools.py

"""
Tools for managing shared session state as a communication mechanism.
"""

from typing import Any, Dict, Optional
import logging

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def store_in_state(key: str, value: Any, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Store a value in the shared session state.
    
    Args:
        key: The key to store the value under
        value: The value to store
        tool_context: Tool context providing access to session state
        
    Returns:
        Status dictionary
    """
    try:
        tool_context.state[key] = value
        return {
            "status": "success",
            "message": f"Successfully stored value under key '{key}'."
        }
    except Exception as e:
        logger.error(f"Error storing in state: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to store value: {str(e)}"
        }

def retrieve_from_state(key: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Retrieve a value from the shared session state.
    
    Args:
        key: The key to retrieve
        tool_context: Tool context providing access to session state
        
    Returns:
        Dictionary containing the value or error
    """
    try:
        value = tool_context.state.get(key)
        if value is not None:
            return {
                "status": "success",
                "value": value
            }
        else:
            return {
                "status": "error",
                "error_message": f"No value found for key '{key}'."
            }
    except Exception as e:
        logger.error(f"Error retrieving from state: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to retrieve value: {str(e)}"
        }
```

## Recommendation Summary

Based on the requirements, the recommended approach for this project is:

1. **For Internal Communication** (between main agent and sub-agents):
   - Use ADK's built-in `AgentTool` for synchronous sub-agent calls where the parent needs results
   - Use ADK's `AutoFlow` for agent transfers when specialized agents should take over
   - Use shared session state for passing data between sequential steps

## Next Steps

With the agent communication strategy implemented, the next steps are:

1. Implement the Qdrant memory system for persistent agent memory
2. Set up MCP integration for Home Assistant 
3. Create the comprehensive testing suite for the framework