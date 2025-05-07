# Crawl4AI Two-Step Crawling Implementation

## Overview

This document details the two-step crawling implementation for crawl4ai. This approach combines the simplicity of the API-based URL fetching with comprehensive link extraction and multi-URL crawling.

## Handling Large Content

The implementation includes optimized content chunking to handle large documents:

1. **Embedding Size Limit**: Google's embedding API has a limit of 36,000 bytes per request
2. **Chunking Strategy**: Content is broken down into smaller chunks of ~800 characters
3. **Hierarchical Chunking**: 
   - First attempts to split by headings
   - Then by paragraphs
   - Then by sentences if needed
   - Finally by arbitrary character limits as a last resort

This ensures we stay well under the embedding size limit while maintaining semantic coherence in chunks.

## Problem

The Crawl4AI integration faced several challenges:

1. **Playwright Dependency**: The deep crawling functionality in crawl4ai 0.6.2 requires Playwright browser binaries
2. **Unreliable Depth Handling**: The built-in deep crawling was not reliably following links at each level
3. **Agent Blocking**: Long-running deep crawling operations would block the agent

## Solution

### Two-Step Crawling Approach

The two-step crawling approach implements a more reliable solution that:

1. **First Step**: Uses `crawl4ai_ingest_and_read` to fetch and display the initial URL content (no Playwright needed)
2. **Link Extraction**: Extracts all links from the markdown content using regex
3. **Second Step**: Passes those links to `crawl4ai_ingest_url` as a multi-URL request

### Implementation Details

1. Created a new `crawl4ai_two_step` function that:
   - Fetches the initial URL using the stable API endpoint
   - Extracts links from the markdown content using regex
   - Filters links based on domain and validity requirements
   - Crawls those links in batch mode

2. Added detailed logging to track:
   - Number of links extracted
   - Number of links successfully crawled
   - Total chunks stored in the vector database

3. Added MCP integration by:
   - Registering the function with proper schema
   - Including it in the tools list

## Usage

```python
result = crawl4ai_two_step(
    url="https://example.com/docs",
    max_links=10,  # Optional: Limit number of links to crawl
    include_external=False  # Optional: Include external links
)
```

This will:
1. Fetch and display the content of the main URL
2. Extract all links from that content
3. Crawl and store those links (up to max_links)
4. Return a comprehensive result with both the initial content and statistics about the linked pages

## Benefits

- **API Compatibility**: Uses the stable API endpoint for the initial fetch, avoiding Playwright dependency
- **Immediate Content**: Shows the initial page content right away
- **Reliable Link Extraction**: Direct control over the link extraction process
- **Efficient Batch Processing**: Processes all links in a single request
- **Transparent Progress**: Clear information about what's being crawled
- **Minimal Agent Blocking**: Better user experience with faster initial response

## Technical Approach

1. **Markdown Link Extraction**: Uses regex to extract both `[text](url)` style links and raw URLs from the content
2. **URL Normalization**: Properly handles relative URLs by joining them with the base URL
3. **Domain Filtering**: Option to include or exclude external links
4. **Batched Processing**: Efficiently processes multiple URLs in a single request

## Future Improvements

- Add option to extract links from HTML content instead of markdown for more robust link discovery
- Implement progressive crawling to process links in smaller batches
- Add support for more advanced filtering of links
- Create visualization of the link structure
