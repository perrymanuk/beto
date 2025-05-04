"""
Radbot agent implementation.
"""

import logging
import os
from typing import Any, Dict, List, Optional

from google.adk.agent import Agent, AgentBuilder
from google.adk.agents import QueryResponse
from google.adk.tools import FunctionTool
from google.protobuf.json_format import MessageToDict
from google.adk.tools.tool_context import ToolContext

from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

from radbot.tools.crawl4ai.crawl4ai_query import create_crawl4ai_query_tool
from radbot.tools.get_weather import create_weather_tool
from radbot.tools.memory import search_past_conversations, store_important_information
from radbot.tools.mcp import (
    create_fileserver_toolset,
    handle_fileserver_tool_call,
)
from radbot.tools.crawl4ai.mcp_crawl4ai_client import (
    create_crawl4ai_toolset,
    handle_crawl4ai_tool_call,
)
from radbot.cache.prompt_cache import PromptCache
from radbot.cache.multi_level_cache import MultiLevelCache
from radbot.callbacks.model_callbacks import cache_prompt_callback, cache_response_callback, should_skip_caching
from radbot.config.cache_settings import get_cache_config

logger = logging.getLogger(__name__)


def agent_error_handler(e: Exception) -> Dict[str, Any]:
    """Handle agent errors by returning a user-friendly error message."""
    logger.error(f"Agent error: {e}", exc_info=True)
    return {
        "error": f"I encountered an error: {str(e)}. Please try again or contact support if the issue persists."
    }


