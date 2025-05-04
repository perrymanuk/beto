"""MultiLevelCache for implementing a two-level caching strategy."""

import logging
import time
import json
from typing import Dict, Any, Optional

from google.adk.models import LlmResponse
from radbot.cache.cache_telemetry import CacheTelemetry

logger = logging.getLogger(__name__)


class MultiLevelCache:
    """Implements a two-level caching strategy with session-specific and global caches."""
    
    def __init__(self, redis_client=None):
        """Initialize the multi-level cache.
        
        Args:
            redis_client: Optional Redis client for global cache
        """
        self.telemetry = CacheTelemetry()
        self.redis_client = redis_client  # Optional, for global cache
        
    def get(self, cache_key: str, session_state: Dict[str, Any]) -> Optional[LlmResponse]:
        """Retrieve a cached response from the appropriate cache level.
        
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
            logger.info(f"Session cache hit for key: {cache_key}")
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
                    logger.info(f"Global cache hit for key: {cache_key}")
                    return cached_response
            except Exception as e:
                logger.warning(f"Error accessing Redis cache: {e}")
        
        # Cache miss
        latency_ms = (time.time() - start_time) * 1000
        self.telemetry.record_miss(cache_key, latency_ms)
        return None
        
    def put(self, cache_key: str, response: LlmResponse, session_state: Dict[str, Any], ttl: int = 3600) -> None:
        """Store a response in the appropriate cache level(s).
        
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
        logger.info(f"Cached in session cache: {cache_key}")
        
        # Update global cache if available
        if self.redis_client:
            try:
                serialized = self._serialize_response(response)
                self.redis_client.setex(f"prompt_cache:{cache_key}", ttl, serialized)
                logger.info(f"Cached in global cache: {cache_key}")
            except Exception as e:
                logger.warning(f"Error updating Redis cache: {e}")
                
    def _serialize_response(self, response: LlmResponse) -> str:
        """Serialize LlmResponse for storage.
        
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
        """Deserialize stored data to LlmResponse.
        
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
        """Estimate token count for a response.
        
        Args:
            response: LlmResponse object
            
        Returns:
            Estimated token count
        """
        # Simple estimation based on text length
        if hasattr(response, 'text'):
            return len(response.text) // 4  # Rough estimate: 4 chars per token
        return 0