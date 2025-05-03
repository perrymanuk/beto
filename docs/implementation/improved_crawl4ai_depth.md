# Improved Crawl4AI Depth Crawling

## Problem

The original implementation of Crawl4AI's recursive depth crawling functionality was not working as expected. With `depth=1`, it would only crawl the initial page once, and with `depth=2`, it would crawl the same page twice. The expected behavior was:

- `depth=1`: Crawl the initial page AND all links discovered on that page
- `depth=2`: Crawl the initial page, all links on the initial page, and all links on those linked pages
- And so on for deeper levels

## Solution

We've reimplemented the depth crawling functionality using crawl4ai version 0.6.2's built-in `BFSDeepCrawlStrategy` class for proper depth handling, combined with our own `DeepCrawl` helper class for additional control over the crawling process.

## Implementation Details

### 1. BFSDeepCrawlStrategy Integration

We're using the built-in breadth-first search crawling strategy that comes with crawl4ai:

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

This ensures proper crawling behavior where:
- All URLs at one depth level are processed before moving to the next level
- External domains can be optionally included or excluded
- The maximum number of pages per level can be controlled

### 2. DeepCrawl Helper Class

We implemented a `DeepCrawl` helper class that:

- Handles the setup and execution of the AsyncWebCrawler with proper configuration
- Processes the results into a consistent format for our vector storage
- Tracks visited URLs to prevent infinite loops
- Provides detailed metadata about the crawl results

```python
class DeepCrawl:
    """
    A helper class for deep crawling with configurable depth.
    Uses AsyncWebCrawler from crawl4ai for efficient link discovery and crawling.
    """
    # ... implementation ...
```

### 3. API Compatibility

Since we had to adapt to the available API in crawl4ai 0.6.2 (instead of the expected version 1.0.0), we made several adjustments:

- Changed from `AsyncCrawler` to `AsyncWebCrawler` which is the available class in 0.6.2
- Adjusted the configuration to use `BrowserConfig` and `CrawlerRunConfig` classes
- Modified the result handling to extract content from the result object's properties
- Added proper depth handling using the built-in deep crawling strategies

### 4. Breadth-First Approach

The implementation maintains the breadth-first approach, which ensures:

1. The initial URL is processed first (depth 0)
2. All links discovered at depth 0 are processed next (depth 1)
3. All links discovered at depth 1 are processed next (depth 2)
4. And so on, until the maximum depth is reached

This approach guarantees that all URLs at each level are fully processed before moving deeper, providing a more comprehensive and systematic crawl.

## Configuration Options

The implementation supports various configuration options:

```python
crawl4ai_ingest_url(
    url="https://example.com",
    crawl_depth=2,          # How many levels deep to crawl
    include_external=False, # Whether to follow external links
    max_pages=20,           # Maximum pages per depth level
    content_selectors=None  # Optional CSS selectors for content targeting
)
```

## Vector Storage Integration

After crawling, all discovered content is:

1. Processed and chunked if necessary
2. Stored in the Qdrant vector database with metadata
3. Available for semantic search via the `crawl4ai_query` function

This ensures that the crawled content is properly indexed for efficient retrieval.

## Performance Considerations

- The implementation uses semaphores to limit concurrent requests
- Large content is automatically chunked to stay within vector database limits
- Domain filtering prevents the crawler from wandering to unrelated websites
- The maximum number of pages can be limited to prevent excessive crawling

## Usage Examples

```python
# Just crawl a single URL
crawl4ai_ingest_url("https://example.com")

# Crawl the URL and all directly linked pages
crawl4ai_ingest_url("https://example.com", crawl_depth=1)

# Crawl two levels deep, including external domains
crawl4ai_ingest_url("https://example.com", crawl_depth=2, include_external=True)

# Process multiple URLs in one call
crawl4ai_ingest_url("https://example.com,https://example.org", crawl_depth=1)

# Limit to maximum 10 pages per depth level
crawl4ai_ingest_url("https://example.com", crawl_depth=2, max_pages=10)
```

## Future Improvements

Areas for potential enhancements:

1. **Improved filtering**: More sophisticated URL filtering based on content relevance
2. **Progressive loading**: Stream results as they become available rather than waiting for all processing to complete
3. **Selective crawling**: Prioritize more relevant pages using semantic similarity
4. **Robots.txt support**: Add support for respecting robots exclusion directives
5. **Resumed crawling**: Allow interrupted crawls to be resumed from the last point