# Crawl4AI Integration with Vector Search

## Overview

This document outlines the implementation of Crawl4AI integration with Qdrant vector storage for semantic search within the radbot framework.

The integration provides two key capabilities:
1. Crawling and ingesting web content using Crawl4AI
2. Performing semantic search across ingested content using Qdrant vector database

## Problem Solved

The initial implementation faced an issue where the `web_query` function would result in a `400 Bad Request` error when querying the Crawl4AI API:
```
message: "Failed to search knowledge base: 400 Client Error: Bad Request for url: https://crawl4ai.demonsafe.com/md"
```

This occurred because Crawl4AI doesn't natively provide a vector search capability for previously ingested content. The solution implemented uses Qdrant (which is already available in our codebase) to store and search the content extracted by Crawl4AI.

## Implementation Details

### 1. Vector Store Implementation

A new class `Crawl4AIVectorStore` has been implemented in `radbot/tools/crawl4ai_vector_store.py` that:

- Creates and manages a Qdrant collection for storing crawled content
- Provides methods for adding documents (with automatic chunking)
- Supports semantic search using the same embedding model as the memory system
- Handles document deletion and management

The implementation leverages the existing embedding capabilities from `radbot/memory/embedding.py` to maintain consistency with the wider system.

### 2. Modified Crawl4AI Client

The `mcp_crawl4ai_client.py` module has been updated to:

- Store crawled content in the vector database automatically
- Redirect search queries to the vector store instead of the Crawl4AI API
- Format search results for optimal LLM consumption

### 3. Document Chunking Strategy

Documents are split into semantic chunks based on heading structure to preserve context:
- Content is divided at heading boundaries (e.g., `# Heading`)
- Chunks are limited to a maximum size (default: 1000 characters)
- Each chunk is stored as a separate vector in Qdrant with metadata
- This ensures more precise search results by matching smaller, coherent sections of content

### 4. Search Process

The search workflow now follows these steps:
1. User query is converted to a vector embedding
2. Vector similarity search is performed in Qdrant
3. Most relevant chunks are retrieved and formatted
4. Results are returned with source information and relevance scores

## User-Facing Functions

### read_url_as_markdown_directly(url)

Fetches content from a URL, returns it for immediate use, and automatically stores it in the vector database.

```python
result = read_url_as_markdown_directly("https://example.com/docs")
# Returns content and automatically stores in vector DB
```

### ingest_url_to_knowledge_base(url)

Fetches content from a URL and stores it in the vector database for later search, but does not return the content to save context window space.

```python
result = ingest_url_to_knowledge_base("https://example.com/api-docs")
# Stores content for later search without returning it
```

### web_query(query)

Performs semantic search across all previously ingested content stored in the vector database.

```python
results = web_query("How to authenticate API requests?")
# Returns most relevant chunks from ingested content
```

## Configuration

The implementation uses these environment variables:

- `QDRANT_URL` or `QDRANT_HOST`/`QDRANT_PORT`: Qdrant connection details
- `QDRANT_API_KEY`: Authentication for Qdrant (if needed)
- `CRAWL4AI_COLLECTION`: Collection name for storing crawled content (default: "crawl4ai_docs")
- `radbot_EMBED_MODEL`: Embedding model to use (inherits from memory system)
- `CRAWL4AI_API_URL`: URL for the Crawl4AI API (for content extraction)

## Testing

A test script `tools/test_crawl4ai_vector_search.py` is available for verifying:
- Vector store connection
- Document ingestion
- Semantic search functionality

Run the test using:
```bash
python tools/test_crawl4ai_vector_search.py
```

## Future Improvements

Potential enhancements for the implementation:

1. **Incremental Updates**: Add capability to update existing documents instead of replacing them entirely
2. **Multi-URL Ingestion**: Support for batch processing of multiple URLs at once
3. **Advanced Filtering**: Allow searching within specific domains or date ranges
4. **Relevance Tuning**: Adjustable relevance thresholds and ranking parameters
5. **Web UI**: Simple interface for browsing and managing ingested content