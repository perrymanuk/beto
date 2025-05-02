"""
Root agent.py file for ADK web interface.

This file is used by the ADK web interface to create the agent with all needed tools.
The ADK web interface uses this file directly based on the adk.config.json setting.
"""

import logging
import os
import sys
from typing import Optional, Any, List

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

# Log configuration
logger.info(f"Config manager loaded. Model config: {config_manager.model_config}")
logger.info(f"Main model from config: '{config_manager.get_main_model()}'")
logger.info(f"Environment RADBOT_MAIN_MODEL: '{os.environ.get('RADBOT_MAIN_MODEL')}'")
logger.info(f"Using Vertex AI: {config_manager.is_using_vertex_ai()}")

# Import tools
from radbot.tools.basic_tools import get_current_time, get_weather
from radbot.tools.memory_tools import search_past_conversations, store_important_information
from radbot.tools.mcp_tools import search_home_assistant_entities
from radbot.tools.web_search_tools import create_tavily_search_tool
from radbot.tools.mcp_fileserver_client import create_fileserver_toolset
from radbot.tools.mcp_crawl4ai_client import create_crawl4ai_toolset, test_crawl4ai_connection

# Log startup
logger.info("ROOT agent.py loaded - this is the main implementation loaded by ADK web")
print(f"SPECIAL DEBUG: agent.py loaded with MCP_FS_ROOT_DIR={os.environ.get('MCP_FS_ROOT_DIR', 'Not set')}")


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
    
    # Start with basic tools
    basic_tools = [get_current_time, get_weather]
    
    # Always include memory tools
    memory_tools = [search_past_conversations, store_important_information]
    logger.info(f"Including memory tools: {[t.__name__ for t in memory_tools]}")
    
    # Add Home Assistant entity search
    basic_tools.append(search_home_assistant_entities)
    
    # Add MCP Fileserver tools
    try:
        # Print MCP fileserver configuration
        mcp_fs_root_dir = os.environ.get("MCP_FS_ROOT_DIR")
        if mcp_fs_root_dir:
            logger.info(f"MCP Fileserver: Using root directory {mcp_fs_root_dir}")
            print(f"SPECIAL DEBUG: MCP_FS_ROOT_DIR={mcp_fs_root_dir}")  # Will print even in subprocess
        else:
            logger.info("MCP Fileserver: Root directory not set (MCP_FS_ROOT_DIR not found in environment)")
            print("SPECIAL DEBUG: MCP_FS_ROOT_DIR not set")  # Will print even in subprocess
            
        logger.info("Creating MCP fileserver toolset...")
        print("SPECIAL DEBUG: About to call create_fileserver_toolset()")  # Will print even in subprocess
        fs_tools = create_fileserver_toolset()
        if fs_tools:
            # Log detailed information about each fileserver tool
            logger.debug(f"FileServerMCP returned {len(fs_tools)} tools")
            for i, tool in enumerate(fs_tools):
                tool_name = tool.name if hasattr(tool, 'name') else str(tool)
                tool_type = type(tool).__name__
                logger.debug(f"  FS Tool {i+1}: {tool_name} (type: {tool_type})")
            
            # fs_tools is now a list of tools, so extend basic_tools with it
            basic_tools.extend(fs_tools)
            
            # Log tools individually for better debugging
            fs_tool_names = [tool.name if hasattr(tool, 'name') else str(tool) for tool in fs_tools]
            logger.info(f"Successfully added {len(fs_tools)} MCP fileserver tools: {', '.join(fs_tool_names)}")
        else:
            logger.warning("MCP fileserver tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create MCP fileserver tools: {str(e)}")
        logger.debug(f"Fileserver tool creation error details:", exc_info=True)
        
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
                from radbot.tools.web_search_tools import HAVE_TAVILY, TavilySearchResults
                
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
        
        # Add MCP fileserver instructions if available
        if any("file" in str(tool).lower() for tool in all_tools):
            fs_instruction = """
            You can access files on the system through the file tools. Here are some examples:
            - To list files: Use the list_files tool with the path parameter
            - To read a file: Use the read_file tool with the path parameter
            - To get file info: Use the get_file_info tool with the path parameter
            
            Always tell the user what action you're taking, and report back the results. If a filesystem operation fails, inform the user politely about the issue.
            """
            instruction += "\n\n" + fs_instruction
            logger.info("Added MCP fileserver instructions to agent instruction")
    except Exception as e:
        logger.warning(f"Failed to load main_agent instruction: {str(e)}")
        instruction = """You are a helpful assistant. Your goal is to understand the user's request and fulfill it by using available tools."""
    
    # Create an ADK Agent directly - this is what the web UI expects
    # Get model from config manager which handles environment variable precedence
    model_name = config_manager.get_main_model()
    
    # Log the model we're using
    logger.info(f"Creating agent with model: {model_name}")
    
    agent = Agent(
        name="radbot_web",
        model=model_name,  # Use the sanitized model name
        instruction=instruction,
        description="The main agent that handles user requests with memory capabilities.",
        tools=all_tools
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
    
    logger.info(f"Created ADK BaseAgent for web UI with {len(all_tools)} tools")
    return agent

# Create a root_agent instance for ADK web to use directly
root_agent = create_agent()
logger.info("Created root_agent instance for direct use by ADK web")