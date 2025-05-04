# Prompt Caching System

This document outlines the implementation of a prompt caching system for the Radbot agent framework to optimize performance, reduce costs, and improve scalability.

## Current Issues

- Every user query triggers a new LLM API call, even for identical or similar prompts
- Unnecessary API costs for repeated queries
- Higher latency for users awaiting responses
- Inconsistent answers for identical questions
- Reduced scalability under high load

## Solution Approach

We'll implement a comprehensive prompt caching system with three key components:

1. **Callback-Based Caching Mechanism**: Using ADK's callback system to intercept LLM requests
2. **Cache Performance Telemetry**: Monitoring cache efficiency to optimize strategies
3. **Multi-Level Caching Strategy**: Using session state for session-specific caching and an external persistent store for cross-session caching

## Implementation

### 1. Callback-Based Caching Mechanism

#### 1.1 Cache Structure

```python
# radbot/cache/prompt_cache.py

import hashlib
import json
import time
from typing import Dict, Optional, Any
from google.adk.models import LlmResponse, LlmRequest

class PromptCache:
    """Manages caching of LLM responses to reduce duplicate API calls."""
    
    def __init__(self, max_cache_size: int = 1000):
        """Initialize the prompt cache.
        
        Args:
            max_cache_size: Maximum number of responses to cache
        """
        self.cache: Dict[str, LlmResponse] = {}
        self.max_cache_size = max_cache_size
    
    def generate_cache_key(self, llm_request: LlmRequest) -> str:
        """Generate a cache key for the request.
        
        Args:
            llm_request: The LLM request to generate a key for
            
        Returns:
            A string cache key
        """
        # Normalize and hash relevant parts of the request
        key_components = {
            "model": llm_request.model,
            "contents": json.dumps([self._normalize_content(c) for c in llm_request.contents]),
            "config": json.dumps(self._normalize_config(llm_request.config))
        }
        
        # Create a deterministic string from the components
        key_str = json.dumps(key_components, sort_keys=True)
        
        # Generate a hash for the key
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()
    
    def _normalize_content(self, content: Any) -> Dict[str, Any]:
        """Normalize content for consistent key generation."""
        # Extract just the content role and text
        return {
            "role": getattr(content, "role", "unknown"),
            "parts": [{"text": getattr(p, "text", str(p))} for p in getattr(content, "parts", [])]
        }
    
    def _normalize_config(self, config: Any) -> Dict[str, Any]:
        """Normalize config for consistent key generation."""
        # Extract relevant config parameters
        normalized = {}
        if hasattr(config, 'temperature'):
            normalized["temperature"] = config.temperature
        if hasattr(config, 'top_p'):
            normalized["top_p"] = config.top_p
        if hasattr(config, 'top_k'):
            normalized["top_k"] = config.top_k
        return normalized
    
    def get(self, key: str) -> Optional[LlmResponse]:
        """Get a cached response by key.
        
        Args:
            key: Cache key
            
        Returns:
            Cached LlmResponse or None if not found
        """
        return self.cache.get(key)
    
    def put(self, key: str, response: LlmResponse) -> None:
        """Put a response in the cache.
        
        Args:
            key: Cache key
            response: LlmResponse to cache
        """
        # If cache is full, remove an entry
        if len(self.cache) >= self.max_cache_size:
            # Simple approach: remove a random entry
            self.cache.pop(next(iter(self.cache)))
        
        self.cache[key] = response
```

#### 1.2 Callbacks Implementation

```python
# radbot/callbacks/model_callbacks.py

import logging
import time
from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from radbot.cache.prompt_cache import PromptCache

logger = logging.getLogger(__name__)

def should_skip_caching(llm_request: LlmRequest) -> bool:
    """
    Determine if caching should be skipped for this request.
    
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
    """
    Check if a cached response exists for this request.
    
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
    """
    Cache the response if appropriate.
    
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
```

### 2. Cache Performance Telemetry

