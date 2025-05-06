"""
Main agent implementation for Radbot.

This module defines the core RadBotAgent class and factory functions using Google's ADK.
"""
import os
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
SessionService = InMemorySessionService  # Type alias for backward compatibility

from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Load environment variables
load_dotenv()

# Fallback instruction if configuration loading fails
FALLBACK_INSTRUCTION = """
You are a helpful and versatile AI assistant. Your goal is to understand the user's request
and fulfill it by using available tools, delegating to specialized sub-agents, or accessing 
memory when necessary. Be clear and concise in your responses.
"""


class RadBotAgent:
    """
    Main agent class for the RadBot framework.
    
    This class encapsulates the ADK agent, runner, and session management.
    It provides a unified interface for interacting with the agent system.
    """
    
    def __init__(
        self,
        session_service: Optional[SessionService] = None,
        tools: Optional[List[Any]] = None,
        model: Optional[str] = None,
        name: str = "main_coordinator",
        instruction: Optional[str] = None,
        instruction_name: Optional[str] = "main_agent",
        config: Optional[ConfigManager] = None,
        memory_service: Optional[Any] = None
    ):
        """
        Initialize the RadBot agent.
        
        Args:
            session_service: Optional custom session service for conversation state
            tools: Optional list of tools to provide to the agent
            model: Optional model name (defaults to config's main_model if not provided)
            name: Name for the agent (default: main_coordinator)
            instruction: Optional explicit instruction string (overrides instruction_name)
            instruction_name: Optional name of instruction to load from config
            config: Optional ConfigManager instance (uses global if not provided)
            memory_service: Optional custom memory service (tries to create one if None)
        """
        # Use provided config or default
        self.config = config or config_manager
        
        # Use provided session service or create an in-memory one
        self.session_service = session_service or InMemorySessionService()
        
        # Store app_name for use with session service
        self.app_name = "beto"  # Changed from "radbot" to match agent name
        
        # Determine the model to use
        self.model = model or self.config.get_main_model()
        
        # Determine instruction to use
        self.instruction_name = instruction_name
        if instruction:
            # Use explicitly provided instruction
            agent_instruction = instruction
        elif instruction_name:
            # Try to load from config, fall back to default if not found
            try:
                agent_instruction = self.config.get_instruction(instruction_name)
            except FileNotFoundError:
                # Log a warning and use fallback instruction
                import logging
                logging.warning(f"Instruction '{instruction_name}' not found, using fallback")
                agent_instruction = FALLBACK_INSTRUCTION
        else:
            # No instruction or name provided, use fallback
            agent_instruction = FALLBACK_INSTRUCTION
        
        # Create the main agent
        self.root_agent = Agent(
            name=name,
            model=self.model,
            instruction=agent_instruction,
            description="The main coordinating agent that handles user requests and orchestrates tasks.",
            tools=tools or []  # Start with empty tools list if none provided
        )
        
        # Set up memory service if needed
        self._memory_service = memory_service
        if self._memory_service is None and any(tool.__name__ in ['search_past_conversations', 'store_important_information'] 
                                               for tool in (tools or []) if hasattr(tool, '__name__')):
            # Try to create memory service if memory tools are included but no service provided
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.info("Memory tools detected, trying to create memory service")
                
                from radbot.memory.qdrant_memory import QdrantMemoryService
                self._memory_service = QdrantMemoryService()
                logger.info("Successfully created QdrantMemoryService")
            except Exception as e:
                logger.warning(f"Failed to create memory service: {str(e)}")
                logger.warning("Memory tools will not function properly without a memory service")
        
        # Initialize the runner with the agent and memory service if available
        if self._memory_service:
            self.runner = Runner(
                agent=self.root_agent,
                session_service=self.session_service,
                memory_service=self._memory_service
            )
            import logging
            logging.getLogger(__name__).info("Runner initialized with memory service")
        else:
            self.runner = Runner(
                agent=self.root_agent,
                app_name=self.app_name,  # Use self.app_name for consistency
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
        # Import logging and other necessary modules
        import logging
        from google.genai.types import Content, Part
        
        logger = logging.getLogger(__name__)
        
        # Log available tools to help debug
        if self.root_agent and self.root_agent.tools:
            tool_names = []
            for tool in self.root_agent.tools:
                tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool))
                tool_names.append(tool_name)
            
            logger.info(f"Processing message with {len(tool_names)} available tools: {', '.join(tool_names[:10])}...")
            
            # Specifically check for Home Assistant tools
            has_tools = [t for t in tool_names if t.startswith('Hass')]
            if has_tools:
                logger.info(f"Home Assistant tools available: {', '.join(has_tools)}")
            else:
                logger.warning("No Home Assistant tools found in the agent!")
        else:
            logger.warning("No tools available to the agent!")
        
        try:
            # Get or create a session with a stable session ID derived from user_id
            session_id = f"session_{user_id[:8]}"
            logger.info(f"Using session ID: {session_id}")
            
            try:
                session = self.session_service.get_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                if not session:
                    session = self.session_service.create_session(
                        app_name=self.app_name,
                        user_id=user_id,
                        session_id=session_id
                    )
                    logger.info(f"Created new session for user {user_id} with ID {session_id}")
                else:
                    logger.info(f"Using existing session for user {user_id} with ID {session_id}")
            except Exception as session_error:
                logger.warning(f"Error getting/creating session: {str(session_error)}. Creating new session.")
                session = self.session_service.create_session(
                    app_name=self.app_name,
                    user_id=user_id,
                    session_id=session_id
                )
                logger.info(f"Created new session for user {user_id} with ID {session_id}")
            
            # Create Content object with the user's message
            user_message = Content(
                parts=[Part(text=message)],
                role="user"
            )
            
            # Use the runner to process the message
            logger.info(f"Running agent with message: {message[:50]}{'...' if len(message) > 50 else ''}")
            events = list(self.runner.run(
                user_id=user_id,
                session_id=session.id,  # Include the session ID
                new_message=user_message
            ))
            
            # Extract the agent's text response from the events
            logger.info(f"Received {len(events)} events from runner")
            
            # Find the final response event
            final_response = None
            for event in events:
                # Log the event type for debugging
                logger.debug(f"Event type: {type(event).__name__}")
                
                # Method 1: Check if it's a final response
                if hasattr(event, 'is_final_response') and event.is_final_response():
                    logger.debug("Found final response event")
                    if hasattr(event, 'content') and event.content:
                        if hasattr(event.content, 'parts') and event.content.parts:
                            for part in event.content.parts:
                                if hasattr(part, 'text') and part.text:
                                    final_response = part.text
                                    break
                                
                # Method 2: Check for content directly
                if final_response is None and hasattr(event, 'content'):
                    logger.debug("Checking event.content for text")
                    if hasattr(event.content, 'text') and event.content.text:
                        final_response = event.content.text
                        
                # Method 3: Check for message attribute
                if final_response is None and hasattr(event, 'message'):
                    logger.debug("Checking event.message for content")
                    if hasattr(event.message, 'content'):
                        final_response = event.message.content
                        
                # Break once we have a final response
                if final_response:
                    break
            
            if final_response:
                return final_response
            else:
                logger.warning("No text response found in events")
                return "I apologize, but I couldn't generate a response."
                
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            return f"I apologize, but I encountered an error processing your message. Please try again. Error: {str(e)}"

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
    
    def get_configuration(self) -> Dict[str, Any]:
        """
        Get the current configuration of the agent.
        
        Returns:
            Dictionary containing the agent's configuration
        """
        return {
            "name": self.root_agent.name,
            "model": self.root_agent.model,
            "instruction_name": self.instruction_name,
            "tools_count": len(self.root_agent.tools) if self.root_agent.tools else 0,
            "sub_agents_count": len(self.root_agent.sub_agents) if self.root_agent.sub_agents else 0,
        }
    
    def update_instruction(self, new_instruction: str = None, instruction_name: str = None) -> None:
        """
        Update the agent's instruction.
        
        Args:
            new_instruction: The new instruction to set directly
            instruction_name: Name of instruction to load from config
            
        Raises:
            ValueError: If neither new_instruction nor instruction_name is provided
            FileNotFoundError: If instruction_name is provided but not found in config
        """
        if new_instruction:
            self.root_agent.instruction = new_instruction
            self.instruction_name = None
        elif instruction_name:
            try:
                self.root_agent.instruction = self.config.get_instruction(instruction_name)
                self.instruction_name = instruction_name
            except FileNotFoundError as e:
                raise FileNotFoundError(f"Instruction '{instruction_name}' not found in config") from e
        else:
            raise ValueError("Either new_instruction or instruction_name must be provided")
    
    def update_model(self, new_model: str) -> None:
        """
        Update the agent's model.
        
        Args:
            new_model: The new model to use (e.g., "gemini-2.5-pro", "gemini-2.0-flash")
        """
        self.root_agent.model = new_model
        self.model = new_model
    
    def reset_session(self, user_id: str) -> None:
        """
        Reset a user's session.
        
        Args:
            user_id: The user ID to reset
        """
        # Generate a stable session ID from user_id
        session_id = f"session_{user_id[:8]}"
        
        try:
            # Delete the specific session
            self.session_service.delete_session(
                app_name=self.app_name,
                user_id=user_id,
                session_id=session_id
            )
            import logging
            logging.getLogger(__name__).info(f"Reset session for user {user_id} with ID {session_id}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Error resetting session: {str(e)}")


