"""
Module-level agent implementation for RadBot.

This module provides a simplified interface for agent creation.
It delegates to the core implementation in radbot.agent.agent.
"""
import logging
import os
from typing import Any, Dict, List, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

# Import core components from the agent package
from radbot.agent.agent import (
    RadBotAgent, 
    AgentFactory,
    create_agent as _create_agent,
    create_runner,
    SessionService
)

# Import useful ADK components for direct use
from google.adk.agents import Agent, QueryResponse
from google.adk.tools.tool_context import ToolContext
from google.protobuf.json_format import MessageToDict

# Define agent error handler for convenience
def agent_error_handler(e: Exception) -> Dict[str, Any]:
    """Handle agent errors by returning a user-friendly error message."""
    logger.error(f"Agent error: {e}", exc_info=True)
    return {
        "error": f"I encountered an error: {str(e)}. Please try again or contact support if the issue persists."
    }


def create_agent(
    model: str = None,
    tools: Optional[List[Any]] = None,
    session_service: Optional[SessionService] = None,
    instruction_name: str = "main_agent",
    name: str = "beto",
    include_memory_tools: bool = True,
    register_tools: bool = True,
    for_web: bool = False
) -> Union[RadBotAgent, Agent]:
    """
    Create a RadBot agent with all necessary tools and configuration.
    
    This function is a wrapper around the core implementation in radbot.agent.agent.
    
    Args:
        model: Model to use (if None, defaults to config's main_model)
        tools: List of tools to add to the agent
        session_service: Optional session service for conversation state
        instruction_name: Name of instruction to load from config
        name: Name for the agent
        include_memory_tools: If True, includes memory tools automatically
        register_tools: Whether to register common tool handlers
        for_web: If True, returns an ADK Agent for web interface
        
    Returns:
        A configured RadBotAgent instance or ADK Agent for web interface
    """
    # We delegate the implementation to the core function
    return _create_agent(
        session_service=session_service,
        tools=tools,
        model=model,
        instruction_name=instruction_name,
        name=name,
        include_memory_tools=include_memory_tools,
        register_tools=register_tools,
        for_web=for_web,
        app_name="beto"
    )


# Module-specific functions for caching
def register_cache_callbacks(agent: RadBotAgent) -> RadBotAgent:
    """Register prompt caching callbacks with the agent.
    
    Args:
        agent: The RadBotAgent instance
        
    Returns:
        The same agent with callbacks registered
    """
    from radbot.cache.prompt_cache import PromptCache
    from radbot.cache.multi_level_cache import MultiLevelCache
    from radbot.callbacks.model_callbacks import (
        cache_prompt_callback, 
        cache_response_callback,
        should_skip_caching
    )
    from radbot.config.cache_settings import get_cache_config
    
    # Get cache configuration
    cache_config = get_cache_config()
    
    # Skip if caching is disabled
    if not cache_config.get("enabled", False):
        logger.info("Prompt caching is disabled, skipping cache callback registration")
        return agent
        
    try:
        # Initialize cache components
        prompt_cache = PromptCache(max_cache_size=cache_config.get("max_size", 1000))
        
        # Initialize Redis if configured
        redis_client = None
        if "redis_url" in cache_config and cache_config["redis_url"]:
            try:
                import redis
                redis_url = cache_config["redis_url"]
                redis_client = redis.from_url(redis_url)
                logger.info(f"Redis client initialized for global cache: {redis_url}")
            except (ImportError, Exception) as e:
                logger.warning(f"Could not initialize Redis client: {e}")
                logger.info("Continuing with session-level caching only")
    
        # Create multi-level cache
        multi_level_cache = MultiLevelCache(redis_client)
        
        # Create wrapped callbacks for the multi-level cache
        def before_model_cb(callback_context, llm_request):
            # Skip caching if disabled
            if not cache_config.get("enabled", False):
                logger.debug("Caching is disabled, skipping cache check")
                return None
            
            # Generate cache key
            cache_key = prompt_cache.generate_cache_key(llm_request)
            logger.info(f"CACHE KEY: {cache_key}")
            
            # Skip check if selective caching is enabled and content should be skipped
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
            if not cache_config.get("enabled", False):
                return llm_response
            
            # Get the pending cache key
            cache_key = callback_context.state.get("pending_cache_key")
            if cache_key and llm_response:
                # Get minimum token threshold for caching
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
            
        # Register the callbacks with the agent's builder
        if hasattr(agent, 'builder'):
            agent.builder = (
                agent.builder
                .set_before_model_callback(before_model_cb)
                .set_after_model_callback(after_model_cb)
            )
            logger.info("Registered cache callbacks with agent builder")
            
            # Make telemetry accessible
            setattr(ToolContext, "cache_telemetry", multi_level_cache.telemetry)
            
        else:
            logger.warning("Agent does not have a builder, cannot register cache callbacks")
            
    except Exception as e:
        logger.warning(f"Failed to register cache callbacks: {str(e)}")
        
    return agent

# Re-export these components for backward compatibility
from radbot.agent.agent import RadBotAgent, AgentFactory, create_runner