```python
# radbot/cache/cache_telemetry.py

import logging
import time
from typing import Dict, Any

class CacheTelemetry:
    """
    Tracks and reports on cache performance metrics.
    """
    
    def __init__(self):
        """Initialize the telemetry collector."""
        self.logger = logging.getLogger(__name__)
        self.hits = 0
        self.misses = 0
        self.hit_latency_total = 0  # ms
        self.miss_latency_total = 0  # ms
        self.estimated_token_savings = 0
        self.entry_hit_counts = {}  # cache_key -> hit_count
        self.start_time = time.time()
        
    def record_hit(self, cache_key: str, latency_ms: float, token_count: int = 0) -> None:
        """
        Record a cache hit.
        
        Args:
            cache_key: The cache key that was hit
            latency_ms: Time taken to retrieve the cached response
            token_count: Estimated token count saved
        """
        self.hits += 1
        self.hit_latency_total += latency_ms
        self.estimated_token_savings += token_count
        self.entry_hit_counts[cache_key] = self.entry_hit_counts.get(cache_key, 0) + 1
        
    def record_miss(self, cache_key: str, latency_ms: float) -> None:
        """
        Record a cache miss.
        
        Args:
            cache_key: The cache key that was missed
            latency_ms: Time taken to determine the miss
        """
        self.misses += 1
        self.miss_latency_total += latency_ms
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Get current statistics.
        
        Returns:
            Dictionary of statistics
        """
        total_requests = self.hits + self.misses
        if total_requests == 0:
            return {"error": "No cache activity recorded"}
            
        hit_rate = self.hits / total_requests
        avg_hit_latency = self.hit_latency_total / max(1, self.hits)
        avg_miss_latency = self.miss_latency_total / max(1, self.misses)
        latency_reduction = 1 - (avg_hit_latency / avg_miss_latency) if self.misses > 0 else 0
        uptime_seconds = time.time() - self.start_time
        
        return {
            "hit_rate": hit_rate,
            "miss_rate": 1 - hit_rate,
            "total_requests": total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "avg_hit_latency_ms": avg_hit_latency,
            "avg_miss_latency_ms": avg_miss_latency,
            "latency_reduction": latency_reduction,
            "estimated_token_savings": self.estimated_token_savings,
            "most_frequent_entries": sorted(self.entry_hit_counts.items(), 
                                           key=lambda x: x[1], reverse=True)[:10],
            "uptime_seconds": uptime_seconds
        }
```

### 3. Multi-Level Caching Strategy

