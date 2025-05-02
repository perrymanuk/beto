# Base Agent Structure Implementation

This document details the implementation of the core agent structure using Google's Agent Development Kit (ADK).

## Core Agent Components

The agent framework consists of several key components:

1. Main Coordinator Agent
2. ADK Runner
3. Session Management
4. Initial Tool Integration

## Agent Implementation (`agent.py`)

The main agent module defines the core agent and supporting structures.

```python
# radbot/agent.py

"""
Core agent implementation for the radbot framework.
"""

import os
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from google.adk.agents import Agent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import SessionService, InMemorySessionService

# Load environment variables
load_dotenv()

# Define the main agent instruction
MAIN_AGENT_INSTRUCTION = """
You are the central coordinator for an AI assistant system. Your primary role is to understand the user's request and orchestrate the necessary actions to fulfill it.

**Capabilities:**
*   You can answer general questions directly.
*   You have access to basic tools: `get_current_time`, `get_weather`. Use them when the user asks for current time or weather information.
*   You can access long-term memory using the `search_past_conversations` tool to recall previous interactions if relevant to the current query.
*   You can interact with Home Assistant via MCP tools (e.g., `HA_turn_light_on`, `HA_get_temperature`). Use these when the user requests actions or information related to their smart home.

**Workflow:**
1.  Analyze the user's query.
2.  If the query requires past context, consider using `search_past_conversations`.
3.  Determine the best course of action: answer directly, use a basic tool, use a Home Assistant tool, or delegate.
4.  If using a tool, clearly state you are using it and present the result clearly.
5.  If a tool or sub-agent returns an error, inform the user politely and state you cannot complete the request.
6.  Provide a final, concise response to the user.

**Constraints:**
*   Be polite and helpful.
*   Do not guess information if a tool fails or doesn't provide an answer.
*   Prioritize using specific tools/agents when applicable over general knowledge.
"""

# Select the Gemini model based on environment, defaulting to Pro 2.5
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")

class radbotAgent:
    """
    Main agent class for the radbot framework.
    
    This class encapsulates the ADK agent, runner, and session management.
    It provides a unified interface for interacting with the agent system.
    """
    
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        tools: Optional[List[Any]] = None,
        model: str = GEMINI_MODEL,
    ):
        """
        Initialize the radbot agent.
        
        Args:
            session_service: Optional custom session service for conversation state
            tools: Optional list of tools to provide to the agent
            model: Gemini model to use for the agent
        """
        # Use provided session service or create an in-memory one
        self.session_service = session_service or InMemorySessionService()
        
        # Create the main agent
        self.root_agent = Agent(
            name="main_coordinator",
            model=model,
            instruction=MAIN_AGENT_INSTRUCTION,
            description="The main coordinating agent that handles user requests and orchestrates tasks.",
            tools=tools or []  # Start with empty tools list if none provided
        )
        
        # Initialize the runner with the agent
        self.runner = Runner(
            agent=self.root_agent,
            app_name="radbot",
            session_service=self.session_service
        )
    
    def add_tool(self, tool: Any) -> None:
        """
        Add a tool to the agent's capabilities.
        
        Args:
            tool: The tool to add (function, FunctionTool, or MCPToolset)
        """
        # Get current tools and add the new one
        current_tools = list(self.root_agent.tools) if self.root_agent.tools else []
        current_tools.append(tool)
        
        # Update the agent's tools
        self.root_agent.tools = current_tools
    
    def add_tools(self, tools: List[Any]) -> None:
        """
        Add multiple tools to the agent's capabilities.
        
        Args:
            tools: List of tools to add
        """
        for tool in tools:
            self.add_tool(tool)
    
    def process_message(self, user_id: str, message: str) -> str:
        """
        Process a user message and return the agent's response.
        
        Args:
            user_id: Unique identifier for the user
            message: The user's message
            
        Returns:
            The agent's response as a string
        """
        # Run the agent on the message and extract the first text response
        events = list(self.runner.run_async(user_id=user_id, message=message))
        
        # Extract the agent's text response from the events
        for event in events:
            if event.type.name == "TEXT" and event.payload.get("author_role") == "assistant":
                return event.payload.get("text", "")
        
        # Fallback if no text response was found
        return "I apologize, but I couldn't generate a response."

    def add_sub_agent(self, sub_agent: Agent) -> None:
        """
        Add a sub-agent to the main agent.
        
        Args:
            sub_agent: The agent to add as a sub-agent
        """
        # Get current sub-agents
        current_sub_agents = list(self.root_agent.sub_agents) if self.root_agent.sub_agents else []
        current_sub_agents.append(sub_agent)
        
        # Update the agent's sub-agents list
        self.root_agent.sub_agents = current_sub_agents


# Create a factory function for easy agent creation
def create_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    model: str = GEMINI_MODEL
) -> radbotAgent:
    """
    Create a configured radbot agent.
    
    Args:
        session_service: Optional session service for conversation state
        tools: Optional list of tools for the agent
        model: Gemini model to use
        
    Returns:
        A configured radbotAgent instance
    """
    return radbotAgent(session_service=session_service, tools=tools, model=model)
```