class AgentFactory:
    """Factory class for creating and configuring agents."""

    @staticmethod
    def create_root_agent(
        name: str = "main_coordinator",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        instruction_name: str = "main_agent",
        config: Optional[ConfigManager] = None
    ) -> Agent:
        """Create the main root agent.

        Args:
            name: Name of the agent
            model: Model to use (if None, uses config's main_model)
            tools: List of tools to add to the agent
            instruction_name: Name of the instruction to load from config
            config: Optional ConfigManager instance (uses global if not provided)

        Returns:
            Configured root agent
        """
        # Use provided config or default
        cfg = config or config_manager
        
        # Get the model name
        model_name = model or cfg.get_main_model()
        
        # Get the instruction
        try:
            instruction = cfg.get_instruction(instruction_name)
        except FileNotFoundError:
            # Fall back to default instruction
            instruction = FALLBACK_INSTRUCTION
        
        # Create the root agent
        root_agent = Agent(
            name=name,
            model=model_name,
            instruction=instruction,
            description="The main coordinating agent that handles user requests and orchestrates tasks.",
            tools=tools or [],  # Initialize with provided tools or empty list
        )

        return root_agent

    @staticmethod
    def create_sub_agent(
        name: str,
        description: str,
        instruction_name: str,
        tools: Optional[List] = None,
        model: Optional[str] = None,
        config: Optional[ConfigManager] = None
    ) -> Agent:
        """Create a sub-agent with appropriate model and configuration.

        Args:
            name: Name of the sub-agent
            description: Description of the sub-agent's capabilities
            instruction_name: Name of the instruction to load from config
            tools: List of tools to add to the agent
            model: Optional model override (if None, uses config's sub_agent_model)
            config: Optional ConfigManager instance (uses global if not provided)

        Returns:
            Configured sub-agent
        """
        # Use provided config or default
        cfg = config or config_manager
        
        # Get the model name (use sub-agent model by default)
        model_name = model or cfg.get_sub_agent_model()
        
        # Get the instruction
        try:
            instruction = cfg.get_instruction(instruction_name)
        except FileNotFoundError:
            # Use a minimal instruction if the named one isn't found
            import logging
            logging.warning(f"Instruction '{instruction_name}' not found for sub-agent, using minimal instruction")
            instruction = f"You are a specialized {name} agent. {description}"
        
        # Create the sub-agent
        sub_agent = Agent(
            name=name,
            model=model_name,
            instruction=instruction,
            description=description,
            tools=tools or [],
        )

        return sub_agent


