# Qdrant Compatibility Fix

## Issue

When using `crawl4ai_query` with our vector database implementation, we encountered the following error:

```
ERROR - crawl4ai_vector_store.py:408 - Error counting documents: 'QdrantClient' object has no attribute 'has_collection'
```

This error occurred despite documents being successfully ingested into the vector database. The issue was in our `count_documents()` method in `crawl4ai_vector_store.py`, which was using a `has_collection()` method that doesn't exist in our version of the Qdrant client.

## Investigation

The error suggested that the Qdrant client library we were using didn't have the `has_collection` method that our code was trying to call. This happens because different versions of Qdrant client have different APIs.

The logs showed:
1. Content was successfully ingested (169 points were stored)
2. But when trying to search, the system reported that the vector store was empty
3. This was due to the failed `has_collection` check in the `count_documents()` method

## Solution

We implemented two changes:

1. Modified the `count_documents()` method to use a more compatible approach for checking if a collection exists:

```python
def count_documents(self) -> int:
    """Return the number of documents in the collection."""
    try:
        # Check if collection exists by getting all collections
        collections = self.client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if self.collection_name not in collection_names:
            logger.warning(f"Collection '{self.collection_name}' doesn't exist yet")
            return 0
            
        # Collection exists, count the documents
        count_response = self.client.count(self.collection_name)
        count = count_response.count if hasattr(count_response, 'count') else 0
        
        if count == 0:
            logger.warning(f"Collection '{self.collection_name}' exists but is empty")
        else:
            logger.info(f"Collection '{self.collection_name}' has {count} documents")
        return count
    except Exception as e:
        logger.error(f"Error counting documents: {str(e)}")
        return 0
```

2. Pinned the Qdrant client version in `pyproject.toml` to ensure consistent behavior:

```toml
dependencies = [
    "google-adk>=0.3.0",
    "google-generativeai>=0.8.5",
    "qdrant-client==1.7.0",  # Pinned to a version that works well with our implementation
    # ... other dependencies
]
```

## Key Improvements

1. **More Robust Collection Check**: Instead of using `has_collection()`, we now retrieve all collections and check if our target collection is in the list.
2. **Safer Count Access**: We added a check to safely access the `count` attribute on the response object.
3. **Version Pinning**: We pinned the Qdrant client version to prevent future API compatibility issues.

These changes ensure that our code works consistently with the specified Qdrant client version and is more robust against API changes.