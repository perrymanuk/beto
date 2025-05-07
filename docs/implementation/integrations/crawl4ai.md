# Crawl4AI Integration

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


## Overview

This document covers the complete Crawl4AI integration for the RadBot framework, providing a comprehensive web crawling, content extraction, and knowledge retrieval capability using vector search.

Crawl4AI is a specialized web crawler and knowledge retrieval system designed for LLM-friendly content extraction. The integration enables RadBot to:

1. Ingest web content from specified URLs with configurable crawl depth
2. Extract and process content for optimal LLM consumption
3. Store content in a vector database for semantic search
4. Query ingested content using natural language
5. Utilize retrieved information to enhance agent responses

## Architecture

The integration follows RadBot's Model Context Protocol (MCP) pattern, implementing these key components:

### Core Components

1. **MCP Client (`mcp_crawl4ai_client.py`)**
   - Exposes Crawl4AI capabilities through MCP-compatible tools
   - Handles API communication with the Crawl4AI service
   - Provides factory functions for creating agents with Crawl4AI capabilities
   - Implements tool handlers for the MCP protocol

2. **Vector Store (`crawl4ai_vector_store.py`)**
   - Manages Qdrant collections for storing crawled content
   - Handles document embedding and retrieval
   - Implements semantic search functionality
   - Provides chunking strategies for optimal content storage

3. **Crawling Strategies**
   - Multiple approaches for different use cases:
     - Basic URL ingestion (single page)
     - Depth crawling (follow links to specified depth)
     - Staged crawling (extract links first, then selectively crawl)
     - Two-step crawling (combine API and link extraction)

4. **Content Processing**
   - Document chunking strategies for optimal LLM consumption
   - Heading-based content splitting to preserve document structure
   - Metadata enrichment for improved search context

## Configuration

The integration uses the following environment variables:

```
# Crawl4AI API Configuration
CRAWL4AI_API_URL=https://crawl4ai.demonsafe.com
CRAWL4AI_API_TOKEN=your_token_here

# Vector Store Configuration
QDRANT_URL=http://localhost:6333
# Or use individual components:
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your_api_key_here

# Collection Configuration
CRAWL4AI_COLLECTION=crawl4ai_docs

# Embedding Configuration
EMBED_MODEL=text-embedding-3-small
```

## Crawling Approaches

The integration provides several approaches to crawling, each optimized for different use cases.

### 1. Basic URL Ingestion

The simplest approach that fetches and processes a single URL.

```python
result = crawl4ai_ingest_url("https://example.com/docs")
```

This approach:
- Extracts content from a single URL
- Processes and chunks the content
- Stores in the vector database
- Returns a success message with metadata

### 2. Depth Crawling

Recursively crawls a website to a specified depth.

```python
result = crawl4ai_ingest_url(
    url="https://example.com/docs",
    crawl_depth=2,  # Follow links two levels deep
    include_external=False,  # Only stay on the same domain
    max_pages=20  # Limit to 20 pages per depth level
)
```

This approach:
- Crawls the initial URL (depth 0)
- Follows links on that page to specified depth
- Uses breadth-first search to ensure complete level coverage
- Stores all discovered content in the vector database

#### Implementation Details

The depth crawling functionality uses two main methods:

1. **BFSDeepCrawlStrategy**: The built-in crawl4ai breadth-first search strategy
2. **DeepCrawl Helper Class**: Our custom implementation for advanced control

```python
deep_crawl_strategy = BFSDeepCrawlStrategy(
    max_depth=self.max_depth,
    include_external=self.include_external,
    max_pages=self.max_urls_per_depth
)

run_config = CrawlerRunConfig(
    deep_crawl_strategy=deep_crawl_strategy,
    word_count_threshold=10,  # Skip very small content blocks
    verbose=False
)
```

### 3. Staged Crawling

A two-stage approach that gives users more control over what gets crawled.

```python
# Stage 1: Extract links only
links = crawl4ai_ingest_url(
    url="https://example.com/docs",
    staged_crawl=True
)

# Stage 2: Crawl selected links
result = crawl4ai_ingest_url(
    url="https://example.com/docs",
    target_links=[
        "https://example.com/docs/page1",
        "https://example.com/docs/page2"
    ]
)
```

This approach:
- First extracts all links from the target page
- Returns the links to the user for selection
- Then crawls only the selected links
- Reduces agent blocking and resource usage
- Gives users more control over content selection

### 4. Two-Step Crawling

