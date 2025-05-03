#!/usr/bin/env python3
"""
Test script for the two-step crawling implementation for crawl4ai.

This script demonstrates:
1. Initial URL fetching and display
2. Link extraction from content
3. Batch crawling of extracted links

Run with:
    python examples/crawl4ai_two_step_test.py [--url URL] [--max-links MAX_LINKS]
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.tools.crawl4ai.crawl4ai_two_step_crawl import crawl4ai_two_step

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the test."""
    parser = argparse.ArgumentParser(
        description="Test the two-step crawling implementation for crawl4ai"
    )
    parser.add_argument(
        "--url", 
        default="https://terragrunt.gruntwork.io/docs",
        help="URL to crawl (default: Terragrunt docs)"
    )
    parser.add_argument(
        "--max-links",
        type=int,
        default=5,
        help="Maximum number of links to crawl (default: 5)"
    )
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Include external links (default: False)"
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=800,
        help="Maximum chunk size for content (default: 800)"
    )
    
    args = parser.parse_args()

    # Display banner
    print("\n" + "=" * 80)
    print(f"Crawl4AI Two-Step Crawling Test")
    print("=" * 80)
    
    # Execute two-step crawl
    print(f"\n🔍 Starting two-step crawl for {args.url}")
    print(f"Max links: {args.max_links}")
    print(f"Include external: {args.include_external}")
    print(f"Chunk size: {args.chunk_size}")
    
    # Call the function
    result = crawl4ai_two_step(
        url=args.url,
        max_links=args.max_links,
        include_external=args.include_external,
        chunk_size=args.chunk_size
    )
    
    # Display results
    print("\n" + "=" * 80)
    print("Two-Step Crawl Results")
    print("=" * 80)
    
    print(f"\nStatus: {'✅ Success' if result.get('success') else '❌ Failed'}")
    print(f"Message: {result.get('message', 'No message')}")
    
    # Display statistics
    print("\n📊 Statistics:")
    print(f"Links found: {result.get('links_found', 0)}")
    print(f"Links crawled successfully: {result.get('links_crawled', 0)}")
    print(f"Links failed: {result.get('links_failed', 0)}")
    print(f"Total chunks stored: {result.get('total_chunks', 0)}")
    
    # Display initial content preview
    initial_content = result.get('initial_content', '')
    if initial_content:
        content_preview = initial_content[:500] + "..." if len(initial_content) > 500 else initial_content
        print("\n📄 Initial content preview:")
        print("-" * 40)
        print(content_preview)
        print("-" * 40)
    
    # List crawled links
    crawled_links = result.get('crawled_links', [])
    if crawled_links:
        print(f"\n🔗 Crawled links ({len(crawled_links)}):")
        for i, link in enumerate(crawled_links):
            print(f"{i+1}. {link}")
    
    print("\n" + "=" * 80)
    print("Test completed!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
