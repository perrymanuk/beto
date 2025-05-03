#!/usr/bin/env python3
"""
Test script for the manual deep crawling implementation for crawl4ai.

This script tests:
1. Manual deep crawling (depth=1)
2. Link extraction and following
3. Proper result handling

Run with:
    python examples/crawl4ai_manual_deep_crawl_test.py [--url URL]
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url, ManualDeepCrawl
from radbot.tools.crawl4ai.utils import run_async_safely

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(
        description="Test the manual deep crawling implementation for crawl4ai"
    )
    parser.add_argument(
        "--url", 
        default="https://terragrunt.gruntwork.io/docs",
        help="URL to crawl (default: Terragrunt docs)"
    )
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Include external links (default: False)"
    )
    parser.add_argument(
        "--max-links",
        type=int,
        default=10,
        help="Maximum number of links to crawl (default: 10)"
    )
    
    args = parser.parse_args()

    # Display banner
    print("\n" + "=" * 80)
    print(f"Crawl4AI Manual Deep Crawling Test")
    print("=" * 80)
    
    # Initialize deep crawler directly
    print(f"\n🔍 Testing manual deep crawler with URL: {args.url}")
    crawler = ManualDeepCrawl(
        base_url=args.url,
        max_depth=1,
        max_urls_per_depth=args.max_links,
        include_external=args.include_external
    )
    
    # Execute crawl
    print("\n⏳ Executing manual deep crawl...")
    results = run_async_safely(crawler.crawl())
    
    # Display results
    print("\n✅ Crawl completed!")
    print(f"Total pages processed: {len(results)}")
    
    # Count success vs failure
    success_count = sum(1 for r in results if r.get("success"))
    failure_count = len(results) - success_count
    
    print(f"Pages successfully crawled: {success_count}")
    print(f"Pages failed to crawl: {failure_count}")
    
    # Group by depth
    depth_counts = {}
    for result in results:
        depth = result.get("depth", "unknown")
        if depth not in depth_counts:
            depth_counts[depth] = 0
        depth_counts[depth] += 1
    
    print("\nPages by depth level:")
    for depth, count in sorted(depth_counts.items()):
        print(f"  Depth {depth}: {count} pages")
    
    # Display some example results
    print("\nExample pages crawled:")
    for i, result in enumerate(results[:5]):
        if result.get("success"):
            content_preview = result.get("content", "")[:50].replace("\n", " ") + "..." if result.get("content") else "No content"
            print(f"{i+1}. {result.get('url')} - {content_preview}")
        else:
            print(f"{i+1}. {result.get('url')} - ERROR: {result.get('error', 'Unknown error')}")
    
    if len(results) > 5:
        print(f"... and {len(results) - 5} more")
    
    # Test with the main API function
    print("\n" + "=" * 80)
    print("Testing with crawl4ai_ingest_url function")
    print("=" * 80)
    
    print(f"\n🔍 Crawling {args.url} with crawl_depth=1...")
    api_result = crawl4ai_ingest_url(
        url=args.url,
        crawl_depth=1,
        include_external=args.include_external,
        max_pages=args.max_links
    )
    
    # Display result
    print(f"\n✅ Crawling result: {api_result.get('message', 'No message')}")
    
    if api_result.get("success"):
        # If it was a deep crawl, show additional information
        if "pages_crawled" in api_result:
            print(f"Pages crawled: {api_result.get('pages_crawled', 0)}")
            print(f"Pages stored: {api_result.get('pages_stored', 0)}")
            print(f"Total chunks: {api_result.get('total_chunks', 0)}")
    else:
        print(f"❌ Crawling failed: {api_result.get('error', 'Unknown error')}")
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
