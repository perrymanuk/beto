# Crawl4AI Chunking Fix for Claude MCP Integration

## Issue

When using Crawl4AI with Claude through the Model Context Protocol (MCP), we were encountering "Input is too long for the model" errors. These errors occurred because:

1. The default chunking settings were producing chunks that were too large for Claude's context window
2. There was inconsistency in chunking parameters between our ingestion script, vector store, and MCP client
3. The chunking strategy wasn't optimized for semantic content like Terraform documentation

## Investigation

We identified three components that needed alignment:

1. `ingest-terraform-docs.py` in the crawl repo - used for batch ingestion
2. `terraform_vector_store.py` in the crawl repo - handles vector storage and chunking
3. `crawl4ai_ingest_url.py` in the radbot repo - handles MCP integration

Our testing revealed:
- Default chunk size (800 characters) was creating chunks exceeding Claude's limits
- Some chunking implementations weren't properly handling headings and sections
- The MCP integration was attempting to process chunks without extra chunking safeguards

## Solution

We've implemented a comprehensive fix across all components:

1. **Reduced chunk size**: Changed from 800 to 500 characters per chunk
2. **Added chunk overlap**: Implemented 50 character overlap between chunks  
3. **Heading-based chunking**: Enhanced chunking to respect document structure
4. **Consistent settings**: Standardized parameters across all components
5. **Size validation**: Added safeguards to prevent exceeding context limits

### Configuration Parameters

The key configuration parameters now use these values:

```python
# Chunking Configuration - OPTIMIZED FOR CLAUDE
VECTOR_STORE_CHUNK_SIZE = 500  # Reduced chunk size for better Claude compatibility
CHUNK_OVERLAP = 50  # Overlap between chunks for context continuity
MAX_CONTENT_SIZE = 16000  # Maximum content size before extra chunking (in characters)
CHUNK_BY_HEADING = True  # Enable chunking by headings for more semantic chunks
```

### Implementation Details

1. **Enhanced chunking algorithm**: 
   - First splits by headings (# Heading) to preserve document structure
   - For each section, checks if adding content would exceed max chunk size
   - If a section itself is too large, splits by paragraphs with proper segmentation
   - Applies overlap between chunks for better context continuity

2. **Pre-chunked document detection**:
   - Added logic to detect if a document is already pre-chunked
   - Prevents re-chunking of content that's already been properly segmented

3. **Metadata enrichment**:
   - Added chunk index and total chunks to metadata
   - Preserves document structure information in the vector store
   - Enhances search results with pagination capability

## Testing

We created a testing utility (`test_claude_chunking.py`) to verify the effectiveness of different chunking configurations. The utility:

1. Tests multiple configurations with different chunk sizes and overlaps
2. Measures key metrics like average chunk size, maximum chunk size, and chunk count
3. Generates detailed reports with recommendations
4. Validates the chunking works correctly with Claude's context limits

Our testing showed that the new configuration (500 character chunks with 50 character overlap) provides the best balance between:
- Context preservation - maintaining document coherence
- Safe chunk sizes - staying well below Claude's limits
- Efficiency - minimizing unnecessary overhead

## Usage

No changes are required to existing code using these components. The chunking improvements are transparent to users, as they're implemented within the underlying libraries. The system now handles large documents properly and avoids context limit errors with Claude.

## Future Improvements

Potential future enhancements:

1. Add adaptive chunking based on content complexity
2. Implement recursive chunking for extremely large documents
3. Explore additional semantic chunking strategies
4. Add more robust error handling and reporting
5. Implement auto-tuning of chunking parameters based on feedback

## Dependencies

This implementation works with:
- Claude models via the MCP
- Crawl4AI for content extraction
- Qdrant for vector storage
- `sentence-transformers` for embedding generation
