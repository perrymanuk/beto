"""Callback implementations for model requests and responses."""

import logging
import time
from typing import Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest

from radbot.cache.prompt_cache import PromptCache

logger = logging.getLogger(__name__)


def should_skip_caching(llm_request: LlmRequest) -> bool:
    """Determine if caching should be skipped for this request.
    
    Args:
        llm_request: The request to the LLM
        
    Returns:
        True if caching should be skipped, False otherwise
    """
    # Skip if request contains certain keywords indicating time-sensitivity
    if llm_request.contents and any(content.parts for content in llm_request.contents):
        for content in llm_request.contents:
            for part in content.parts:
                if hasattr(part, 'text') and part.text and any(
                    kw in part.text.lower() for kw in [
                        'time', 'weather', 'today', 'now', 'current', 
                        'latest', 'recent', 'update'
                    ]
                ):
                    return True
    
    return False


def cache_prompt_callback(
    cache: PromptCache,
    callback_context: CallbackContext, 
    llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """Check if a cached response exists for this request.
    
    Args:
        cache: PromptCache instance
        callback_context: Callback context
        llm_request: The request to the LLM
        
    Returns:
        Cached LlmResponse if available, otherwise None
    """
    start_time = time.time()
    
    # Skip caching if disabled via config
    if not callback_context.state.get("cache_enabled", True):
        return None
    
    # Skip for certain patterns
    if should_skip_caching(llm_request):
        logger.debug("Skipping cache for time-sensitive request")
        return None
    
    # Generate cache key
    cache_key = cache.generate_cache_key(llm_request)
    
    # Check if cached response exists
    cached_response = cache.get(cache_key)
    if cached_response:
        # Log cache hit
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Cache hit for prompt: {cache_key[:8]}... ({elapsed_ms:.2f}ms)")
        
        # Store cache hit stats in state
        callback_context.state["cache_hits"] = callback_context.state.get("cache_hits", 0) + 1
        callback_context.state["cache_hit_time_ms"] = callback_context.state.get("cache_hit_time_ms", 0) + elapsed_ms
        
        # Return cached response, skipping the actual LLM call
        return cached_response
    
    # Cache miss - store the key in context for the after_model_callback to use
    callback_context.state["pending_cache_key"] = cache_key
    logger.info(f"Cache miss for prompt: {cache_key[:8]}...")
    callback_context.state["cache_misses"] = callback_context.state.get("cache_misses", 0) + 1
    
    # Continue with the LLM call
    return None


def cache_response_callback(
    cache: PromptCache,
    callback_context: CallbackContext, 
    llm_request: LlmRequest, 
    llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """Cache the response if appropriate.
    
    Args:
        cache: PromptCache instance
        callback_context: Callback context
        llm_request: The request to the LLM
        llm_response: The response from the LLM
        
    Returns:
        The original LlmResponse (unmodified)
    """
    # Skip if caching is disabled
    if not callback_context.state.get("cache_enabled", True):
        return llm_response
    
    # Get the pending cache key from state
    cache_key = callback_context.state.get("pending_cache_key")
    if cache_key and llm_response:
        # Skip caching if response is too short (might be an error)
        min_length = 50  # Minimum characters to cache
        response_text = getattr(llm_response, 'text', '')
        if not response_text or len(response_text) < min_length:
            logger.debug(f"Skipping cache for short response: {len(response_text)} chars")
        else:
            # Cache the response
            cache.put(cache_key, llm_response)
            logger.info(f"Cached response for prompt: {cache_key[:8]}...")
        
        # Clean up state
        callback_context.state.pop("pending_cache_key", None)
    
    # Return the response unmodified
    return llm_response