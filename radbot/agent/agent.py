"""
Core agent implementation for RadBot.

This module defines the essential RadBotAgent class and factory functions for the RadBot framework.
It serves as the single source of truth for all agent functionality.
"""
import os
import logging
from typing import Any, Dict, List, Optional, Union

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
from google.protobuf.json_format import MessageToDict
# Note: In ADK 0.4.0, agent transfers use transfer_to_agent directly without QueryResponse

# Configure logging
logger = logging.getLogger(__name__)

# Type alias for backward compatibility
SessionService = InMemorySessionService  

# Load environment variables
load_dotenv()

# Import our configuration modules
from radbot.config import config_manager
from radbot.config.settings import ConfigManager

# Import our ADK configuration setup to handle Vertex AI settings
from radbot.config.adk_config import setup_vertex_environment

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
        name: str = "beto",
        instruction: Optional[str] = None,
        instruction_name: Optional[str] = "main_agent",
        config: Optional[ConfigManager] = None,
        memory_service: Optional[Any] = None,
        app_name: str = "beto"
    ):
        """
        Initialize the RadBot agent.
        
        Args:
            session_service: Optional custom session service for conversation state
            tools: Optional list of tools to provide to the agent
            model: Optional model name (defaults to config's main_model if not provided)
            name: Name for the agent (default: beto)
            instruction: Optional explicit instruction string (overrides instruction_name)
            instruction_name: Optional name of instruction to load from config
            config: Optional ConfigManager instance (uses global if not provided)
            memory_service: Optional custom memory service (tries to create one if None)
            app_name: Application name for session management (default: beto)
        """
        # Use provided config or default
        self.config = config or config_manager
        
        # Use provided session service or create an in-memory one
        self.session_service = session_service or InMemorySessionService()
        
        # Store app_name for use with session service
        self.app_name = app_name
        
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
                logger.warning(f"Instruction '{instruction_name}' not found, using fallback")
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
            logger.info("Runner initialized with memory service")
        else:
            self.runner = Runner(
                agent=self.root_agent,
                app_name=self.app_name,
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
        # Log available tools to help debug
        if self.root_agent and self.root_agent.tools:
            tool_names = []
            for tool in self.root_agent.tools:
                tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', str(tool))
                tool_names.append(tool_name)
            
            logger.info(f"Processing message with {len(tool_names)} available tools: {', '.join(tool_names[:10])}...")
            
            # Specifically check for Home Assistant tools
            ha_tools = [t for t in tool_names if t.startswith('Hass') or "ha_" in t.lower()]
            if ha_tools:
                logger.info(f"Home Assistant tools available: {', '.join(ha_tools)}")
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
        
        # Set bidirectional relationships for agent transfers
        if hasattr(sub_agent, 'parent'):
            sub_agent.parent = self.root_agent
        elif hasattr(sub_agent, '_parent'):
            sub_agent._parent = self.root_agent
            
        logger.info(f"Added sub-agent '{sub_agent.name if hasattr(sub_agent, 'name') else 'unnamed'}' to agent '{self.root_agent.name}'")
    
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
            logger.info(f"Reset session for user {user_id} with ID {session_id}")
        except Exception as e:
            logger.warning(f"Error resetting session: {str(e)}")
    
    def register_tool_handlers(self):
        """Register common tool handlers for the agent."""
        # Only proceed if the agent has register_tool_handler method
        if not hasattr(self.root_agent, 'register_tool_handler'):
            logger.warning("Agent does not support tool handler registration")
            return
            
        try:
            # Import needed components
            from radbot.tools.mcp.mcp_fileserver_client import handle_fileserver_tool_call
            from radbot.tools.crawl4ai.mcp_crawl4ai_client import handle_crawl4ai_tool_call
            from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
            
            # Register filesystem tool handlers
            self.root_agent.register_tool_handler(
                "list_files", lambda params: handle_fileserver_tool_call("list_files", params)
            )
            self.root_agent.register_tool_handler(
                "read_file", lambda params: handle_fileserver_tool_call("read_file", params)
            )
            self.root_agent.register_tool_handler(
                "write_file", lambda params: handle_fileserver_tool_call("write_file", params)
            )
            self.root_agent.register_tool_handler(
                "delete_file", lambda params: handle_fileserver_tool_call("delete_file", params)
            )
            self.root_agent.register_tool_handler(
                "get_file_info",
                lambda params: handle_fileserver_tool_call("get_file_info", params),
            )
            self.root_agent.register_tool_handler(
                "search_files", lambda params: handle_fileserver_tool_call("search_files", params)
            )
            self.root_agent.register_tool_handler(
                "create_directory",
                lambda params: handle_fileserver_tool_call("create_directory", params),
            )
            
            # Register Crawl4AI tool handlers
            self.root_agent.register_tool_handler(
                "crawl4ai_scrape",
                lambda params: handle_crawl4ai_tool_call("crawl4ai_scrape", params),
            )
            self.root_agent.register_tool_handler(
                "crawl4ai_search",
                lambda params: handle_crawl4ai_tool_call("crawl4ai_search", params),
            )
            self.root_agent.register_tool_handler(
                "crawl4ai_extract",
                lambda params: handle_crawl4ai_tool_call("crawl4ai_extract", params),
            )
            self.root_agent.register_tool_handler(
                "crawl4ai_crawl",
                lambda params: handle_crawl4ai_tool_call("crawl4ai_crawl", params),
            )
            
            # Register memory tools
            self.root_agent.register_tool_handler(
                "search_past_conversations",
                lambda params: MessageToDict(search_past_conversations(params)),
            )
            self.root_agent.register_tool_handler(
                "store_important_information",
                lambda params: MessageToDict(store_important_information(params)),
            )
            
            # In ADK 0.4.0, agent transfers are handled differently
            # No need to explicitly register transfer_to_agent handler
            logger.info("Using ADK 0.4.0 native agent transfer functionality")
            
            logger.info("Registered common tool handlers for agent")
        except Exception as e:
            logger.warning(f"Error registering tool handlers: {str(e)}")


class AgentFactory:
    """Factory class for creating and configuring agents."""

    @staticmethod
    def create_root_agent(
        name: str = "beto",
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
            logger.warning(f"Instruction '{instruction_name}' not found for sub-agent, using minimal instruction")
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

    @staticmethod
    def create_web_agent(
        name: str = "beto",
        model: Optional[str] = None,
        tools: Optional[List] = None,
        instruction_name: str = "main_agent",
        config: Optional[ConfigManager] = None,
        register_tools: bool = True
    ) -> Agent:
        """Create an agent specifically for the ADK web interface.
        
        Args:
            name: Name of the agent
            model: Model to use (if None, uses config's main_model)
            tools: List of tools to add to the agent
            instruction_name: Name of the instruction to load from config
            config: Optional ConfigManager instance (uses global if not provided)
            register_tools: Whether to register common tool handlers
            
        Returns:
            Configured ADK Agent for web interface
        """
        # Create the base agent
        agent = AgentFactory.create_root_agent(
            name=name,
            model=model,
            tools=tools,
            instruction_name=instruction_name,
            config=config
        )
        
        # Initialize memory service for the web UI and store API keys
        try:
            from radbot.memory.qdrant_memory import QdrantMemoryService
            memory_service = QdrantMemoryService()
            logger.info("Successfully initialized QdrantMemoryService for web agent")
            
            # Store memory service in ADK's global tool context
            from google.adk.tools.tool_context import ToolContext
            
            # Directly use setattr to add memory service to tool context
            # This makes it accessible in tool implementations
            setattr(ToolContext, "memory_service", memory_service)
            logger.info("Added memory service to tool context")
            
            # Store API keys in ToolContext for tools to access
            tavily_api_key = os.environ.get("TAVILY_API_KEY")
            if tavily_api_key:
                setattr(ToolContext, "tavily_api_key", tavily_api_key)
                logger.info("Stored Tavily API key in global ToolContext")
                
            # Store Crawl4AI API key if available
            crawl4ai_api_token = os.environ.get("CRAWL4AI_API_TOKEN")
            if crawl4ai_api_token:
                setattr(ToolContext, "crawl4ai_api_token", crawl4ai_api_token)
                logger.info("Stored Crawl4AI API token in global ToolContext")
        except Exception as e:
            logger.warning(f"Failed to initialize memory service: {str(e)}")
        
        # Register common tool handlers if requested
        if register_tools:
            try:
                # Use the equivalent of RadBotAgent.register_tool_handlers but for a plain Agent
                from radbot.tools.mcp.mcp_fileserver_client import handle_fileserver_tool_call
                from radbot.tools.crawl4ai.mcp_crawl4ai_client import handle_crawl4ai_tool_call
                from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
                
                # Register filesystem tool handlers
                agent.register_tool_handler(
                    "list_files", lambda params: handle_fileserver_tool_call("list_files", params)
                )
                agent.register_tool_handler(
                    "read_file", lambda params: handle_fileserver_tool_call("read_file", params)
                )
                agent.register_tool_handler(
                    "write_file", lambda params: handle_fileserver_tool_call("write_file", params)
                )
                agent.register_tool_handler(
                    "delete_file", lambda params: handle_fileserver_tool_call("delete_file", params)
                )
                agent.register_tool_handler(
                    "get_file_info",
                    lambda params: handle_fileserver_tool_call("get_file_info", params),
                )
                agent.register_tool_handler(
                    "search_files", lambda params: handle_fileserver_tool_call("search_files", params)
                )
                agent.register_tool_handler(
                    "create_directory",
                    lambda params: handle_fileserver_tool_call("create_directory", params),
                )
                
                # Register Crawl4AI tool handlers
                agent.register_tool_handler(
                    "crawl4ai_scrape",
                    lambda params: handle_crawl4ai_tool_call("crawl4ai_scrape", params),
                )
                agent.register_tool_handler(
                    "crawl4ai_search",
                    lambda params: handle_crawl4ai_tool_call("crawl4ai_search", params),
                )
                agent.register_tool_handler(
                    "crawl4ai_extract",
                    lambda params: handle_crawl4ai_tool_call("crawl4ai_extract", params),
                )
                agent.register_tool_handler(
                    "crawl4ai_crawl",
                    lambda params: handle_crawl4ai_tool_call("crawl4ai_crawl", params),
                )
                
                # Register memory tools
                agent.register_tool_handler(
                    "search_past_conversations",
                    lambda params: MessageToDict(search_past_conversations(params)),
                )
                agent.register_tool_handler(
                    "store_important_information",
                    lambda params: MessageToDict(store_important_information(params)),
                )
                
                # In ADK 0.4.0, agent transfers are handled natively
                # No need to register custom transfer_to_agent handler
                
                logger.info("Registered common tool handlers for web agent")
            except Exception as e:
                logger.warning(f"Error registering tool handlers for web agent: {str(e)}")
                
        return agent


def create_runner(
    agent: Agent, 
    app_name: str = "beto",
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
    name: str = "beto",
    config: Optional[ConfigManager] = None,
    include_memory_tools: bool = True,
    include_google_search: bool = False,
    include_code_execution: bool = False,
    for_web: bool = False,
    register_tools: bool = True,
    app_name: str = "beto"
) -> Union[RadBotAgent, Agent]:
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
        include_google_search: If True, register a google_search sub-agent
        include_code_execution: If True, register a code_execution sub-agent
        for_web: If True, returns an ADK Agent for web interface
        register_tools: Whether to register common tool handlers
        app_name: Application name for session management
        
    Returns:
        A configured RadBotAgent instance or ADK Agent for web interface
    """
    logger.info(f"Creating agent (for_web={for_web}, name={name})")
    
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
    
    # For web interface, use AgentFactory to create an ADK Agent directly
    if for_web:
        agent = AgentFactory.create_web_agent(
            name=name,
            model=model,
            tools=all_tools,
            instruction_name=instruction_name,
            config=config,
            register_tools=register_tools
        )
        logger.info(f"Created web agent with {len(all_tools)} tools")
        
        # Add built-in tool agents if requested
        if include_google_search or include_code_execution:
            try:
                from radbot.tools.adk_builtin import register_search_agent, register_code_execution_agent
                
                if include_google_search:
                    try:
                        register_search_agent(agent)
                        logger.info(f"Registered Google Search agent with parent {name}")
                    except Exception as e:
                        logger.warning(f"Failed to register search agent: {str(e)}")
                
                if include_code_execution:
                    try:
                        register_code_execution_agent(agent)
                        logger.info(f"Registered Code Execution agent with parent {name}")
                    except Exception as e:
                        logger.warning(f"Failed to register code execution agent: {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to import built-in tool factories: {str(e)}")
        
        return agent
    
    # Otherwise, create a RadBotAgent instance
    agent = RadBotAgent(
        session_service=session_service,
        tools=all_tools,
        model=model,
        name=name,
        instruction_name=instruction_name,
        config=config,
        app_name=app_name
    )
    
    # Register tool handlers if requested
    if register_tools:
        agent.register_tool_handlers()
    
    # Add built-in tool agents if requested
    if include_google_search or include_code_execution:
        try:
            from radbot.tools.adk_builtin import register_search_agent, register_code_execution_agent
            
            if include_google_search:
                try:
                    # For ADK 0.4.0, we need to properly register the agent in the tree
                    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
                    from radbot.tools.adk_builtin.search_tool import create_search_agent
                    
                    # First create the search agent
                    search_agent = create_search_agent(
                        name="search_agent",
                        model=model,
                        config=config
                    )
                    
                    # Use the proper ADK agent.add_sub_agent method to register it
                    if hasattr(agent.root_agent, 'add_sub_agent'):
                        agent.root_agent.add_sub_agent(search_agent)
                        logger.info(f"Registered search_agent using add_sub_agent method for ADK 0.4.0 compatibility")
                    elif hasattr(agent.root_agent, 'sub_agents'):
                        # Fallback: add to sub_agents list manually
                        if not any(sa.name == "search_agent" for sa in agent.root_agent.sub_agents if hasattr(sa, 'name')):
                            agent.root_agent.sub_agents.append(search_agent)
                            logger.info(f"Added search_agent to root_agent.sub_agents list")
                    else:
                        # Last resort: use the register function
                        register_search_agent(agent.root_agent)
                        logger.info(f"Registered Google Search agent with parent {name} using register function")
                except Exception as e:
                    logger.warning(f"Failed to register search agent: {str(e)}")
            
            if include_code_execution:
                try:
                    # For ADK 0.4.0, we need to properly register the agent in the tree
                    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
                    from radbot.tools.adk_builtin.code_execution_tool import create_code_execution_agent
                    
                    # First create the code execution agent
                    code_agent = create_code_execution_agent(
                        name="code_execution_agent",
                        model=model,
                        config=config
                    )
                    
                    # Use the proper ADK agent.add_sub_agent method to register it
                    if hasattr(agent.root_agent, 'add_sub_agent'):
                        agent.root_agent.add_sub_agent(code_agent)
                        logger.info(f"Registered code_execution_agent using add_sub_agent method for ADK 0.4.0 compatibility")
                    elif hasattr(agent.root_agent, 'sub_agents'):
                        # Fallback: add to sub_agents list manually
                        if not any(sa.name == "code_execution_agent" for sa in agent.root_agent.sub_agents if hasattr(sa, 'name')):
                            agent.root_agent.sub_agents.append(code_agent)
                            logger.info(f"Added code_execution_agent to root_agent.sub_agents list")
                    else:
                        # Last resort: use the register function
                        register_code_execution_agent(agent.root_agent)
                        logger.info(f"Registered Code Execution agent with parent {name} using register function")
                except Exception as e:
                    logger.warning(f"Failed to register code execution agent: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to import built-in tool factories: {str(e)}")
    
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
        logger.info(f"Created RadBotAgent with tools: {', '.join(tool_names)}")
    
    return agent


def create_core_agent_for_web(
    tools: Optional[List[Any]] = None, 
    name: str = "beto", 
    app_name: str = "beto",
    include_google_search: bool = False,
    include_code_execution: bool = False
) -> Agent:
    """
    Create an ADK Agent for web interface with all necessary configurations.
    
    Args:
        tools: Optional list of tools to include
        name: Name for the agent (must be "beto" for consistent transfers)
        app_name: Application name (must match agent name for ADK 0.4.0+)
        include_google_search: If True, register a google_search sub-agent
        include_code_execution: If True, register a code_execution sub-agent
        
    Returns:
        Configured ADK Agent for web interface
    """
    # Ensure agent name is always "beto" for consistent transfers
    if name != "beto":
        logger.warning(f"Agent name '{name}' changed to 'beto' for consistent transfers")
        name = "beto"
        
    # Ensure app_name matches agent name for ADK 0.4.0+
    if app_name != name:
        logger.warning(f"app_name '{app_name}' changed to '{name}' for ADK 0.4.0+ compatibility")
        app_name = name
        
    # Create the base agent with proper name and app_name
    agent = AgentFactory.create_web_agent(
        name=name,
        model=None,  # Will use config default
        tools=tools,
        instruction_name="main_agent",
        config=None,  # Will use global config
        register_tools=True
    )
    
    # Import required components for agent transfers
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Ensure agent has transfer_to_agent tool
    if hasattr(agent, 'tools'):
        # Check if tool already exists
        has_transfer_tool = False
        for tool in agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
            if tool_name == 'transfer_to_agent':
                has_transfer_tool = True
                break
                
        if not has_transfer_tool:
            agent.tools.append(transfer_to_agent)
            logger.info("Added transfer_to_agent tool to root agent")
    
    # Create sub-agents if requested
    sub_agents = []
    
    # Add built-in tool agents if requested
    if include_google_search or include_code_execution:
        try:
            from radbot.tools.adk_builtin import create_search_agent, create_code_execution_agent
            
            if include_google_search:
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
                    logger.info("Created search_agent as sub-agent")
                except Exception as e:
                    logger.warning(f"Failed to create search agent: {str(e)}")
            
            if include_code_execution:
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
                    logger.info("Created code_execution_agent as sub-agent")
                except Exception as e:
                    logger.warning(f"Failed to create code execution agent: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to import built-in tool factories: {str(e)}")
    
    # Create scout agent if needed
    try:
        from radbot.agent.research_agent import create_research_agent
        
        # Pass the same settings to create consistent behavior
        scout_agent = create_research_agent(
            name="scout",  # MUST be "scout" for consistent transfers
            model=None,  # Will use config default
            tools=tools,  # Pass the same tools as the root agent
            as_subagent=False,  # Get the ADK agent directly
            enable_google_search=include_google_search,
            enable_code_execution=include_code_execution,
            app_name=app_name  # Same app_name for consistency
        )
        
        # Add to sub-agents
        sub_agents.append(scout_agent)
        logger.info("Added scout agent as sub-agent")
    except Exception as e:
        logger.warning(f"Failed to create scout agent: {str(e)}")
    
    # Set sub-agents list on the agent
    if sub_agents:
        agent.sub_agents = sub_agents
        logger.info(f"Added {len(sub_agents)} sub-agents to root agent")
        
        # Log the agent tree for debugging
        sub_agent_names = [sa.name for sa in agent.sub_agents if hasattr(sa, 'name')]
        logger.info(f"Agent tree: root='{agent.name}', sub_agents={sub_agent_names}")
    
    return agent