def create_agent(model: str = "gemini-1.5-pro-latest") -> Agent:
    """
    Create a basic agent with default tools.

    Args:
        model: The model to use for the agent.

    Returns:
        An Agent instance.
    """
    # List of basic tools available to all agents
    basic_tools = [
        create_weather_tool(),
        FunctionTool(name="transfer_to_agent", description="Transfer to another agent"),
    ]

    # Add Crawl4AI query tool for searching ingested content
    basic_tools.append(create_crawl4ai_query_tool())

    # Try to add MCP fileserver tools
    try:
        logger.info("Setting up MCP fileserver tools...")
        fileserver_tools = create_fileserver_toolset()
        if fileserver_tools:
            basic_tools.extend(fileserver_tools)
        else:
            logger.warning("MCP fileserver tools not available")
    except Exception as e:
        logger.warning(f"Failed to create MCP fileserver tools: {e}")

    # Try to add Crawl4AI toolset
    logger.info("Creating Crawl4AI toolset...")
    crawl4ai_api_url = os.environ.get(
        "CRAWL4AI_API_URL", "https://crawl4ai.demonsafe.com"
    )
    logger.info(f"Crawl4AI: Using API URL {crawl4ai_api_url}")
    crawl4ai_api_token = os.environ.get("CRAWL4AI_API_TOKEN", "")

    try:
        crawl4ai_tools = create_crawl4ai_toolset(
            api_url=crawl4ai_api_url, api_token=crawl4ai_api_token
        )
        if crawl4ai_tools:
            basic_tools.extend(crawl4ai_tools)
        else:
            logger.warning("Crawl4AI tools not available (returned None)")
    except Exception as e:
        logger.warning(f"Failed to create Crawl4AI tools: {e}")
        
    # Initialize cache system with Redis if available
    cache_config = get_cache_config()
    redis_client = None
    
    # Enable logging for cache debugging
    logging.getLogger('radbot.cache').setLevel(logging.DEBUG)
    logging.getLogger('radbot.callbacks').setLevel(logging.DEBUG)
    
    logger.info(f"Cache config: {cache_config}")
    
    # Force these values in the config
    cache_config["enabled"] = True
    cache_config["selective"] = False  # Don't skip any messages based on content
    
    if "redis_url" in cache_config and cache_config["redis_url"]:
        try:
            import redis
            redis_url = cache_config["redis_url"]
            redis_client = redis.from_url(redis_url)
            logger.info(f"Redis client initialized for global cache: {redis_url}")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize Redis client: {e}")
            # If Redis fails, don't disable caching
            logger.info("Continuing with session-level caching only")
    else:
        logger.info("No Redis URL configured, using session-level caching only")
    
    # Create cache system    
    prompt_cache = PromptCache(max_cache_size=cache_config["max_size"])
    multi_level_cache = MultiLevelCache(redis_client)
    
    # Create wrapped callbacks that use the multi-level cache
    def before_model_cb(callback_context, llm_request):
        # Log the complete raw input for debugging
        if hasattr(llm_request, 'contents') and llm_request.contents:
            user_messages = []
            for content in llm_request.contents:
                if hasattr(content, 'role') and content.role == 'user':
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'text'):
                                user_messages.append(part.text)
            if user_messages:
                logger.info(f"ALL USER MESSAGES: {user_messages}")
                
        # Skip caching if disabled
        if not cache_config["enabled"]:
            logger.debug("Caching is disabled, skipping cache check")
            return None
        
        # Generate cache key
        cache_key = prompt_cache.generate_cache_key(llm_request)
        logger.info(f"CACHE KEY: {cache_key}")
        
        # Skip check if explicitly set to bypass selective caching
        if cache_config.get("selective", True) and should_skip_caching(llm_request):
            logger.debug(f"Skipping cache for time-sensitive content")
            return None
            
        # Try to get from multi-level cache
        cached_response = multi_level_cache.get(cache_key, callback_context.state)
        if cached_response:
            logger.info(f"Cache hit for prompt: {cache_key}")
            return cached_response
        
        # Cache miss - store key for after_model_callback
        logger.info(f"Cache miss for prompt: {cache_key}")
        callback_context.state["pending_cache_key"] = cache_key
        
        return None
        
    def after_model_cb(callback_context, llm_request, llm_response):
        # Skip caching if disabled
        if not cache_config["enabled"]:
            return llm_response
        
        # Debug info about the response
        if hasattr(llm_response, 'text'):
            logger.debug(f"Response text (first 100 chars): {llm_response.text[:100]}...")
        
        # Get the pending cache key
        cache_key = callback_context.state.get("pending_cache_key")
        if cache_key and llm_response:
            # Get minimum token threshold
            min_length = cache_config.get("min_tokens", 50) * 4  # Approximate chars per token
            logger.debug(f"Min length required: {min_length} chars")
            
            # Skip caching if response is too short (might be an error)
            response_text = getattr(llm_response, 'text', '')
            if not response_text:
                logger.debug("Response has no text, skipping cache")
            elif len(response_text) < min_length:
                logger.debug(f"Response too short ({len(response_text)} chars), skipping cache")
            else:
                # Store in multi-level cache
                logger.debug(f"Storing response in cache with key: {cache_key}")
                multi_level_cache.put(
                    cache_key, 
                    llm_response, 
                    callback_context.state,
                    ttl=cache_config.get("ttl", 3600)
                )
                logger.info(f"Cached response for prompt: {cache_key}")
            
            # Clean up state
            callback_context.state.pop("pending_cache_key", None)
        elif not cache_key:
            logger.debug("No pending cache key found in state")
        
        return llm_response

    # Create the agent builder
    agent_builder = (
        AgentBuilder()
        .set_model(model)
        .add_tool_group("basic_tools", basic_tools)
        .set_system_instructions(
            """
You are Radbot, a helpful and intelligent research assistant.

# CAPABILITIES

You have access to several tools:
- Web search and browsing capabilities to find information on the internet
- A knowledge base of crawled content that you can search using the crawl4ai_query tool
- File system access to read and manipulate files
- Tools to fetch weather information and more

## RESEARCH AGENT DELEGATION
If the user asks a complex research question, you can delegate to a specialized research agent.
Use the transfer_to_agent tool to transfer to the "technical_research_agent" for deep technical research.
You may transfer to a research agent when:
- The query requires deep domain knowledge
- The question involves complex technical concepts
- The user requests "advanced" or "deep" research

# GUIDELINES

- Be concise and precise in your responses.
- If you don't know an answer, use your tools to find it.
- Always cite sources when providing information.
- Maintain a professional yet friendly tone.
- Prioritize accuracy over speed.
- For code requests, provide well-documented solutions.
- Respect user privacy and data security.
- When searching the crawled knowledge base, use the crawl4ai_query tool.

# AGENT TRANSFER INSTRUCTION
You can transfer the user to the technical research agent using:
transfer_to_agent(agent_name="technical_research_agent", message="[Optional message for the research agent]")

Similarly, the research agent can transfer back to you using:
transfer_to_agent(agent_name="radbot_web", message="[Optional message for you]")
"""
        )
        .set_error_handler(agent_error_handler)
    )
    
    # Add cache callbacks if enabled
    if cache_config["enabled"]:
        logger.info("LLM response caching is enabled")
        agent_builder = (
            agent_builder
            .set_before_model_callback(before_model_cb)
            .set_after_model_callback(after_model_cb)
        )
    else:
        logger.info("LLM response caching is disabled")
    
    # Build and return the agent
    agent = agent_builder.build()
    
    # Make telemetry accessible if caching is enabled
    if cache_config["enabled"]:
        setattr(ToolContext, "cache_telemetry", multi_level_cache.telemetry)

    # Register custom tool handlers
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

    # Register agent transfer tool
    agent.register_tool_handler(
        "transfer_to_agent",
        lambda params: MessageToDict(QueryResponse(
            transfer_to_agent_response={
                "target_app_name": params["agent_name"],
                "message": params.get("message", ""),
            }
        )),
    )

    # Register Crawl4AI query tool
    agent.register_tool_handler(
        "crawl4ai_query",
        lambda params: {
            "results": search_past_conversations(
                {"query": params["query"], "limit": params.get("limit", 5)}
            )
        },
    )

    return agent