## Basic CLI Interface (`cli.py`)

This module provides a simple command-line interface for interacting with the agent.

```python
# radbot/cli.py

"""
Command-line interface for interacting with the radbot agent.
"""

import sys
import uuid

from radbot.agent import create_agent

def main():
    """
    Run the radbot CLI interface.
    """
    # Generate a random user ID for this session
    user_id = str(uuid.uuid4())
    
    # Create the agent
    agent = create_agent()
    
    print("radbot Agent CLI")
    print("Type 'exit' or 'quit' to end the session")
    print("Type your message and press Enter to interact with the agent")
    print("-" * 50)
    
    # Main interaction loop
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        # Check for exit command
        if user_input.lower() in ["exit", "quit"]:
            print("Exiting radbot CLI. Goodbye!")
            sys.exit(0)
        
        # Process the message
        try:
            response = agent.process_message(user_id, user_input)
            print(f"\nradbot: {response}")
        except Exception as e:
            print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
```

## Entry Points (`__main__.py`)

This module provides the entry point for running the agent as a command-line application.

```python
# radbot/__main__.py

"""
Entry point for running the radbot agent directly.
"""

from radbot.cli import main

if __name__ == "__main__":
    main()
```

## Package Initialization (`__init__.py`)

```python
# radbot/__init__.py

"""
radbot - A modular AI agent framework using Google ADK, Qdrant, MCP, and A2A.
"""

__version__ = "0.1.0"

from radbot.agent import create_agent, radbotAgent
```

## Integration with Makefile

Update the Makefile to include commands for running the CLI:

```makefile
# Makefile (excerpt)

# ...existing commands...

run-cli:
	python -m radbot

# ...
```

## Key Design Considerations

### Agent Structure

- **radbotAgent Class**: Encapsulates the ADK components (agent, runner, session service) into a single, easy-to-use class that handles the initialization and interaction details.
- **Factory Function**: The `create_agent()` function provides a simple way to instantiate a configured agent without needing to directly use the class constructor.
- **Modular Tool Integration**: The `add_tool()` and `add_tools()` methods allow for dynamic addition of tools, enabling incremental enhancement of agent capabilities.
- **Sub-Agent Support**: The `add_sub_agent()` method facilitates the creation of a hierarchical agent structure with specialized sub-agents.

### ADK Components

- **Agent**: The core `Agent` class from ADK serves as the foundation of our agent system, configured with a detailed instruction prompt.
- **Runner**: The `Runner` handles the execution flow and interaction with the session service.
- **Session Management**: Initially using `InMemorySessionService` for simplicity, but designed to allow custom session services (e.g., a persistent session service) to be injected.

### Extensibility

The base agent structure is designed to be extended with:

- Custom tools (both internal and external via MCP)
- Memory system integration
- Sub-agent hierarchies for specialized tasks
- Alternative session management strategies

## Next Steps

With the base agent structure in place, the next implementation tasks are:

1. Implement the basic tools (time, weather)
2. Create the agent configuration system
3. Implement the Qdrant memory system
4. Design the inter-agent communication strategy
5. Set up MCP integration for Home Assistant