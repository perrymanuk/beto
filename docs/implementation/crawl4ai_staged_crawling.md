# Staged Crawling Implementation

## Overview

This document details the staged crawling implementation for crawl4ai URLs. Staged crawling is a more efficient approach to web crawling that doesn't block the agent for extended periods and gives users more control over what content gets crawled.

## Problem

The original crawl4ai implementation had two main issues:

1. **Agent Blocking**: Deep crawling could take a long time, blocking the agent for the entire duration
2. **Resource Intensive**: Crawling large sites with high depth values could consume excessive resources

## Solution

### Staged Crawling Approach

The staged crawling approach splits the crawling process into two distinct stages:

1. **Stage 1: Link Extraction**
   - Only the main page is crawled
   - All links on the page are extracted and returned
   - The agent remains responsive and returns quickly
   - User can see what links are available

2. **Stage 2: Targeted Crawling**
   - User selects specific links to crawl based on Stage 1 results
   - Only the selected links are crawled
   - More efficient use of resources
   - Better user control over what content is stored

### Implementation Details

1. Added a new parameter `staged_crawl` to the `crawl4ai_ingest_url` function
2. Implemented the `_extract_links_from_url` helper function to extract links from a page
3. Implemented the `_perform_staged_crawl` function to execute Stage 1
4. Modified the main function to support both stages
5. Enhanced documentation with usage examples

## Usage

### Stage 1: Extract Links

```python
result = crawl4ai_ingest_url(
    url="https://example.com/docs", 
    staged_crawl=True
)
```

This returns a result containing:
- List of all links found on the page
- Count of internal vs external links
- Suggested next action

### Stage 2: Crawl Specific Links

```python
result = crawl4ai_ingest_url(
    url="https://example.com/docs",
    target_links=[
        "https://example.com/docs/page1",
        "https://example.com/docs/page2"
    ]
)
```

This crawls only the specified links and stores their content in the vector database.

## Benefits

- **Reduced Agent Blocking**: The agent remains responsive during the crawling process
- **User Control**: Users can select which sections of a site to crawl
- **Resource Efficiency**: Only crawls the content that's actually needed
- **Better Scalability**: Can handle large sites more effectively

## Future Improvements

- Integration with a task queue for completely async operations
- Progressive loading of results as they become available
- More sophisticated link categorization and filtering
- Option to save link extraction results for later use