An optimized approach that avoids heavy browser dependencies while still crawling linked content.

```python
result = crawl4ai_two_step(
    url="https://example.com/docs",
    max_links=10,  # Optional: Limit number of links to crawl
    include_external=False  # Optional: Include external links
)
```

This approach:
- Uses the API to fetch the initial URL (no browser needed)
- Extracts links from the markdown content using regex
- Crawls those links in batch mode
- Returns both the initial content and stats about linked pages
- Avoids the Playwright dependency in crawl4ai

## Content Processing and Storage

### Document Chunking

The integration implements advanced document chunking strategies for optimal LLM consumption:

1. **Hierarchical Chunking**:
   - First splits by headings to preserve document structure
   - Then by paragraphs if sections are too large
   - Then by sentences if paragraphs are too large
   - Finally by character limits as a last resort

2. **Claude-Optimized Parameters**:
   ```python
   VECTOR_STORE_CHUNK_SIZE = 500  # Optimized for Claude
   CHUNK_OVERLAP = 50  # Overlap between chunks
   MAX_CONTENT_SIZE = 16000  # Maximum content size before extra chunking
   CHUNK_BY_HEADING = True  # Enable heading-based chunking
   ```

3. **Metadata Enrichment**:
   - Adds chunk index and total chunks
   - Preserves document structure information
   - Enhances search with pagination capability

### Vector Storage

Content is stored in a Qdrant vector database for efficient semantic search:

1. **Collection Management**:
   - Creates a dedicated collection for crawled content
   - Configures proper schema and index settings
   - Handles duplicate detection and updates

2. **Embedding Generation**:
   - Uses the same embedding model as the memory system
   - Consistent vector representation across features
   - Supports configurable embedding models

3. **Search Implementation**:
   - Vector similarity search for natural language queries
   - Relevance scoring and sorting
   - Source tracking for attribution
   - Result formatting for LLM consumption

## User-Facing Functions

### Basic Content Access

```python
result = crawl4ai_ingest_and_read("https://example.com/docs")
```
Fetches, displays, and stores content from a URL.

### Web Content Ingestion

```python
result = crawl4ai_ingest_url("https://example.com/api-docs", crawl_depth=1)
```
Ingests content from a URL and its linked pages and stores it for later search.

### Knowledge Base Querying

```python
results = crawl4ai_query("How to authenticate API requests?")
```
Performs semantic search across all previously ingested content.

### Two-Step Crawling

```python
result = crawl4ai_two_step("https://example.com/docs", max_links=10)
```
Fetches initial content and crawls linked pages in an optimized way.

## Technical Implementation Details

### Vector Store Implementation

The `Crawl4AIVectorStore` class manages document storage and retrieval:

```python
class Crawl4AIVectorStore:
    """
    Manages storage and retrieval of crawled content using Qdrant.
    """
    def __init__(self, collection_name="crawl4ai_docs"):
        # Initialize Qdrant connection
        self.collection_name = collection_name
        self.qdrant_client = self._get_qdrant_client()
        self._ensure_collection_exists()
        
    def add_document(self, content, metadata=None):
        """Add a document to the vector store with chunking."""
        chunks = self._chunk_content(content)
        for chunk in chunks:
            self._add_chunk(chunk, metadata)
    
    def search(self, query, limit=5):
        """Perform semantic search across stored content."""
        # Generate query embedding
        query_vector = generate_embedding(query)
        
        # Search in Qdrant
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit
        )
        
        return self._format_results(results)
```

### Chunking Implementation

The chunking strategy balances coherence and size constraints:

```python
def _chunk_content(self, content, chunk_size=500, overlap=50):
    """
    Split content into chunks with semantic boundaries.
    Prioritizes splitting at headings, then paragraphs, then sentences.
    """
    chunks = []
    
    # Try to split by headings first
    heading_sections = re.split(r'(#+\s+.+\n)', content)
    
    current_chunk = ""
    current_heading = ""
    
    for section in heading_sections:
        if re.match(r'#+\s+.+\n', section):
            # This is a heading
            if current_chunk:
                chunks.append((current_heading + current_chunk).strip())
            current_heading = section
            current_chunk = ""
        else:
            # This is content
            if len(current_chunk + section) <= chunk_size:
                current_chunk += section
            else:
                # Need to split this section further
                paragraph_chunks = self._split_by_paragraphs(
                    current_chunk + section, 
                    chunk_size, 
                    overlap
                )
                
                # Add the first chunk with the current heading
                if paragraph_chunks:
                    chunks.append((current_heading + paragraph_chunks[0]).strip())
                    
                    # Add remaining chunks with heading prefix
                    for chunk in paragraph_chunks[1:]:
                        chunks.append((current_heading + "... " + chunk).strip())
                
                current_chunk = ""
    
    # Add the final chunk
    if current_chunk:
        chunks.append((current_heading + current_chunk).strip())
    
    return chunks
```

