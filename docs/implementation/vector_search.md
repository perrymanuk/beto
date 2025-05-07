# Vector Search with Crawl4AI Integration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document provides implementation details for the integration between Crawl4AI web crawling and Qdrant vector database for semantic search capabilities in radbot.

## Overview

The implementation enhances radbot with the ability to ingest web content via Crawl4AI and perform semantic search using Qdrant vector database. This overcomes the limitations of Crawl4AI's native search functionality (which was causing 400 Bad Request errors) by storing the extracted content in a vector database optimized for semantic search.

## Components

### 1. Vector Storage (crawl4ai_vector_store.py)

The `Crawl4AIVectorStore` class in `radbot/tools/crawl4ai_vector_store.py` provides:

- **Storage**: Methods to add document content to Qdrant, split into semantic chunks
- **Search**: Vector search capabilities using cosine similarity
- **Management**: Document deletion, counting, and collection management
- **Embedding**: Content embedding using the same embedding model as the memory system

### 2. Crawl4AI Client Integration (mcp_crawl4ai_client.py)

The updated client in `radbot/tools/mcp_crawl4ai_client.py` now:

- **Automatic Embedding**: Automatically stores fetched content in the vector database
- **Improved Search**: Replaced direct API calls with vector search
- **Response Formatting**: Returns search results formatted as markdown

## API Functions

### Document Ingestion

#### read_url_as_markdown_directly(url)
- Fetches content from URL and returns it for immediate use
- Automatically stores the content in the vector database
- Returns the original content and metadata about the storage operation

#### ingest_url_to_knowledge_base(url)
- Fetches content from URL and stores it in the vector database
- Does NOT return the actual content to save context window space
- Returns metadata about the ingestion process

### Document Search

#### web_query(query)
- Performs semantic search in the vector database
- Returns formatted markdown with the most relevant chunks
- Includes source URLs and similarity scores

## Implementation Details

### Document Chunking

Documents are split into semantic chunks based on headings to ensure:
- Better context preservation within chunks
- More precise search results
- Content pieces of manageable size

```python
def split_into_chunks(self, markdown_text: str, max_chunk_size: int = 1000) -> List[str]:
    """Split markdown text into chunks based on headings."""
    chunks = re.split(r'(#{1,6}\s+.*)', markdown_text)
    
    processed_chunks = []
    current_chunk = ""
    
    for chunk in chunks:
        # If this is a heading
        if re.match(r'#{1,6}\s+.*', chunk):
            if current_chunk:
                processed_chunks.append(current_chunk)
            current_chunk = chunk
        else:
            current_chunk += chunk
            
            # Check if chunk is getting too large
            if len(current_chunk) > max_chunk_size:
                processed_chunks.append(current_chunk)
                current_chunk = ""
    
    # Add the last chunk if it exists
    if current_chunk:
        processed_chunks.append(current_chunk)
    
    return processed_chunks
```

### Vector Embedding

The implementation uses the same embedding model as the memory system for consistency, but with explicit source context to distinguish between agent memory and crawl4ai content:

```python
from radbot.memory.embedding import get_embedding_model, embed_text

# Get embedding model
self.embedding_model = get_embedding_model()

# Generate document embedding
vector = embed_text(text, self.embedding_model, is_query=False, source="crawl4ai")

# Generate query embedding
query_vector = embed_text(query, self.embedding_model, is_query=True, source="crawl4ai")
```

This distinction is important as it ensures proper separation between the agent's internal memory and the web content knowledge base. It also helps with debugging by making it clear which subsystem is generating embeddings.

### Search Process

The search process follows these steps:

1. User query is converted to an embedding vector
2. Vector similarity search is performed in Qdrant
3. Results are sorted by relevance
4. Content is formatted as markdown for LLM consumption

### Qdrant Collection Setup

The Qdrant collection is created with:
- COSINE distance metric for similarity calculation
- Payload indexes for URL and timestamp fields
- Optional disk storage for payloads to save memory

## Configuration

The implementation uses these environment variables:

- `QDRANT_URL` or `QDRANT_HOST`/`QDRANT_PORT` for Qdrant connection
- `QDRANT_API_KEY` for Qdrant Cloud authentication (if applicable)
- `CRAWL4AI_COLLECTION` to specify the collection name (defaults to "crawl4ai_docs")
- `radbot_EMBED_MODEL` to specify the embedding model type

## Usage Example

```python
# Read a URL and automatically store in vector DB
result = read_url_as_markdown_directly("https://example.com/docs")

# Ingest a URL for future search (no content returned)
ingest_result = ingest_url_to_knowledge_base("https://example.com/api-docs")

# Search across all ingested content
search_result = web_query("How to authenticate API requests?")
```

## Error Handling

The implementation includes comprehensive error handling:

- Connection errors to Qdrant are caught and logged
- Embedding generation errors provide fallback responses
- Content processing errors are reported without crashing the system

## Future Improvements

Possible enhancements include:

1. Implementing metadata filtering for search queries
2. Adding support for bulk ingestion of multiple URLs
3. Creating a management interface for viewing and deleting ingested content
4. Adding support for re-indexing content when embedding models change