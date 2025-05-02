"""
Simple subprocess-based curl client for Qdrant.

This provides a minimal set of Qdrant operations implemented by calling curl
as a subprocess, since Python's networking stack appears to have connectivity
issues but curl works fine.
"""

import json
import subprocess
import logging
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class CurlQdrantClient:
    """
    Minimal Qdrant client implementation using curl subprocess calls.
    Only implements operations needed for memory functionality.
    """
    
    def __init__(self, url: str):
        """Initialize with Qdrant server URL."""
        self.url = url.rstrip("/")
        logger.info(f"Initialized CurlQdrantClient with URL: {self.url}")
        
        # Test connection
        try:
            version = self._curl_get("/")
            logger.info(f"Connected to Qdrant {version.get('version', 'unknown')}")
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant: {str(e)}")
            raise
    
    def _curl_get(self, path: str) -> Dict[str, Any]:
        """Execute a GET request using curl."""
        full_url = f"{self.url}{path}"
        try:
            result = subprocess.run(
                ["curl", "-s", full_url],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl GET request failed: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def _curl_post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a POST request using curl."""
        full_url = f"{self.url}{path}"
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "POST", "-H", "Content-Type: application/json", 
                 "-d", json.dumps(data), full_url],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl POST request failed: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def _curl_put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a PUT request using curl."""
        full_url = f"{self.url}{path}"
        try:
            result = subprocess.run(
                ["curl", "-s", "-X", "PUT", "-H", "Content-Type: application/json", 
                 "-d", json.dumps(data), full_url],
                capture_output=True,
                text=True,
                check=True
            )
            return json.loads(result.stdout)
        except subprocess.CalledProcessError as e:
            logger.error(f"Curl PUT request failed: {e.stderr}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    # Collection management
    
    def get_collections(self):
        """Get list of collections."""
        response = self._curl_get("/collections")
        
        # Format it like the Qdrant client would return
        class Collection:
            def __init__(self, name):
                self.name = name
        
        class CollectionsResponse:
            def __init__(self, collections_data):
                self.collections = [Collection(c["name"]) for c in collections_data.get("collections", [])]
        
        return CollectionsResponse(response)
    
    def create_collection(self, collection_name: str, vectors_config: Dict[str, Any]):
        """Create a new collection."""
        # Convert the vectors_config object to a proper dict
        config_dict = {
            "vectors": {
                "size": vectors_config.size,
                "distance": vectors_config.distance.name.lower()
            },
            "optimizers_config": {
                "indexing_threshold": 10000
            },
            "on_disk_payload": True
        }
        
        return self._curl_put(f"/collections/{collection_name}", config_dict)
    
    def create_payload_index(self, collection_name: str, field_name: str, field_schema):
        """Create a payload index in a collection."""
        index_type = field_schema.name.lower()
        
        payload = {
            "field_name": field_name,
            "field_schema": index_type
        }
        
        return self._curl_post(f"/collections/{collection_name}/index", payload)
    
    def upsert(self, collection_name: str, points, wait: bool = True):
        """Insert or update points in a collection."""
        # Convert PointStruct objects to dicts
        points_data = []
        for point in points:
            point_dict = {
                "id": point.id,
                "vector": point.vector,
            }
            if hasattr(point, 'payload') and point.payload:
                point_dict["payload"] = point.payload
            points_data.append(point_dict)
        
        payload = {"points": points_data, "wait": wait}
        return self._curl_put(f"/collections/{collection_name}/points", payload)
    
    def search(self, collection_name: str, query_vector, query_filter=None, limit: int = 10):
        """Search for similar vectors in a collection."""
        payload = {
            "vector": query_vector,
            "limit": limit,
            "with_payload": True,
            "with_vectors": False,
        }
        
        if query_filter:
            # Convert filter object to dict format expected by Qdrant REST API
            filter_dict = {"must": []}
            for condition in query_filter.must:
                if hasattr(condition, 'key'):
                    # Field condition
                    field_condition = {"key": condition.key}
                    
                    if hasattr(condition, 'match') and condition.match:
                        # Match value
                        field_condition["match"] = {"value": condition.match.value}
                    
                    if hasattr(condition, 'range') and condition.range:
                        # Range condition
                        range_dict = {}
                        if hasattr(condition.range, 'gt'):
                            range_dict["gt"] = condition.range.gt
                        if hasattr(condition.range, 'gte'):
                            range_dict["gte"] = condition.range.gte
                        if hasattr(condition.range, 'lt'):
                            range_dict["lt"] = condition.range.lt
                        if hasattr(condition.range, 'lte'):
                            range_dict["lte"] = condition.range.lte
                        
                        field_condition["range"] = range_dict
                    
                    filter_dict["must"].append(field_condition)
            
            payload["filter"] = filter_dict
        
        response = self._curl_post(f"/collections/{collection_name}/points/search", payload)
        
        # Format the response like the Qdrant client would return
        class ScoredPoint:
            def __init__(self, point_data):
                self.id = point_data.get("id")
                self.score = point_data.get("score")
                self.payload = point_data.get("payload", {})
        
        return [ScoredPoint(p) for p in response.get("result", [])]