"""
MCP integration tools for connecting to Home Assistant.

This module provides utilities for connecting to Home Assistant via the Model Context Protocol (MCP).
"""

import os
import logging
import asyncio
from typing import Dict, Any, Optional, List, Tuple
from contextlib import AsyncExitStack

from dotenv import load_dotenv
from google.adk.tools.mcp_tool import MCPToolset
from google.adk.tools.mcp_tool.mcp_session_manager import SseServerParams

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

async def _create_home_assistant_toolset_async() -> Tuple[List[Any], Optional[AsyncExitStack]]:
    """
    Async function to create an MCPToolset for Home Assistant's MCP Server using ADK 0.3.0 API.
    
    Returns:
        Tuple[List[MCPTool], AsyncExitStack]: The list of tools and exit stack, or ([], None) if configuration fails
    """
    try:
        # Get connection parameters from environment variables
        ha_mcp_url = os.getenv("HA_MCP_SSE_URL")
        ha_auth_token = os.getenv("HA_AUTH_TOKEN")
        
        if not ha_mcp_url:
            logger.error("Home Assistant MCP URL not found. "
                        "Please set HA_MCP_SSE_URL environment variable.")
            return [], None
            
        if not ha_auth_token:
            logger.error("Home Assistant authentication token not found. "
                        "Please set HA_AUTH_TOKEN environment variable.")
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
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tools, exit_stack = loop.run_until_complete(_create_home_assistant_toolset_async())
        
        # We don't need to close the exit_stack here as the connection should remain open
        # for the lifetime of the application
        
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
    from radbot.tools.mcp_utils import find_home_assistant_entities
    
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
    from radbot.tools.mcp_utils import find_home_assistant_entities
    
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
        
    # Check that TAVILY_API_KEY environment variable is set
    if not os.environ.get("TAVILY_API_KEY"):
        logger.error("TAVILY_API_KEY environment variable not set. The Tavily search tool will not function correctly.")
        # We don't return None here to allow for testing/development without credentials
    
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
            from radbot.tools.memory_tools import search_past_conversations, store_important_information
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