```python
# radbot/cache/multi_level_cache.py

import logging
import time
import json
from typing import Dict, Any, Optional
from google.adk.models import LlmResponse
from radbot.cache.cache_telemetry import CacheTelemetry

logger = logging.getLogger(__name__)

class MultiLevelCache:
    """
    Implements a two-level caching strategy with session-specific and global caches.
    """
    
    def __init__(self, redis_client=None):
        """
        Initialize the multi-level cache.
        
        Args:
            redis_client: Optional Redis client for global cache
        """
        self.telemetry = CacheTelemetry()
        self.redis_client = redis_client  # Optional, for global cache
        
    def get(self, cache_key: str, session_state: Dict[str, Any]) -> Optional[LlmResponse]:
        """
        Retrieve a cached response from the appropriate cache level.
        
        Args:
            cache_key: The cache key
            session_state: Current session state for session-specific cache
            
        Returns:
            Cached LlmResponse if found, None otherwise
        """
        start_time = time.time()
        
        # Check session-specific cache first
        session_cache = session_state.get("prompt_cache", {})
        cached_response = session_cache.get(cache_key)
        
        if cached_response:
            # Session cache hit
            latency_ms = (time.time() - start_time) * 1000
            self.telemetry.record_hit(cache_key, latency_ms, 
                                     self._estimate_tokens(cached_response))
            logger.debug(f"Session cache hit for key: {cache_key[:8]}...")
            return cached_response
            
        # Check global cache if available
        if self.redis_client:
            try:
                redis_cached = self.redis_client.get(f"prompt_cache:{cache_key}")
                if redis_cached:
                    # Global cache hit
                    cached_response = self._deserialize_response(redis_cached)
                    # Also update session cache for faster future access
                    if "prompt_cache" not in session_state:
                        session_state["prompt_cache"] = {}
                    session_state["prompt_cache"][cache_key] = cached_response
                    
                    latency_ms = (time.time() - start_time) * 1000
                    self.telemetry.record_hit(cache_key, latency_ms, 
                                             self._estimate_tokens(cached_response))
                    logger.debug(f"Global cache hit for key: {cache_key[:8]}...")
                    return cached_response
            except Exception as e:
                logger.warning(f"Error accessing Redis cache: {e}")
        
        # Cache miss
        latency_ms = (time.time() - start_time) * 1000
        self.telemetry.record_miss(cache_key, latency_ms)
        return None
        
    def put(self, cache_key: str, response: LlmResponse, session_state: Dict[str, Any], ttl: int = 3600) -> None:
        """
        Store a response in the appropriate cache level(s).
        
        Args:
            cache_key: The cache key
            response: LlmResponse to cache
            session_state: Current session state for session-specific cache
            ttl: Time-to-live in seconds for the global cache entry
        """
        # Update session-specific cache
        if "prompt_cache" not in session_state:
            session_state["prompt_cache"] = {}
        session_state["prompt_cache"][cache_key] = response
        logger.debug(f"Cached in session cache: {cache_key[:8]}...")
        
        # Update global cache if available
        if self.redis_client:
            try:
                serialized = self._serialize_response(response)
                self.redis_client.setex(f"prompt_cache:{cache_key}", ttl, serialized)
                logger.debug(f"Cached in global cache: {cache_key[:8]}...")
            except Exception as e:
                logger.warning(f"Error updating Redis cache: {e}")
                
    def _serialize_response(self, response: LlmResponse) -> str:
        """
        Serialize LlmResponse for storage.
        
        Args:
            response: LlmResponse object to serialize
            
        Returns:
            JSON string representation
        """
        # This is a simplified implementation that would need to be adapted
        # based on the actual structure of LlmResponse
        response_dict = {
            "text": getattr(response, "text", ""),
            "content": self._serialize_content(getattr(response, "content", None))
        }
        return json.dumps(response_dict)
        
    def _serialize_content(self, content):
        """Serialize content object to dict."""
        if not content:
            return None
        
        result = {"role": getattr(content, "role", "unknown")}
        if hasattr(content, "parts"):
            result["parts"] = []
            for part in content.parts:
                if hasattr(part, "text"):
                    result["parts"].append({"text": part.text})
        
        return result
        
    def _deserialize_response(self, serialized: str) -> LlmResponse:
        """
        Deserialize stored data to LlmResponse.
        
        Args:
            serialized: JSON string representation
            
        Returns:
            LlmResponse object
        """
        # This is a simplified implementation that would need to be adapted
        # based on the actual structure of LlmResponse
        from google.adk.models import LlmResponse
        from google.genai import types
        
        response_dict = json.loads(serialized)
        content = None
        
        if "content" in response_dict and response_dict["content"]:
            content_dict = response_dict["content"]
            parts = []
            
            if "parts" in content_dict:
                for part_dict in content_dict["parts"]:
                    if "text" in part_dict:
                        parts.append(types.Part(text=part_dict["text"]))
            
            content = types.Content(
                role=content_dict.get("role", "model"),
                parts=parts
            )
        
        return LlmResponse(content=content)
        
    def _estimate_tokens(self, response: LlmResponse) -> int:
        """
        Estimate token count for a response.
        
        Args:
            response: LlmResponse object
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on text length
        if hasattr(response, 'text'):
            return len(response.text) // 4  # Rough estimate: 4 chars per token
        return 0
```

### 4. Command-Line Utility

```python
# radbot/utils/cache_status.py

import argparse
import json
import sys
from typing import Dict, Any

from radbot.agent import create_agent
from google.adk.tools.tool_context import ToolContext

def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache performance statistics.
    
    Returns:
        Dictionary of statistics
    """
    if hasattr(ToolContext, "cache_telemetry"):
        return ToolContext.cache_telemetry.get_stats()
    else:
        return {"error": "Cache telemetry not available"}

def print_stats(stats: Dict[str, Any], json_format: bool = False) -> None:
    """
    Print cache performance statistics.
    
    Args:
        stats: Statistics dictionary
        json_format: Whether to print in JSON format
    """
    if json_format:
        print(json.dumps(stats, indent=2))
    else:
        print("Cache Performance Statistics")
        print("===========================")
        
        if "error" in stats:
            print(f"Error: {stats['error']}")
            return
        
        print(f"Total requests:      {stats.get('total_requests', 0)}")
        print(f"Cache hit rate:      {stats.get('hit_rate', 0) * 100:.1f}%")
        print(f"Cache miss rate:     {stats.get('miss_rate', 0) * 100:.1f}%")
        print(f"Avg hit latency:     {stats.get('avg_hit_latency_ms', 0):.1f} ms")
        print(f"Avg miss latency:    {stats.get('avg_miss_latency_ms', 0):.1f} ms")
        print(f"Latency reduction:   {stats.get('latency_reduction', 0) * 100:.1f}%")
        print(f"Est. token savings:  {stats.get('estimated_token_savings', 0)}")
        print(f"Uptime:              {stats.get('uptime_seconds', 0) / 60:.1f} minutes")
        
        print("\nMost Frequent Cache Entries:")
        for key, hits in stats.get('most_frequent_entries', []):
            print(f"  {key[:8]}... : {hits} hits")

def main() -> None:
    """Main function for the cache status utility."""
    parser = argparse.ArgumentParser(description="Get cache performance statistics")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()
    
    # Get stats
    stats = get_cache_stats()
    
    # Print stats
    print_stats(stats, args.json)

if __name__ == "__main__":
    main()
```