### MCP Integration

The MCP tools are created using ADK's FunctionTool approach:

```python
def create_crawl4ai_toolset():
    """
    Create a set of MCP-compatible tools for Crawl4AI integration.
    """
    tools = [
        FunctionTool(
            func=crawl4ai_ingest_url,
            name="crawl4ai_ingest_url",
            description="Ingest content from a URL into the knowledge base"
        ),
        FunctionTool(
            func=crawl4ai_ingest_and_read,
            name="crawl4ai_ingest_and_read",
            description="Fetch and display content from a URL, and store it in the knowledge base"
        ),
        FunctionTool(
            func=crawl4ai_query,
            name="crawl4ai_query",
            description="Search the knowledge base for information related to a query"
        ),
        FunctionTool(
            func=crawl4ai_two_step,
            name="crawl4ai_two_step",
            description="Fetch a URL and crawl its links in a two-step process"
        )
    ]
    
    return tools
```

## Issues and Solutions

### 1. Vector Search Implementation

**Issue**: The initial implementation faced a `400 Bad Request` error when querying the Crawl4AI API for knowledge base searches.

**Solution**: Implemented custom vector search using Qdrant to store and search content extracted by Crawl4AI.

### 2. Document Chunking for Claude

**Issue**: Default chunking settings produced chunks that were too large for Claude's context window.

**Solution**: 
- Reduced chunk size from 800 to 500 characters
- Added 50 character overlap between chunks
- Implemented heading-based chunking to respect document structure
- Added size validation safeguards

### 3. Depth Crawling Reliability

**Issue**: The original depth crawling implementation wasn't reliably following links at each level.

**Solution**: Reimplemented depth crawling using BFSDeepCrawlStrategy with proper breadth-first search approach.

### 4. Browser Dependencies

**Issue**: Deep crawling required Playwright browser binaries, which increased deployment complexity.

**Solution**: Implemented two-step crawling to combine API-based fetching with link extraction using regex.

### 5. Agent Blocking During Crawling

**Issue**: Deep crawling could block the agent for extended periods.

**Solution**: Implemented staged crawling to split the process into link extraction and selective crawling steps.

## Future Improvements

1. **Incremental Updates**: Add capability to update existing documents instead of replacing them
2. **Multi-URL Ingestion**: Improve batch processing of multiple URLs
3. **Advanced Filtering**: Allow searching within specific domains or date ranges
4. **Relevance Tuning**: Add adjustable relevance thresholds and ranking parameters
5. **Web UI**: Create a simple interface for browsing and managing ingested content
6. **Async Processing**: Implement fully asynchronous crawling with status tracking
7. **Content Summarization**: Add automatic summarization of crawled content
8. **Selective Crawling**: Implement semantic filtering to prioritize relevant pages

## Examples

### Basic Usage Example

```python
# Ingest documentation and query it
agent.process_message("user1", "Please ingest the documentation from https://requests.readthedocs.io/en/latest/")
# Agent uses crawl4ai_ingest_url and confirms success

agent.process_message("user1", "How do I handle timeouts with the requests library?")
# Agent uses crawl4ai_query to retrieve relevant information
# and provides a well-informed response based on the documentation
```

### Advanced Example with Two-Step Crawling

```python
# Two-step crawling with link selection
agent.process_message("user1", "Fetch the FastAPI documentation homepage and analyze what links it contains")
# Agent uses crawl4ai_two_step to fetch the homepage and extract links

agent.process_message("user1", "Now crawl the 'Advanced User Guide' section")
# Agent identifies the specific link and crawls it using crawl4ai_ingest_url

agent.process_message("user1", "How do I implement custom middleware in FastAPI?")
# Agent searches the crawled content using crawl4ai_query
```

## Dependencies

- `crawl4ai` (version 0.6.2 or higher)
- `qdrant-client` (version 1.1.1 or compatible)
- `sentence-transformers` for embedding generation
- `requests` for API communication
- ADK 0.4.0 for tool integration