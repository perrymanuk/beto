"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
The ADK web interface uses this file directly based on the adk.config.json setting.
"""

import asyncio
import logging
import os
import sys
from typing import Optional, Any, List, Dict, Union

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
from radbot.config import config_manager
# Import the ADK's built-in transfer_to_agent tool
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
# Import calendar tools
from radbot.tools.calendar.calendar_tools import (
    list_calendar_events_tool,
    create_calendar_event_tool,
    update_calendar_event_tool,
    delete_calendar_event_tool,
    check_calendar_availability_tool
)

# Log configuration
logger.info(f"Config manager loaded. Model config: {config_manager.model_config}")
logger.info(f"Main model from config: '{config_manager.get_main_model()}'")
logger.info(f"Environment RADBOT_MAIN_MODEL: '{os.environ.get('RADBOT_MAIN_MODEL')}'")
logger.info(f"Using Vertex AI: {config_manager.is_using_vertex_ai()}")

# Import tools
from radbot.tools.basic import get_current_time, get_weather
from radbot.tools.memory import search_past_conversations, store_important_information
from radbot.tools.web_search import create_tavily_search_tool
from radbot.tools.mcp import create_fileserver_toolset
from radbot.tools.mcp import create_crawl4ai_toolset, test_crawl4ai_connection
from radbot.tools.shell import get_shell_tool  # ADK-compatible tool function
from radbot.tools.todo import ALL_TOOLS, init_database  # Todo tools

# Import Home Assistant REST API tools
from radbot.tools.homeassistant import (
    list_ha_entities,
    get_ha_entity_state,
    turn_on_ha_entity,
    turn_off_ha_entity,
    toggle_ha_entity,
    search_ha_entities  # Use our direct implementation
)

# Ensure the Home Assistant client is properly initialized
from radbot.tools.homeassistant import get_ha_client

# Import Home Assistant integration
from radbot.agent.home_assistant_agent_factory import create_home_assistant_agent_factory
from radbot.config.settings import ConfigManager

# Import Research Agent
from radbot.agent.research_agent import create_research_agent

# Log startup
logger.info("ROOT agent.py loaded - this is the main implementation loaded by ADK web")
print(f"SPECIAL DEBUG: agent.py loaded with MCP_FS_ROOT_DIR={os.environ.get('MCP_FS_ROOT_DIR', 'Not set')}")

# We're using REST API approach for Home Assistant


def create_agent(tools: Optional[List[Any]] = None):
    """
    Create the agent with all necessary tools.
    
    This is the entry point used by ADK web to create the agent.
    
    Args:
        tools: Optional list of additional tools to include
        
    Returns:
        An ADK BaseAgent instance
    """
    logger.info("Creating agent for ADK web interface")
    
    # Start with basic tools - added back get_weather as requested
    basic_tools = [get_current_time, get_weather]
    
    # Add calendar tools
    calendar_tools = [
        list_calendar_events_tool,
        create_calendar_event_tool,
        update_calendar_event_tool,
        delete_calendar_event_tool,
        check_calendar_availability_tool
    ]
    logger.info(f"Adding calendar tools")
    basic_tools.extend(calendar_tools)
    
    # Always include memory tools
    memory_tools = [search_past_conversations, store_important_information]
    logger.info(f"Including memory tools: {[t.__name__ for t in memory_tools]}")
    
    # Initialize Todo Database
    try:
        logger.info("Initializing Todo database schema...")
        init_database()
        logger.info("Todo database schema initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Todo database: {str(e)}")
        logger.error("Todo functionality will not be available")
    
    # Add Home Assistant REST API integration
    logger.info("Using Home Assistant REST API integration in agent creation")
    
    # Initialize Home Assistant client
    ha_client = get_ha_client()
    if ha_client:
        logger.info(f"Home Assistant client initialized: {ha_client.base_url}")
        
        # Test connection by listing entities
        try:
            entities = ha_client.list_entities()
            if entities:
                logger.info(f"Successfully connected to Home Assistant. Found {len(entities)} entities.")
            else:
                logger.warning("Connected to Home Assistant but no entities were returned")
        except Exception as e:
            logger.error(f"Error testing Home Assistant connection: {e}")
    else:
        logger.warning("Home Assistant client could not be initialized - check HA_URL and HA_TOKEN")
    
    # Add Home Assistant REST API tools
    ha_tools = [
        search_ha_entities,
        list_ha_entities,
        get_ha_entity_state,
        turn_on_ha_entity,
        turn_off_ha_entity,
        toggle_ha_entity
    ]
    basic_tools.extend(ha_tools)
    logger.info(f"Added {len(ha_tools)} Home Assistant REST API tools")
    
    # Add Direct Filesystem tools (previously used MCP Fileserver)
    try:
        # Print filesystem configuration
        mcp_fs_root_dir = os.environ.get("MCP_FS_ROOT_DIR")
        if mcp_fs_root_dir:
            logger.info(f"Filesystem: Using root directory {mcp_fs_root_dir}")
            print(f"SPECIAL DEBUG: MCP_FS_ROOT_DIR={mcp_fs_root_dir}")  # Will print even in subprocess
        else:
            logger.info("Filesystem: Root directory not set (MCP_FS_ROOT_DIR not found in environment)")
            print("SPECIAL DEBUG: MCP_FS_ROOT_DIR not set")  # Will print even in subprocess
            
        logger.info("Creating filesystem tools using direct implementation...")
        print("SPECIAL DEBUG: About to call create_fileserver_toolset() [direct implementation]")  # Will print even in subprocess
        fs_tools = create_fileserver_toolset()
        if fs_tools:
            # Log detailed information about each filesystem tool
            logger.debug(f"Direct filesystem implementation returned {len(fs_tools)} tools")
            for i, tool in enumerate(fs_tools):
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_type = type(tool).__name__
                logger.debug(f"  FS Tool {i+1}: {tool_name} (type: {tool_type})")
            
            # fs_tools is now a list of tools, so extend basic_tools with it
            basic_tools.extend(fs_tools)
            
            # Log tools individually for better debugging
            fs_tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in fs_tools]
            logger.info(f"Successfully added {len(fs_tools)} filesystem tools: {', '.join(fs_tool_names)}")
        else:
            logger.warning("Filesystem tools not available (returned None)")
            
        logger.info("NOTE: Using direct filesystem implementation (no MCP server required)")
        print("SPECIAL DEBUG: Using direct filesystem implementation (no MCP server required)")

    except Exception as e:
        logger.warning(f"Failed to create filesystem tools: {str(e)}")
        logger.debug(f"Filesystem tool creation error details:", exc_info=True)
        
    # Add Crawl4AI tools
    try:
        logger.info("Creating Crawl4AI toolset...")
        # First check if we have the necessary environment variables
        crawl4ai_api_url = os.environ.get("CRAWL4AI_API_URL", "https://crawl4ai.demonsafe.com")
        
        # We'll proceed with or without a token
        logger.info(f"Crawl4AI: Using API URL {crawl4ai_api_url}")
        crawl4ai_tools = create_crawl4ai_toolset()
        
        if crawl4ai_tools:
            # Log detailed information about each Crawl4AI tool
            logger.debug(f"Crawl4AI returned {len(crawl4ai_tools)} tools")
            for i, tool in enumerate(crawl4ai_tools):
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_type = type(tool).__name__
                logger.debug(f"  Crawl4AI Tool {i+1}: {tool_name} (type: {tool_type})")
            
            # Add tools to basic_tools
            basic_tools.extend(crawl4ai_tools)
            
            # Log tools individually for better debugging
            crawl4ai_tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in crawl4ai_tools]
            logger.info(f"Successfully added {len(crawl4ai_tools)} Crawl4AI tools: {', '.join(crawl4ai_tool_names)}")
        else:
            logger.warning("Crawl4AI tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create Crawl4AI tools: {str(e)}")
        logger.debug(f"Crawl4AI tool creation error details:", exc_info=True)
    
    # Add Tavily web search tool
    try:
        web_search_tool = create_tavily_search_tool(
            max_results=3,
            search_depth="advanced",
            include_answer=True,
            include_raw_content=True
        )
        if web_search_tool:
            basic_tools.insert(0, web_search_tool)  # Add as highest priority
            logger.info("Successfully added web_search tool to base tools")
    except Exception as e:
        logger.warning(f"Failed to create Tavily search tool: {str(e)}")
        
        # If the function tool creation failed, try a simple direct function approach
        try:
            # Define a simple function without decorators
            def web_search(query: str) -> str:
                """Search the web for current information on a topic."""
                from radbot.tools.web_search import HAVE_TAVILY, TavilySearchResults
                
                logger.info(f"Running fallback web search for query: {query}")
                
                try:
                    if HAVE_TAVILY and os.environ.get("TAVILY_API_KEY"):
                        # Instantiate LangChain's Tavily search tool
                        tavily_search = TavilySearchResults(
                            max_results=3,
                            search_depth="advanced",
                            include_answer=True,
                            include_raw_content=True,
                            include_images=False,
                        )
                        # Use the tool directly
                        results = tavily_search.invoke(query)
                        return results
                    else:
                        return f"Unable to search for '{query}'. Tavily search is not available."
                except Exception as e:
                    logger.error(f"Error in fallback web_search: {str(e)}")
                    return f"Error searching for '{query}': {str(e)}"
            
            # Try to wrap it with FunctionTool
            from google.adk.tools import FunctionTool
            web_search.__name__ = "web_search"  # Ensure function name is correct for LLM
            search_tool = FunctionTool(web_search)
            basic_tools.insert(0, search_tool)
            logger.info("Added fallback web_search tool to base tools")
        except Exception as e:
            logger.error(f"Failed to create fallback web search tool: {str(e)}")
    
    # Add Shell Command Execution tool
    try:
        # Check for shell command execution flag in environment
        enable_shell = os.environ.get("RADBOT_ENABLE_SHELL", "strict").lower()
        
        if enable_shell in ["true", "1", "yes", "enable", "all", "allow"]:
            # Allow all mode (SECURITY RISK)
            logger.warning(
                "SECURITY WARNING: Adding shell command execution in ALLOW ALL mode. "
                "This allows execution of ANY command without restrictions!"
            )
            # Note: get_shell_tool now returns an ADK-compatible FunctionTool
            shell_tool = get_shell_tool(strict_mode=False)
            basic_tools.append(shell_tool)
            logger.info("Added shell command execution tool in ALLOW ALL mode")
        elif enable_shell in ["strict", "restricted", "secure"]:
            # Strict mode (only allow-listed commands)
            logger.info("Adding shell command execution tool in STRICT mode (only allow-listed commands)")
            # Note: get_shell_tool now returns an ADK-compatible FunctionTool
            shell_tool = get_shell_tool(strict_mode=True)
            basic_tools.append(shell_tool)
            logger.info("Added shell command execution tool in STRICT mode")
        else:
            logger.info("Shell command execution is disabled")
            
        # Add instruction about shell command execution if enabled
        if enable_shell in ["true", "1", "yes", "enable", "all", "allow", "strict", "restricted", "secure"]:
            shell_instruction = """
            You can execute shell commands using the execute_shell_command tool.
            
            Usage:
            - execute_shell_command(command="command_name", arguments=["arg1", "arg2"], timeout=30)
            
            Examples:
            - execute_shell_command(command="ls", arguments=["-la"])
            - execute_shell_command(command="cat", arguments=["/etc/hostname"])
            
            Always tell the user what command you're executing and what the results are.
            Never execute potentially destructive commands like rm, dd, or anything that could
            modify or delete important files.
            """
            
            if enable_shell in ["strict", "restricted", "secure"]:
                from radbot.tools.shell import ALLOWED_COMMANDS
                allowed_cmds = ", ".join(sorted(list(ALLOWED_COMMANDS)))
                shell_instruction += f"\n\nNOTE: You can only execute these allowed commands: {allowed_cmds}"
                
    except Exception as e:
        logger.warning(f"Failed to create shell command execution tool: {str(e)}")
        logger.debug(f"Shell command tool creation error details:", exc_info=True)
    
    # Add Todo Tools
    try:
        logger.info("Adding Todo tools to agent...")
        basic_tools.extend(ALL_TOOLS)
        logger.info(f"Added {len(ALL_TOOLS)} Todo tools to agent")
    except Exception as e:
        logger.warning(f"Failed to add Todo tools: {str(e)}")
        logger.debug(f"Todo tool addition error details:", exc_info=True)
    
    # Add the ADK's built-in transfer_to_agent tool
    try:
        # Rather than wrapping in a FunctionTool, add transfer_to_agent directly
        # as it's likely already properly registered within the ADK
        basic_tools.append(transfer_to_agent)
        logger.info("Added transfer_to_agent function directly to tools list")
        
        # Check if the function tool is available in the ADK
        from google.adk.tools.transfer_to_agent_tool import TRANSFER_TO_AGENT_TOOL
        if TRANSFER_TO_AGENT_TOOL:
            basic_tools.append(TRANSFER_TO_AGENT_TOOL)
            logger.info("Added TRANSFER_TO_AGENT_TOOL from ADK")
    except Exception as e:
        logger.warning(f"Failed to add transfer_to_agent tool: {str(e)}")
        logger.debug(f"Transfer tool addition error details:", exc_info=True)
    
    # Add any additional tools if provided
    all_tools = list(basic_tools) + memory_tools
    if tools:
        all_tools.extend(tools)
    
    # Log all tools being added
    tool_names = []
    for tool in all_tools:
        if hasattr(tool, '__name__'):
            tool_names.append(tool.__name__)
        elif hasattr(tool, 'name'):
            tool_names.append(tool.name)
        else:
            tool_names.append(str(type(tool)))
    
    logger.info(f"Creating web agent with tools: {', '.join(tool_names)}")
    
    # Get the instruction
    try:
        instruction = config_manager.get_instruction("main_agent")
        
        # Safely check tools (avoiding errors with None values)
        file_tool_exists = False
        ha_tool_exists = False
        shell_tool_exists = False
        todo_tool_exists = False
        
        for tool in all_tools:
            if tool is None:
                continue
                
            tool_str = str(tool).lower()
            if "file" in tool_str:
                file_tool_exists = True
            if "home_assistant" in tool_str:
                ha_tool_exists = True
            if "shell" in tool_str or "command" in tool_str or "execute" in tool_str:
                shell_tool_exists = True
            if "task" in tool_str or "todo" in tool_str:
                todo_tool_exists = True
        
        # Add filesystem instructions if available
        if file_tool_exists:
            fs_instruction = """
            You can access files on the system through the filesystem tools. Here are some examples:
            - To list files: Use the list_directory tool with the path parameter
            - To read a file: Use the read_file tool with the path parameter
            - To get file info: Use the get_info tool with the path parameter
            - To search for files: Use the search tool with path and pattern parameters
            
            If write operations are enabled, you can also:
            - Write to a file: Use the write_file tool with path and content parameters
            - Edit a file: Use the edit_file tool with path and edits parameters
            - Copy files: Use the copy tool with source_path and destination_path parameters
            
            If delete operations are enabled, you can also:
            - Delete files: Use the delete tool with the path parameter
            
            Always tell the user what action you're taking, and report back the results. If a filesystem operation fails, inform the user politely about the issue.
            """
            instruction += "\n\n" + fs_instruction
            logger.info("Added filesystem instructions to agent instruction")
            
        # Add Home Assistant REST API instructions
        if ha_tool_exists:
            ha_instruction = """
            You have access to Home Assistant smart home control tools through the REST API integration.
            
            First, search for entities:
            - Use search_ha_entities("search_term") to find entities matching your search
            - For domain-specific search, use search_ha_entities("search_term", "domain_filter") 
              Example domains: light, switch, sensor, climate, media_player, etc.
            
            You can also list all entities:
            - Use list_ha_entities() to get all Home Assistant entities
            
            Get information about specific entities:
            - Use get_ha_entity_state("entity_id") to get the state of a specific entity
              Example: get_ha_entity_state("light.living_room")
            
            Once you have the entity IDs, you can control them using:
            - turn_on_ha_entity("entity_id") - to turn on devices
            - turn_off_ha_entity("entity_id") - to turn off devices
            - toggle_ha_entity("entity_id") - to toggle devices (on if off, off if on)
            
            Always check the entity state before controlling it to understand its current status.
            """
            instruction += "\n\n" + ha_instruction
            logger.info("Added detailed Home Assistant REST API instructions to agent instruction")
            
        # Add Shell Command Execution instructions if available
        if shell_tool_exists:
            enable_shell = os.environ.get("RADBOT_ENABLE_SHELL", "strict").lower()
            shell_instruction = """
            You can execute shell commands using the execute_shell_command tool.
            
            Usage:
            - execute_shell_command(command="command_name", arguments=["arg1", "arg2"], timeout=30)
            
            Examples:
            - execute_shell_command(command="ls", arguments=["-la"])
            - execute_shell_command(command="cat", arguments=["/etc/hostname"])
            
            Always tell the user what command you're executing and what the results are.
            Never execute potentially destructive commands like rm, dd, or anything that could
            modify or delete important files.
            """
            
            if enable_shell in ["strict", "restricted", "secure"]:
                from radbot.tools.shell import ALLOWED_COMMANDS
                allowed_cmds = ", ".join(sorted(list(ALLOWED_COMMANDS)))
                shell_instruction += f"\n\nNOTE: You can only execute these allowed commands: {allowed_cmds}"
                
            instruction += "\n\n" + shell_instruction
            logger.info("Added shell command execution instructions to agent instruction")
            
        # Add Todo Tools instructions if available
        if todo_tool_exists:
            todo_instruction = """
            You can manage a persistent todo list using these todo tools:
            
            - add_task(description, project_id, category, origin, related_info): Creates a new task in the database
              description: The main text content describing the task (Required)
              project_id: Can be a UUID or a simple project name like 'home' or 'work' (Required)
              category: An optional label to categorize the task (e.g., 'work', 'personal')
              origin: An optional string indicating the source of the task (e.g., 'chat', 'email')
              related_info: An optional dictionary for storing supplementary structured data
            
            - list_tasks(project_id, status_filter): Retrieves tasks for a specific project
              project_id: Can be a UUID or a simple project name like 'home' or 'work' (Required)
              status_filter: Optional filter for task status ('backlog', 'inprogress', 'done')
            
            - list_projects(): Lists all available projects with their UUIDs and names
              Use this to show the user what projects are available
            
            - complete_task(task_id): Marks a specific task as 'done'
              task_id: The UUID identifier of the task to mark as completed (Required)
            
            - remove_task(task_id): Permanently deletes a task from the database
              task_id: The UUID identifier of the task to delete (Required)
            
            You don't need to generate UUIDs for projects - simply use common names like 'home', 'work', or any name the user
            chooses for their projects. The system will handle creating and mapping UUIDs internally.
            
            Always confirm actions before executing them and provide helpful feedback about the results of todo operations.
            Keep track of task IDs for the user so they don't need to remember them.
            """
            instruction += "\n\n" + todo_instruction
            logger.info("Added Todo tools instructions to agent instruction")
            
        # Add Calendar instructions
        calendar_instruction = """
        You have access to Google Calendar tools to view and manage calendar events.
        
        Available tools:
        - list_calendar_events_wrapper - Lists upcoming events from Google Calendar
        - create_calendar_event_wrapper - Creates a new event in Google Calendar
        - update_calendar_event_wrapper - Updates an existing event in Google Calendar
        - delete_calendar_event_wrapper - Deletes an event from Google Calendar
        - check_calendar_availability_wrapper - Checks availability on calendars
        
        Example usage:
        - To list events: list_calendar_events_wrapper(max_results=5, days_ahead=7)
        - To create an event: create_calendar_event_wrapper(summary="Meeting", start_time="2025-06-01T10:00:00", end_time="2025-06-01T11:00:00", description="Discuss project")
        - To update an event: update_calendar_event_wrapper(event_id="event123", summary="Updated Meeting")
        - To delete an event: delete_calendar_event_wrapper(event_id="event123")
        - To check availability: check_calendar_availability_wrapper(calendar_ids=["primary"], days_ahead=7)
        
        When working with calendar events, always provide clear details and confirm actions with the user.
        """
        instruction += "\n\n" + calendar_instruction
        logger.info("Added Calendar tools instructions to agent instruction")
    except Exception as e:
        logger.warning(f"Failed to load main_agent instruction: {str(e)}")
        instruction = """You are a helpful assistant. Your goal is to understand the user's request and fulfill it by using available tools."""
    
    # Create an ADK Agent directly - this is what the web UI expects
    # Get model from config manager which handles environment variable precedence
    model_name = config_manager.get_main_model()
    
    # Log the model we're using
    logger.info(f"Creating agent with model: {model_name}")
    
    # Create the agent with tools
    agent = None
    
    # For now, create regular agent without GenAI function calling
    # This approach is more compatible across ADK versions
    agent = Agent(
        name="beto",
        model=model_name,
        instruction=instruction,
        description="The main agent that handles user requests with memory capabilities.",
        tools=all_tools
    )
    logger.info("Created agent with standard tools")
    
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
    
    # Add research agent as a subagent if available
    try:
        logger.info("Creating research agent as a subagent")
        
        # Collect tools for the research agent
        research_tools = []
        
        # NEW APPROACH: Include ALL tools EXCEPT Home Assistant tools
        logger.info("USING NEW DIRECT APPROACH: Include all tools except HA tools")
        
        # Copy all tools except Home Assistant tools
        for tool in all_tools:
            # Get the tool name
            tool_name = None
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            else:
                tool_name = str(tool)
            
            # Skip Home Assistant tools
            ha_keywords = ["ha_", "home_assistant", "entity", "entities", "turn_on_ha", "turn_off_ha", "toggle_ha", "list_ha", "get_ha"]
            if any(ha_kw in str(tool_name).lower() for ha_kw in ha_keywords):
                logger.info(f"Skipping Home Assistant tool: {tool_name}")
                continue
            
            # Add all other tools (including get_weather tool)
            research_tools.append(tool)
            logger.info(f"Added tool to research agent: {tool_name}")
        
        # Create the research agent with all collected tools
        research_agent = create_research_agent(
            name="scout",
            model=model_name,
            tools=research_tools,
            as_subagent=False  # Get the ADK agent directly
        )
        
        # Log the final list of tools assigned to the research agent
        logger.info("========== RESEARCH AGENT TOOLS ===========")
        logger.info(f"Total tools assigned to research agent: {len(research_tools)}")
        for i, tool in enumerate(research_tools):
            tool_name = "Unknown"
            
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            else:
                tool_name = str(tool)
                
            logger.info(f"Research Tool {i+1}: {tool_name}")
        logger.info("===========================================")
        
        # Add the scout agent as a subagent directly to the main agent
        # This is critical for agent transfers to work correctly - the scout must be listed in the agent.sub_agents
        if hasattr(agent, 'sub_agents'):
            # Force reinitialization - this is crucial for ADK to register the agent in the tree
            agent.sub_agents = []  # Clear existing sub-agents
            agent.sub_agents.append(research_agent)
            
            # Bidirectional linking - research_agent should know its parent
            if hasattr(research_agent, 'parent'):
                research_agent.parent = agent
                
            # Verify registration
            sub_agent_names = [sa.name for sa in agent.sub_agents if hasattr(sa, 'name')]
            logger.info(f"Verified agent tree structure - Root agent: '{agent.name}', Sub-agents: {sub_agent_names}")
        else:
            agent.sub_agents = []
            agent.sub_agents.append(research_agent)
            logger.info(f"Created new sub_agents list with scout agent")
            
        # Ensure bidirectional relationship
        if hasattr(research_agent, '_parent'):
            research_agent._parent = agent
            logger.info(f"Set parent (_parent) reference on scout agent to '{agent.name}'")
        elif hasattr(research_agent, 'parent'):
            research_agent.parent = agent
            logger.info(f"Set parent reference on scout agent to '{agent.name}'")
            
        # Force agent name consistency one more time
        if hasattr(research_agent, 'name') and research_agent.name != 'scout':
            logger.warning(f"Scout agent name mismatch: '{research_agent.name}' not 'scout', fixing...")
            research_agent.name = 'scout'
        
        logger.info("Successfully added scout agent as a subagent")
        
        # Debug the agent tree structure extensively
        if agent.sub_agents:
            sub_agent_names = [sub_agent.name for sub_agent in agent.sub_agents if hasattr(sub_agent, 'name')]
            logger.info(f"Agent tree structure - Root agent: '{agent.name}', Sub-agents: {sub_agent_names}")
            
            # Print details of each sub-agent
            for i, sub_agent in enumerate(agent.sub_agents):
                sa_name = sub_agent.name if hasattr(sub_agent, 'name') else f"unnamed-{i}"
                
                # Check parent references
                parent_ref = None
                if hasattr(sub_agent, 'parent'):
                    parent_name = sub_agent.parent.name if hasattr(sub_agent.parent, 'name') else "unnamed-parent"
                    parent_ref = f"parent.name='{parent_name}'"
                elif hasattr(sub_agent, '_parent'):
                    parent_name = sub_agent._parent.name if hasattr(sub_agent._parent, 'name') else "unnamed-parent"
                    parent_ref = f"_parent.name='{parent_name}'"
                
                # Log details
                logger.info(f"Sub-agent {i}: name='{sa_name}', parent_ref={parent_ref}")
                
                # Check bidirectional relationship
                if parent_ref:
                    # Verify parent's sub_agents contains this agent
                    if hasattr(sub_agent, 'parent') and hasattr(sub_agent.parent, 'sub_agents'):
                        found_self = any(sa is sub_agent for sa in sub_agent.parent.sub_agents)
                        logger.info(f"  - Bidirectional check: parent.sub_agents contains this agent: {found_self}")
        else:
            logger.info(f"Agent tree structure - Root agent: '{agent.name}', No sub-agents found")
            
        # Debug transfer_to_agent function access
        from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
        logger.info(f"transfer_to_agent function available: {bool(transfer_to_agent)}")
        # Check if transfer tool is in agent's tools
        has_transfer_tool = False
        if hasattr(agent, 'tools'):
            for tool in agent.tools:
                if hasattr(tool, 'name') and tool.name == 'transfer_to_agent':
                    has_transfer_tool = True
                    break
                elif hasattr(tool, '__name__') and tool.__name__ == 'transfer_to_agent':
                    has_transfer_tool = True
                    break
        logger.info(f"Main agent has transfer_to_agent tool: {has_transfer_tool}")
        
        # Check research agent's tools
        if research_agent and hasattr(research_agent, 'tools'):
            has_research_transfer_tool = False
            for tool in research_agent.tools:
                if hasattr(tool, 'name') and tool.name == 'transfer_to_agent':
                    has_research_transfer_tool = True
                    break
                elif hasattr(tool, '__name__') and tool.__name__ == 'transfer_to_agent':
                    has_research_transfer_tool = True
                    break
            logger.info(f"Research agent has transfer_to_agent tool: {has_research_transfer_tool}")
        
        # Add instruction for scout agent delegation
        research_agent_instruction = """
        If the user has a technical research question or wants to discuss a design/architecture,
        you can transfer the conversation to the scout agent by using the
        transfer_to_agent function. Example: transfer_to_agent(agent_name='scout')
        
        The scout agent is specialized for:
        1. Technical research using web search, internal knowledge, and GitHub
        2. Design discussions (rubber duck debugging) to help think through technical designs
        
        Before transferring, make sure you've fully understood what the user wants to research
        or discuss, then use session.state to pass the context to the scout agent.
        
        The scout agent can transfer control back to you using the same function:
        transfer_to_agent(agent_name='beto')
        """
        instruction += "\n\n" + research_agent_instruction
        agent.instruction = instruction
        logger.info("Added scout agent delegation instructions to main agent")
    except Exception as e:
        logger.warning(f"Failed to add scout agent as a subagent: {str(e)}")
        logger.debug("Scout agent creation error details:", exc_info=True)
    
    logger.info(f"Created ADK BaseAgent for web UI with {len(all_tools)} tools")
    return agent

# Create a root_agent instance for ADK web to use directly
root_agent = create_agent()
logger.info(f"Created root_agent instance for ADK web with name '{root_agent.name}' and {len(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') else 0} sub-agents")

# Using REST API approach for Home Assistant