### 5. Agent Integration

```python
# Updated radbot/agent.py (changes only, not entire file)

# Add imports
import os
from radbot.cache.prompt_cache import PromptCache
from radbot.cache.multi_level_cache import MultiLevelCache
from radbot.callbacks.model_callbacks import cache_prompt_callback, cache_response_callback

def create_agent(tools=None):
    # ... existing code ...
    
    # Initialize cache system with Redis if available
    redis_client = None
    if os.environ.get("REDIS_URL"):
        try:
            import redis
            redis_client = redis.from_url(os.environ.get("REDIS_URL"))
            logger.info(f"Redis client initialized for global cache")
        except (ImportError, Exception) as e:
            logger.warning(f"Could not initialize Redis client: {e}")
    
    # Create cache system    
    prompt_cache = PromptCache()
    multi_level_cache = MultiLevelCache(redis_client)
    
    # Create wrapped callbacks
    def before_model_cb(callback_context, llm_request):
        return cache_prompt_callback(prompt_cache, callback_context, llm_request)
        
    def after_model_cb(callback_context, llm_request, llm_response):
        return cache_response_callback(prompt_cache, callback_context, llm_request, llm_response)
    
    # Create agent with callbacks
    agent = Agent(
        name="radbot_web",
        model=model_name,
        instruction=instruction,
        description="The main agent that handles user requests with memory capabilities.",
        tools=all_tools,
        before_model_callback=before_model_cb,
        after_model_callback=after_model_cb
    )
    
    # Make telemetry accessible
    from google.adk.tools.tool_context import ToolContext
    setattr(ToolContext, "cache_telemetry", multi_level_cache.telemetry)
    
    # ... rest of existing code ...
    
    return agent
```

## Configuration

The caching system can be configured through environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `RADBOT_CACHE_ENABLED` | Enable/disable caching | `true` |
| `RADBOT_CACHE_TTL` | Time-to-live for cached entries (seconds) | `3600` |
| `RADBOT_CACHE_MAX_SIZE` | Maximum entries in session cache | `1000` |
| `RADBOT_CACHE_SELECTIVE` | Only cache eligible requests | `true` |
| `RADBOT_CACHE_MIN_TOKENS` | Minimum tokens in response to cache | `50` |
| `REDIS_URL` | Redis connection URL for global cache | `None` |

## Expected Outcomes

- 30-60% reduction in response latency for cached queries
- 20-40% overall reduction in API calls
- Improved throughput under high load
- Estimated 20-30% reduction in LLM token usage
- Consistent responses for identical queries

## Testing

To validate the caching implementation, we'll need tests to ensure:

1. Cache key generation is consistent for identical requests
2. Caching and retrieval work correctly
3. Telemetry accurately tracks hits and misses
4. Multi-level caching works with both session state and Redis
5. Callbacks integrate properly with the ADK system

## Monitoring and Evaluation

The command-line utility (`radbot/utils/cache_status.py`) provides insights into cache performance:

```bash
python -m radbot.utils.cache_status
```

This will display current statistics including hit rate, latency reduction, and estimated token savings.

## Extensions

Future enhancements could include:

1. More sophisticated cache eviction policies (LRU, LFU)
2. Enhanced cache key generation with semantic similarity
3. Automatic cache warming for common queries
4. Proactive invalidation for time-sensitive content
5. User-specific caching preferences
