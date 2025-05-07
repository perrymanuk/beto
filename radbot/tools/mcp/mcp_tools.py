"""
MCP integration tools for connecting to various servers.

This module provides utilities for connecting to external services via the Model Context Protocol (MCP).
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from contextlib import AsyncExitStack

from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

from radbot.config.config_loader import config_loader
from radbot.tools.mcp.mcp_client_factory import MCPClientFactory, MCPClientError

logger = logging.getLogger(__name__)

# Flag to track if we have Tavily dependencies
HAVE_TAVILY = False

# Try to import tavily and langchain tools
try:
    from langchain_community.tools import TavilySearchResults
    from google.adk.tools.langchain import LangchainTool
    HAVE_TAVILY = True
    logger.info("Tavily and Langchain tools imported successfully")
except ImportError:
    logger.warning("Tavily or Langchain tools not found. Web search capabilities will be limited.")
    logger.warning("Try installing with: pip install langchain-community tavily-python")

def get_available_mcp_tools() -> List[Any]:
    """
    Get a list of all available MCP tools.
    
    This function returns a consolidated list of all available MCP tools
    including Home Assistant, FileServer, Crawl4AI, and other MCP integrations.
    
    Returns:
        List of available MCP tools
    """
    tools = []
    
    # Get all tools from configured MCP servers
    try:
        # Get MCP server tools using ConfigLoader and MCPClientFactory
        mcp_tools = create_mcp_tools()
        if mcp_tools:
            tools.extend(mcp_tools)
            logger.info(f"Added {len(mcp_tools)} tools from MCP servers configured in config.yaml")
    except Exception as e:
        logger.warning(f"Failed to get tools from MCP servers in config.yaml: {str(e)}")
    
    # If no tools were added from config, try the legacy approach
    if not tools:
        logger.info("No MCP tools found from config.yaml, falling back to legacy approach")
        
        # Try to get Home Assistant tools
        try:
            ha_tools = create_home_assistant_toolset()
            if ha_tools:
                if isinstance(ha_tools, list):
                    tools.extend(ha_tools)
                    logger.info(f"Added {len(ha_tools)} Home Assistant MCP tools")
                else:
                    tools.append(ha_tools)
                    logger.info("Added Home Assistant MCP toolset")
        except Exception as e:
            logger.warning(f"Failed to get Home Assistant MCP tools: {str(e)}")
        
        # Try to get FileServer tools if available
        try:
            # Import here to avoid circular imports
            from radbot.tools.mcp.mcp_fileserver_client import create_fileserver_toolset
            fs_tools = create_fileserver_toolset()
            if fs_tools:
                if isinstance(fs_tools, list):
                    tools.extend(fs_tools)
                    logger.info(f"Added {len(fs_tools)} FileServer MCP tools")
                else:
                    tools.append(fs_tools)
                    logger.info("Added FileServer MCP toolset")
        except Exception as e:
            logger.warning(f"Failed to get FileServer MCP tools: {str(e)}")
            
        # Try to get Crawl4AI tools if available
        try:
            # Import here to avoid circular imports
            from radbot.tools.crawl4ai.mcp_crawl4ai_client import create_crawl4ai_toolset
            crawl4ai_tools = create_crawl4ai_toolset()
            if crawl4ai_tools:
                if isinstance(crawl4ai_tools, list):
                    tools.extend(crawl4ai_tools)
                    logger.info(f"Added {len(crawl4ai_tools)} Crawl4AI MCP tools")
                else:
                    tools.append(crawl4ai_tools)
                    logger.info("Added Crawl4AI MCP toolset")
        except Exception as e:
            logger.warning(f"Failed to get Crawl4AI MCP tools: {str(e)}")
    
    return tools

def create_mcp_tools() -> List[Any]:
    """
    Create tools for all enabled MCP servers defined in the configuration.
    
    Returns:
        List of MCP tools created from the configuration
    """
    tools = []
    
    # Get all enabled MCP servers from configuration
    servers = config_loader.get_enabled_mcp_servers()
    
    if not servers:
        logger.info("No enabled MCP servers found in configuration")
        return tools
    
    logger.info(f"Found {len(servers)} enabled MCP servers in configuration")
    
    # Create tools for each enabled server
    for server in servers:
        server_id = server.get("id")
        server_name = server.get("name", server_id)
        
        try:
            # Get or create the MCP client for this server
            client = MCPClientFactory.get_client(server_id)
            
            # Create tools from the client
            server_tools = _create_tools_from_client(client, server)
            
            if server_tools:
                logger.info(f"Created {len(server_tools)} tools for MCP server '{server_name}'")
                tools.extend(server_tools)
            else:
                logger.warning(f"No tools created for MCP server '{server_name}'")
                
        except MCPClientError as e:
            logger.warning(f"Failed to create client for MCP server '{server_name}': {e}")
        except Exception as e:
            logger.error(f"Error creating tools for MCP server '{server_name}': {e}")
    
    return tools

def _create_tools_from_client(client: Any, server_config: Dict[str, Any]) -> List[Any]:
    """
    Create tools from an MCP client.
    
    Args:
        client: The MCP client instance
        server_config: The server configuration dictionary
        
    Returns:
        List of tools created from the client
    """
    tools = []
    server_id = server_config.get("id")
    
    try:
        # Different MCP servers might have different APIs for getting tools
        # Try common patterns
        
        # 1. Check if client has get_tools method
        if hasattr(client, "get_tools") and callable(client.get_tools):
            server_tools = client.get_tools()
            if server_tools:
                tools.extend(server_tools)
                return tools
        
        # 2. Check if client has a tools attribute that's a list
        if hasattr(client, "tools") and isinstance(client.tools, list):
            tools.extend(client.tools)
            return tools
            
        # 3. Check if client has a create_tools method
        if hasattr(client, "create_tools") and callable(client.create_tools):
            server_tools = client.create_tools()
            if server_tools:
                tools.extend(server_tools)
                return tools
        
        # 4. Check if client is a descriptor class with tools attribute
        if hasattr(client, "descriptor") and hasattr(client.descriptor, "tools"):
            tools.extend(client.descriptor.tools)
            return tools
        
        # If we get here, we couldn't find tools through standard methods
        # Try to look for specific implementations based on server_id
        
        if server_id == "crawl4ai":
            # Handle Crawl4AI special case
            from radbot.tools.crawl4ai.mcp_crawl4ai_client import create_crawl4ai_toolset
            crawl4ai_tools = create_crawl4ai_toolset()
            if crawl4ai_tools:
                tools.extend(crawl4ai_tools)
                return tools
        
        # Add other special cases as needed
        
        logger.warning(f"Could not determine how to get tools from MCP server '{server_id}'")
        return tools
        
    except Exception as e:
        logger.error(f"Error creating tools from MCP client for '{server_id}': {e}")
        return tools

async def _create_home_assistant_toolset_async() -> Tuple[List[Any], Optional[AsyncExitStack]]:
    """
    Async function to create an MCPToolset for Home Assistant's MCP Server using ADK 0.3.0 API.
    
    Returns:
        Tuple[List[MCPTool], AsyncExitStack]: The list of tools and exit stack, or ([], None) if configuration fails
    """
    try:
        # Get Home Assistant configuration from config.yaml
        ha_config = config_loader.get_home_assistant_config()
        
        # Get connection parameters from configuration or fall back to environment variables
        ha_mcp_url = ha_config.get("mcp_sse_url")
        if not ha_mcp_url:
            # Fall back to environment variable
            ha_mcp_url = os.getenv("HA_MCP_SSE_URL")
        
        ha_auth_token = ha_config.get("token")
        if not ha_auth_token:
            # Fall back to environment variable
            ha_auth_token = os.getenv("HA_AUTH_TOKEN")
        
        if not ha_mcp_url:
            logger.error("Home Assistant MCP URL not found. "
                        "Please set mcp_sse_url in the Home Assistant configuration section of config.yaml "
                        "or set HA_MCP_SSE_URL environment variable.")
            return [], None
            
        if not ha_auth_token:
            logger.error("Home Assistant authentication token not found. "
                        "Please set token in the Home Assistant configuration section of config.yaml "
                        "or set HA_AUTH_TOKEN environment variable.")
            return [], None
            
        # Normalize URL path - ensure it has the correct format
        # Home Assistant MCP Server typically uses /mcp_server/sse or sometimes /api/mcp_server/sse
        if not ha_mcp_url.endswith("/mcp_server/sse") and not ha_mcp_url.endswith("/api/mcp_server/sse"):
            original_url = ha_mcp_url
            
            # If URL ends with a trailing slash, remove it
            if ha_mcp_url.endswith("/"):
                ha_mcp_url = ha_mcp_url[:-1]
                
            # If URL doesn't contain /mcp_server/sse path, add it
            if "/mcp_server/sse" not in ha_mcp_url:
                ha_mcp_url = f"{ha_mcp_url}/mcp_server/sse"
                
            logger.info(f"Normalized Home Assistant MCP URL from {original_url} to {ha_mcp_url}")
            
        logger.info(f"Using Home Assistant MCP URL: {ha_mcp_url}")
        
        # Configure the SSE parameters for Home Assistant MCP server
        ha_mcp_params = SseServerParams(
            url=ha_mcp_url,
            headers={
                "Authorization": f"Bearer {ha_auth_token}"
            }
        )
        
        # Create an AsyncExitStack for resource management
        exit_stack = AsyncExitStack()
        
        try:
            # Use from_server static method instead of direct constructor in ADK 0.3.0
            # This returns a tuple of (tools_list, exit_stack)
            tools, _ = await MCPToolset.from_server(
                connection_params=ha_mcp_params,
                async_exit_stack=exit_stack
            )
            
            logger.info(f"Successfully loaded {len(tools)} Home Assistant MCP tools with ADK 0.3.0 API")
            return tools, exit_stack
        except Exception as e:
            logger.error(f"Failed to create MCPToolset: {str(e)}")
            # Try to clean up resources if exit_stack was used
            try:
                await exit_stack.aclose()
            except:
                pass
            return [], None
        
    except ImportError as ie:
        logger.error(f"Failed to import required modules: {str(ie)}")
        logger.error("Make sure google-adk>=0.3.0 is installed")
        return [], None
    except Exception as e:
        logger.error(f"Failed to create Home Assistant MCP toolset: {str(e)}")
        return [], None

def create_home_assistant_toolset() -> List[Any]:
    """
    Create Home Assistant MCP tools using ADK 0.3.0 API.
    
    Uses environment variables for configuration (HA_MCP_SSE_URL, HA_AUTH_TOKEN).
    
    Returns:
        List[MCPTool]: List of Home Assistant MCP tools, or empty list if configuration fails
    """
    exit_stack = None
    try:
        # Need to check if we're already in an event loop
        try:
            existing_loop = asyncio.get_event_loop()
            if existing_loop.is_running():
                logger.warning("Cannot create Home Assistant toolset: Event loop is already running")
                logger.warning("This likely means you're using this in an async context")
                logger.warning("Try using 'await _create_home_assistant_toolset_async()' instead")
                return []
        except RuntimeError:
            # No event loop exists, create a new one
            pass
            
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tools, exit_stack = loop.run_until_complete(_create_home_assistant_toolset_async())
        
        # Close only the event loop
        loop.close()
        
        return tools
    except Exception as e:
        logger.error(f"Error creating Home Assistant tools: {str(e)}")
        if exit_stack:
            try:
                # We need to close the exit stack if an error occurred
                # Create a new event loop for this
                cleanup_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(cleanup_loop)
                cleanup_loop.run_until_complete(exit_stack.aclose())
                cleanup_loop.close()
            except Exception as cleanup_error:
                logger.error(f"Error during cleanup: {str(cleanup_error)}")
        return []


def create_find_ha_entities_tool():
    """Create a function tool to search for Home Assistant entities."""
    import logging
    from radbot.tools.mcp.mcp_utils import find_home_assistant_entities
    
    logger = logging.getLogger(__name__)
    
    # For ADK 0.3.0 compatibility, we'll use the built-in tool creation
    # mechanism from the Agent Development Kit instead of directly creating a FunctionTool
    try:
        # ADK 0.3.0 approach using @tool decorator
        from google.adk.tools.decorators import tool
        
        # Create a decorated function with proper schema
        @tool(
            name="search_home_assistant_entities",
            description="Search for Home Assistant entities by name or area",
            parameters={
                "search_term": {
                    "type": "string",
                    "description": "Term to search for in entity names, like 'kitchen' or 'plant'"
                },
                "domain_filter": {
                    "type": "string",
                    "description": "Optional domain type to filter by (light, switch, etc.)",
                    "enum": ["light", "switch", "sensor", "media_player", "climate", "cover", "vacuum"],
                    "required": False
                }
            },
            required=["search_term"]
        )
        def search_home_assistant_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
            """
            Search for Home Assistant entities by name.
            
            Args:
                search_term: Text to search for in entity names/IDs
                domain_filter: Optional domain type to filter by (light, switch, etc.)
                
            Returns:
                Dictionary with matching entities
            """
            logger.info(f"Entity search called with term: '{search_term}', domain_filter: '{domain_filter}'")
            result = find_home_assistant_entities(search_term, domain_filter)
            logger.info(f"Entity search result: {result.get('status', 'unknown')} (found {result.get('match_count', 0)} matches)")
            return result
            
        logger.info(f"Created entity search tool using @tool decorator")
        return search_home_assistant_entities
        
    except (ImportError, AttributeError):
        # Fall back to direct FunctionTool creation
        logger.warning("@tool decorator not available, falling back to FunctionTool creation")
        
        from google.adk.tools import FunctionTool
        
        # Define the search function with exactly matching name as specified in schema
        def search_home_assistant_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
            """
            Search for Home Assistant entities by name.
            
            Args:
                search_term: Text to search for in entity names/IDs
                domain_filter: Optional domain type to filter by (light, switch, etc.)
                
            Returns:
                Dictionary with matching entities
            """
            logger.info(f"Entity search called with term: '{search_term}', domain_filter: '{domain_filter}'")
            result = find_home_assistant_entities(search_term, domain_filter)
            logger.info(f"Entity search result: {result.get('status', 'unknown')} (found {result.get('match_count', 0)} matches)")
            return result
        
        # Try FunctionTool creation with different approaches
        try:
            # First try the newer ADK 0.3.0 style
            tool = FunctionTool(
                function=search_home_assistant_entities,
                function_schema={
                    "name": "search_home_assistant_entities", 
                    "description": "Search for Home Assistant entities by name or area",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string",
                                "description": "Term to search for in entity names, like 'kitchen' or 'plant'"
                            },
                            "domain_filter": {
                                "type": "string",
                                "description": "Optional domain type to filter by (light, switch, etc.)",
                                "enum": ["light", "switch", "sensor", "media_player", "climate", "cover", "vacuum"]
                            }
                        },
                        "required": ["search_term"]
                    }
                }
            )
            logger.info("Created entity search tool using ADK 0.3.0 FunctionTool style")
        except TypeError:
            # Fall back to older ADK API
            tool = FunctionTool(
                search_home_assistant_entities,
                {
                    "name": "search_home_assistant_entities",
                    "description": "Search for Home Assistant entities by name or area",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "search_term": {
                                "type": "string", 
                                "description": "Term to search for in entity names, like 'kitchen' or 'plant'"
                            },
                            "domain_filter": {
                                "type": "string",
                                "description": "Optional domain type to filter by (light, switch, etc.)",
                                "enum": ["light", "switch", "sensor", "media_player", "climate", "cover", "vacuum"]
                            }
                        },
                        "required": ["search_term"]
                    }
                }
            )
            logger.info("Created entity search tool using legacy FunctionTool style")
        
        return tool


# Create a pure function version of the search tool
def search_home_assistant_entities(search_term: str, domain_filter: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for Home Assistant entities by name or area.
    
    Args:
        search_term: Term to search for in entity names, like 'kitchen' or 'plant'
        domain_filter: Optional domain type to filter by (light, switch, etc.)
        
    Returns:
        Dictionary with matching entities
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Entity search called with term: '{search_term}', domain_filter: '{domain_filter}'")
    from radbot.tools.mcp.mcp_utils import find_home_assistant_entities
    
    try:
        result = find_home_assistant_entities(search_term, domain_filter)
        logger.info(f"Entity search result: {result.get('status', 'unknown')} (found {result.get('match_count', 0)} matches)")
        
        # If no entities were found, provide a helpful message
        if not result.get("success"):
            if result.get("status") == "no_entities":
                return {
                    "success": False,
                    "status": "no_entities",
                    "message": "I couldn't find any entities in your Home Assistant system. This could be because:\n"
                              "1. Home Assistant MCP server is not properly configured\n"
                              "2. Your Home Assistant instance doesn't have any entities that match your search\n"
                              "3. The MCP integration doesn't support entity listing for your Home Assistant version\n\n"
                              "Please check your Home Assistant MCP server configuration.",
                    "search_term": search_term,
                    "domain_filter": domain_filter,
                    "supported_domains": result.get("supported_domains", []),
                    "match_count": 0,
                    "matches": []
                }
            elif result.get("status") == "unsupported_domain":
                domain = search_term.split(".", 1)[0] if "." in search_term else domain_filter
                supported_domains = result.get("supported_domains", [])
                
                return {
                    "success": False,
                    "status": "unsupported_domain",
                    "message": f"I couldn't find the entity because the domain '{domain}' is not supported by your Home Assistant MCP integration.\n\n"
                              f"Supported domains are: {', '.join(supported_domains) if supported_domains else 'None detected'}\n\n"
                              "This could be because:\n"
                              "1. The domain is not properly enabled in your Home Assistant instance\n"
                              "2. The domain is not exposed via the MCP integration\n"
                              "3. The MCP server configuration needs updating\n\n"
                              f"You searched for: {search_term}",
                    "search_term": search_term,
                    "domain_filter": domain_filter,
                    "supported_domains": supported_domains,
                    "domain": domain,
                    "match_count": 0,
                    "matches": []
                }
        
        return result
    except Exception as e:
        logger.error(f"Error in search_home_assistant_entities: {str(e)}")
        # Return a more helpful error message
        return {
            "success": False,
            "error": str(e),
            "message": "There was a problem connecting to your Home Assistant system. "
                      "Please check your Home Assistant MCP server configuration and ensure it's running.",
            "search_term": search_term,
            "domain_filter": domain_filter,
            "match_count": 0,
            "matches": [],
            "status": "error"
        }

def create_mcp_enabled_agent(agent_factory: Callable, base_tools: Optional[List[Any]] = None, **kwargs) -> Any:
    """
    Create an agent with all MCP tools enabled.
    
    This function creates an agent with all MCP tools from config.yaml.
    
    Args:
        agent_factory: Function to create an agent (like create_agent)
        base_tools: Optional list of base tools to include
        **kwargs: Additional arguments to pass to agent_factory
        
    Returns:
        Agent: The created agent with MCP tools
    """
    try:
        # Start with base tools or empty list
        tools = list(base_tools or [])
        
        # Create MCP tools
        mcp_tools = get_available_mcp_tools()
        
        if mcp_tools:
            # Add the tools to our list
            tools.extend(mcp_tools)
            logger.info(f"Added {len(mcp_tools)} MCP tools to agent")
        else:
            logger.warning("No MCP tools were created")
            
        # Create the agent with the tools
        agent = agent_factory(tools=tools, **kwargs)
        return agent
    except Exception as e:
        logger.error(f"Error creating agent with MCP tools: {str(e)}")
        # Create agent without MCP tools as fallback
        return agent_factory(tools=base_tools, **kwargs)

def create_tavily_search_tool(max_results=5, search_depth="advanced", include_answer=True, include_raw_content=True, include_images=False):
    """
    Create a Tavily search tool that can be used by the agent.
    
    This tool allows the agent to search the web via Tavily's search API.
    
    Args:
        max_results: Maximum number of search results to return (default: 5)
        search_depth: Search depth, either "basic" or "advanced" (default: "advanced")
        include_answer: Whether to include an AI-generated answer (default: True) 
        include_raw_content: Whether to include the raw content of search results (default: True)
        include_images: Whether to include images in search results (default: False)
        
    Returns:
        The created Tavily search tool wrapped for ADK, or None if creation fails
    """
    if not HAVE_TAVILY:
        logger.error("Tavily search tool requires langchain-community package with TavilySearchResults")
        return None
    
    # Get Tavily API key from config.yaml or environment variable
    api_key = config_loader.get_config().get("api_keys", {}).get("tavily")
    if not api_key:
        # Fall back to environment variable
        api_key = os.environ.get("TAVILY_API_KEY")
    
    if not api_key:
        logger.error("Tavily API key not found in config.yaml or TAVILY_API_KEY environment variable. "
                     "The Tavily search tool will not function correctly.")
        # We don't return None here to allow for testing/development without credentials
    else:
        # Set the environment variable for the LangChain tool
        os.environ["TAVILY_API_KEY"] = api_key
    
    try:
        # Instantiate LangChain's Tavily search tool
        tavily_search = TavilySearchResults(
            max_results=max_results,
            search_depth=search_depth,
            include_answer=include_answer,
            include_raw_content=include_raw_content,
            include_images=include_images,
        )
        
        # Wrap with LangchainTool for ADK compatibility
        adk_tavily_tool = LangchainTool(tool=tavily_search)
        logger.info(f"Successfully created Tavily search tool with max_results={max_results}, search_depth={search_depth}")
        return adk_tavily_tool
        
    except Exception as e:
        logger.error(f"Failed to create Tavily search tool: {str(e)}")
        return None


def create_ha_mcp_enabled_agent(agent_factory, base_tools=None, ensure_memory_tools=True):
    """
    Create an agent with Home Assistant MCP tools.
    
    Args:
        agent_factory: Function to create an agent (like AgentFactory.create_root_agent or create_memory_enabled_agent)
        base_tools: Optional list of base tools to include
        ensure_memory_tools: If True, ensure memory tools are included in the agent tools
        
    Returns:
        Agent: The created agent, or None if creation fails
    """
    try:
        # Start with base tools or empty list
        tools = list(base_tools or [])
        
        # Add the entity search tool as a pure function (highest priority)
        tools.insert(0, search_home_assistant_entities)  
        logger.info("Added search_home_assistant_entities as pure function (highest priority)")
        
        # Ensure memory tools are included if requested
        if ensure_memory_tools:
            from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
            memory_tools = [search_past_conversations, store_important_information]
            
            # Check if memory tools are already in tools list
            memory_tool_names = set([tool.__name__ for tool in memory_tools])
            existing_tool_names = set()
            for tool in tools:
                if hasattr(tool, '__name__'):
                    existing_tool_names.add(tool.__name__)
                elif hasattr(tool, 'name'):
                    existing_tool_names.add(tool.name)
                    
            # Add any missing memory tools
            for tool in memory_tools:
                if tool.__name__ not in existing_tool_names:
                    tools.append(tool)
                    logger.info(f"Explicitly adding memory tool: {tool.__name__}")
        
        # Also add the wrapped version as a backup
        entity_search_tool = create_find_ha_entities_tool()
        if entity_search_tool:
            tools.insert(1, entity_search_tool)
            logger.info(f"Added wrapped entity search tool as backup with name: {getattr(entity_search_tool, 'name', 'unknown')}")
        
        # Try to add Home Assistant MCP tools (using ADK 0.3.0 API)
        ha_tools = create_home_assistant_toolset()
        
        if ha_tools and len(ha_tools) > 0:
            logger.info(f"Adding {len(ha_tools)} Home Assistant MCP tools to agent")
            
            # Create proper function wrappers for each Home Assistant tool with schemas
            from google.adk.tools import FunctionTool
            
            # Add each tool individually with proper schema information
            for tool in ha_tools:
                if hasattr(tool, 'name'):
                    tool_name = tool.name
                    logger.info(f"Processing tool: {tool_name}")
                    
                    # Create a wrapper function with clear parameter definitions
                    if tool_name == "HassTurnOn" or tool_name == "HassTurnOff":
                        # Create a wrapper function for turn on/off
                        def wrap_hass_tool(tool_ref, tool_name_ref):
                            async def wrapped_tool(entity_id: str):
                                """Control a Home Assistant entity."""
                                logger.info(f"Calling {tool_name_ref} with entity_id: {entity_id}")
                                return await tool_ref(entity_id=entity_id)
                            # Preserve the original tool name
                            wrapped_tool.__name__ = tool_name_ref
                            return wrapped_tool
                            
                        # Add the wrapped tool with explicit schema
                        wrapped_tool = wrap_hass_tool(tool, tool_name)
                        
                        try:
                            # ADK 0.3.0 style
                            function_tool = FunctionTool(
                                function=wrapped_tool,
                                function_schema={
                                    "name": tool_name,
                                    "description": getattr(tool, 'description', f"{tool_name} function for Home Assistant entity control"),
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "entity_id": {
                                                "type": "string", 
                                                "description": "The entity ID to control (e.g. light.kitchen, switch.fan)"
                                            }
                                        },
                                        "required": ["entity_id"]
                                    }
                                }
                            )
                            logger.info(f"Added wrapped tool: {tool_name} with schema (ADK 0.3.0 style)")
                        except TypeError:
                            # Fallback for older ADK versions
                            function_tool = FunctionTool(
                                wrapped_tool,
                                {
                                    "name": tool_name,
                                    "description": getattr(tool, 'description', f"{tool_name} function for Home Assistant entity control"),
                                    "parameters": {
                                        "type": "object",
                                        "properties": {
                                            "entity_id": {
                                                "type": "string", 
                                                "description": "The entity ID to control (e.g. light.kitchen, switch.fan)"
                                            }
                                        },
                                        "required": ["entity_id"]
                                    }
                                }
                            )
                            logger.info(f"Added wrapped tool: {tool_name} with schema (legacy style)")
                            
                        tools.append(function_tool)
                        logger.info(f"Added wrapped tool: {tool_name} with schema")
                    else:
                        # For other tools, just add them directly for now
                        logger.info(f"Adding original tool: {tool_name}")
                        tools.append(tool)
                else:
                    logger.warning(f"Skipping tool without name: {tool}")
                    
            logger.info(f"Total tools after adding HA tools: {len(tools)}")
        else:
            logger.warning("No Home Assistant MCP tools were found")
        
        # Log all tool names before creating agent
        tool_names = []
        for tool in tools:
            if hasattr(tool, 'name'):
                tool_names.append(tool.name)
            elif hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            else:
                tool_names.append(str(type(tool)))
        logger.info(f"Tools being added to agent: {', '.join(tool_names[:10])}...")
        
        # Create the agent with tools
        logger.info(f"Creating agent with {len(tools)} total tools")
        agent = agent_factory(tools=tools)
        
        # Verify tools were added correctly
        if hasattr(agent, 'tools'):
            agent_tools = agent.tools
            search_tools = []
            memory_tools = []
            for t in agent_tools:
                if hasattr(t, 'name') and t.name == "search_home_assistant_entities":
                    search_tools.append(t)
                elif hasattr(t, '__name__') and t.__name__ == "search_home_assistant_entities":
                    search_tools.append(t)
                
                # Check for memory tools
                if hasattr(t, '__name__') and t.__name__ in ["search_past_conversations", "store_important_information"]:
                    memory_tools.append(t.__name__)
                elif hasattr(t, 'name') and t.name in ["search_past_conversations", "store_important_information"]:
                    memory_tools.append(t.name)
            
            ha_tools_in_agent = [t for t in agent_tools if hasattr(t, 'name') and t.name.startswith('Hass')]
            logger.info(f"Agent created with {len(agent_tools)} tools")
            logger.info(f"Found {len(search_tools)} search tools, {len(ha_tools_in_agent)} Home Assistant control tools")
            logger.info(f"Memory tools present: {memory_tools}")
        elif hasattr(agent, 'root_agent') and hasattr(agent.root_agent, 'tools'):
            agent_tools = agent.root_agent.tools
            search_tools = []
            memory_tools = []
            for t in agent_tools:
                if hasattr(t, 'name') and t.name == "search_home_assistant_entities":
                    search_tools.append(t)
                elif hasattr(t, '__name__') and t.__name__ == "search_home_assistant_entities":
                    search_tools.append(t)
                
                # Check for memory tools
                if hasattr(t, '__name__') and t.__name__ in ["search_past_conversations", "store_important_information"]:
                    memory_tools.append(t.__name__)
                elif hasattr(t, 'name') and t.name in ["search_past_conversations", "store_important_information"]:
                    memory_tools.append(t.name)
            
            ha_tools_in_agent = [t for t in agent_tools if hasattr(t, 'name') and t.name.startswith('Hass')]
            logger.info(f"Agent wrapper created with {len(agent_tools)} tools")
            logger.info(f"Found {len(search_tools)} search tools, {len(ha_tools_in_agent)} Home Assistant control tools")
            logger.info(f"Memory tools present: {memory_tools}")
            
            # Log all tool names for debugging
            tool_names = []
            for tool in agent_tools:
                if hasattr(tool, 'name'):
                    tool_names.append(tool.name)
                elif hasattr(tool, '__name__'):
                    tool_names.append(tool.__name__)
                else:
                    tool_names.append(str(type(tool)))
            logger.info(f"Tools in agent: {', '.join(tool_names[:20])}...")
        
        return agent
    except Exception as e:
        logger.error(f"Error creating agent with Home Assistant MCP tools: {str(e)}")
        return None