def create_runner(
    agent: Agent, 
    app_name: str = "beto",  # Changed from "radbot" to match agent name
    session_service: Optional[SessionService] = None
) -> Runner:
    """Create an ADK Runner with the specified agent.

    Args:
        agent: The agent to run
        app_name: Name of the application
        session_service: Optional custom session service

    Returns:
        Configured runner
    """
    # Use provided session service or create an in-memory one
    sess_service = session_service or InMemorySessionService()
    
    # Make sure the session service knows about the app_name
    # This is for internal reference, as methods like get_session and create_session
    # require app_name as a parameter
    
    # Create and return the runner
    return Runner(
        agent=agent,
        app_name=app_name,
        session_service=sess_service
    )


def create_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    model: Optional[str] = None,
    instruction_name: str = "main_agent",
    name: str = "main_coordinator",
    config: Optional[ConfigManager] = None,
    include_memory_tools: bool = True
) -> RadBotAgent:
    """
    Create a configured RadBot agent.
    
    Args:
        session_service: Optional session service for conversation state
        tools: Optional list of tools for the agent
        model: Optional model to use (defaults to config's main_model)
        instruction_name: Name of instruction to load from config
        name: Name for the agent
        config: Optional ConfigManager instance (uses global if not provided)
        include_memory_tools: If True, includes memory tools automatically
        
    Returns:
        A configured RadBotAgent instance
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Start with the given tools or empty list
    all_tools = list(tools or [])
    
    # Include memory tools if requested
    if include_memory_tools:
        try:
            from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
            memory_tools = [search_past_conversations, store_important_information]
            
            # Add memory tools if they're not already included
            memory_tool_names = set([tool.__name__ for tool in memory_tools])
            existing_tool_names = set()
            for tool in all_tools:
                if hasattr(tool, '__name__'):
                    existing_tool_names.add(tool.__name__)
                elif hasattr(tool, 'name'):
                    existing_tool_names.add(tool.name)
            
            # Add any missing memory tools
            for tool in memory_tools:
                if tool.__name__ not in existing_tool_names:
                    all_tools.append(tool)
                    logger.info(f"Explicitly adding memory tool: {tool.__name__}")
        except Exception as e:
            logger.warning(f"Failed to add memory tools: {str(e)}")
    
    # Create the agent with all the specified parameters
    agent = RadBotAgent(
        session_service=session_service,
        tools=all_tools,
        model=model,
        name=name,
        instruction_name=instruction_name,
        config=config
    )
    
    # Log the tools included in the agent
    if agent.root_agent and agent.root_agent.tools:
        tool_names = []
        for tool in agent.root_agent.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            elif hasattr(tool, 'name'):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(type(tool)))
        logger.info(f"Agent created with tools: {', '.join(tool_names)}")
    
    return agent
