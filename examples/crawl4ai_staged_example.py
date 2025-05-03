#!/usr/bin/env python3
"""
Example script demonstrating the staged crawling and depth limiting features
of the Crawl4AI integration.

This script shows:
1. Basic depth-limited crawling (default depth=1)
2. Stage 1 of staged crawling (link extraction)
3. Stage 2 of staged crawling (targeted content crawling)

Usage:
    python crawl4ai_staged_example.py [--url URL] [--staged] [--depth DEPTH]
"""

import argparse
import json
import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from radbot.tools.crawl4ai.crawl4ai_ingest_url import crawl4ai_ingest_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """Main function to run the example."""
    parser = argparse.ArgumentParser(
        description="Demonstrate Crawl4AI staged crawling and depth limiting"
    )
    parser.add_argument(
        "--url", 
        default="https://terragrunt.gruntwork.io/docs",
        help="URL to crawl (default: Terragrunt docs)"
    )
    parser.add_argument(
        "--staged", 
        action="store_true",
        help="Use staged crawling (link extraction first)"
    )
    parser.add_argument(
        "--depth", 
        type=int, 
        default=1,
        help="Crawl depth (default: 1)"
    )
    args = parser.parse_args()

    # Display banner
    print("\n" + "=" * 80)
    print(f"Crawl4AI Example: {'Staged Crawling' if args.staged else 'Depth-Limited Crawling'}")
    print("=" * 80)
    
    if args.staged:
        # Stage 1: Extract links
        print(f"\n🔍 Stage 1: Extracting links from {args.url}...")
        stage1_result = crawl4ai_ingest_url(
            url=args.url,
            staged_crawl=True
        )
        
        # Print the result in a readable format
        print(f"\n✅ Found {len(stage1_result.get('links', []))} links:")
        print(f"   - {stage1_result.get('internal_link_count', 0)} internal links")
        print(f"   - {stage1_result.get('external_link_count', 0)} external links")
        
        # Display some example links
        print("\nExample links found:")
        for i, link in enumerate(stage1_result.get('links', [])[:5]):
            print(f"{i+1}. {link.get('title', 'No title')}: {link.get('url', 'No URL')}")
        
        if len(stage1_result.get('links', [])) > 5:
            print(f"   ... and {len(stage1_result.get('links', [])) - 5} more")
            
        # Stage 2: Option to crawl specific links
        print("\n" + "=" * 80)
        print("Stage 2: Targeted crawling")
        print("=" * 80)
        
        # Select the first 2 internal links for demonstration
        internal_links = [
            link.get('url') for link in stage1_result.get('links', [])
            if 'terragrunt.gruntwork.io' in link.get('url', '')
        ][:2]
        
        if internal_links:
            print(f"\n🔍 Crawling {len(internal_links)} selected links...")
            for link in internal_links:
                print(f"   - {link}")
            
            stage2_result = crawl4ai_ingest_url(
                url=args.url,
                target_links=internal_links
            )
            
            # Print the result
            print(f"\n✅ Crawling result: {stage2_result.get('message', 'No message')}")
            print(f"Stored URLs: {stage2_result.get('stored_urls', [])}")
            print(f"Total chunks: {stage2_result.get('total_chunks', 0)}")
        else:
            print("\n⚠️ No internal links found to crawl in Stage 2")
    else:
        # Regular depth-limited crawling
        print(f"\n🔍 Crawling {args.url} with depth={args.depth}...")
        result = crawl4ai_ingest_url(
            url=args.url,
            crawl_depth=args.depth
        )
        
        # Print the result
        print(f"\n✅ Crawling result: {result.get('message', 'No message')}")
        
        # If it was a deep crawl, show additional information
        if args.depth > 0 and 'pages_crawled' in result:
            print(f"Pages crawled: {result.get('pages_crawled', 0)}")
            print(f"Pages stored: {result.get('pages_stored', 0)}")
            print(f"Total chunks: {result.get('total_chunks', 0)}")
    
    print("\n" + "=" * 80)
    print("Example complete!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
