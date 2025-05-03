#!/usr/bin/env python3
"""
Crawl4AI Link Scanner Module

This module provides functions for scanning a website to discover links
without fully crawling all pages. It's designed to work with documentation
sites and other structured content.

Features:
- Initial link discovery without deep crawling
- Structured link organization
- Fast preview of site structure
"""

import logging
import requests
import asyncio
from typing import Dict, Any, Optional, List, Set
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

from .utils import run_async_safely, get_crawl4ai_config
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

# Configure logging
logger = logging.getLogger(__name__)

class LinkScanner:
    """
    A helper class for scanning a website to discover links.
    It crawls only the initial page and extracts all links.
    """
    
    def __init__(self, base_url: str, include_external: bool = False):
        """
        Initialize the link scanner.
        
        Args:
            base_url: The starting URL for scanning
            include_external: Whether to include links to external domains
        """
        self.base_url = base_url
        self.include_external = include_external
        self.base_domain = urlparse(base_url).netloc
        self.links = []
        
    def _is_valid_link(self, url: str) -> bool:
        """Check if link should be included based on domain restrictions."""
        if not url or not url.startswith(('http://', 'https://')):
            return False
            
        # Skip fragment identifiers or empty links
        if '#' in url:
            url = url.split('#')[0]
            if not url:
                return False
                
        # Check domain restrictions if not including external links
        if not self.include_external:
            parsed_url = urlparse(url)
            if parsed_url.netloc != self.base_domain:
                return False
                
        return True
        
    def _categorize_link(self, url: str, base_url: str) -> str:
        """Categorize link as section, subsection, etc."""
        if url == base_url:
            return "main"
            
        # Remove protocol and domain from both URLs for comparison
        base_parts = urlparse(base_url).path.strip('/').split('/')
        url_parts = urlparse(url).path.strip('/').split('/')
        
        # If URL has one more path segment than base, it's a section
        if len(url_parts) == len(base_parts) + 1:
            return "section"
        # If URL has two more path segments than base, it's a subsection
        elif len(url_parts) == len(base_parts) + 2:
            return "subsection"
        # If URL has more path segments, it's a deep page
        elif len(url_parts) > len(base_parts) + 2:
            return "deep"
        # If URL has same or fewer path segments, it's a sibling or parent
        else:
            return "other"
    
    async def scan(self) -> Dict[str, Any]:
        """
        Scan the base URL and extract all links.
        
        Returns:
            Dictionary with scanning results
        """
        # Set up browser configuration
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        # Set up crawler configuration
        run_config = CrawlerRunConfig(
            word_count_threshold=10,
            verbose=False
        )
        
        # Create crawler and scan the page
        try:
            async with AsyncWebCrawler(config=browser_config) as crawler:
                result = await crawler.arun(
                    url=self.base_url,
                    config=run_config
                )
                
                if result and hasattr(result, "success") and result.success:
                    # Extract links from HTML
                    soup = BeautifulSoup(result.html if hasattr(result, "html") else "", "html.parser")
                    
                    # Extract page title
                    title = soup.title.text.strip() if soup.title else "Unknown Title"
                    
                    # Find all links
                    raw_links = []
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        link_text = a_tag.text.strip()
                        
                        # Skip empty links or javascript
                        if not href or href.startswith("javascript:"):
                            continue
                            
                        # Normalize URL
                        if not href.startswith(("http://", "https://")):
                            href = urljoin(self.base_url, href)
                            
                        # Check if link is valid
                        if self._is_valid_link(href):
                            # Add to links list
                            link_category = self._categorize_link(href, self.base_url)
                            raw_links.append({
                                "url": href,
                                "text": link_text if link_text else href.split("/")[-1],
                                "category": link_category
                            })
                    
                    # Remove duplicates and sort by category then text
                    seen_urls = set()
                    organized_links = {
                        "main": [],
                        "section": [],
                        "subsection": [],
                        "deep": [],
                        "other": []
                    }
                    
                    for link in raw_links:
                        if link["url"] not in seen_urls:
                            seen_urls.add(link["url"])
                            organized_links[link["category"]].append(link)
                    
                    # Sort links by text
                    for category in organized_links:
                        organized_links[category].sort(key=lambda x: x["text"])
                    
                    # Count links by category
                    link_counts = {category: len(links) for category, links in organized_links.items()}
                    total_links = sum(link_counts.values())
                    
                    return {
                        "success": True,
                        "url": self.base_url,
                        "title": title,
                        "total_links": total_links,
                        "link_counts": link_counts,
                        "organized_links": organized_links,
                        "content": result.markdown if hasattr(result, "markdown") else ""
                    }
                else:
                    return {
                        "success": False,
                        "url": self.base_url,
                        "error": "Failed to crawl page",
                        "message": "Could not extract links from page"
                    }
                    
        except Exception as e:
            logger.error(f"Error scanning {self.base_url}: {str(e)}")
            return {
                "success": False,
                "url": self.base_url,
                "error": str(e),
                "message": f"Failed to scan URL: {str(e)}"
            }

async def scan_links(url: str, include_external: bool = False) -> Dict[str, Any]:
    """
    Scan a URL to discover available links without deep crawling.
    
    This is the first stage of a two-stage crawling process:
    1. Scan the initial page to discover and categorize available links
    2. User can then select which links to crawl in depth
    
    Args:
        url: The URL to scan
        include_external: Whether to include links to external domains
        
    Returns:
        Dictionary with scanning results, including organized links
    """
    scanner = LinkScanner(
        base_url=url,
        include_external=include_external
    )
    
    return await scanner.scan()

def crawl4ai_scan_links(url: str, include_external: bool = False) -> Dict[str, Any]:
    """
    Scan a URL to discover available links without deep crawling.
    
    This function provides a preview of a website's structure by extracting
    all links from the main page. It organizes links by category (sections,
    subsections, etc.) to help users decide which parts to crawl in depth.
    
    Usage:
    1. Call this function first to see available links: 
       result = crawl4ai_scan_links(url="https://example.com/docs")
    2. Examine the organized_links in the result to see available sections
    3. Use crawl4ai_ingest_url to crawl specific sections or the entire site
    
    Args:
        url: The URL to scan
        include_external: Whether to include links to external domains
        
    Returns:
        Dictionary containing organized links and metadata
    """
    # Validate URL parameter
    if not url or not isinstance(url, str):
        error_msg = f"Invalid URL parameter: {url!r}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "URL must be a non-empty string"
        }
    
    logger.info(f"🔍 Crawl4AI scanning links from {url}")
    
    # Run the scanner
    try:
        result = run_async_safely(scan_links(
            url=url,
            include_external=include_external
        ))
        
        if result["success"]:
            # Create a summary response
            sections_count = len(result["organized_links"].get("section", []))
            subsections_count = len(result["organized_links"].get("subsection", []))
            
            return {
                "success": True,
                "message": f"✅ Found {result['total_links']} links on {url} ({sections_count} sections, {subsections_count} subsections)",
                "url": url,
                "title": result.get("title", ""),
                "total_links": result.get("total_links", 0),
                "link_counts": result.get("link_counts", {}),
                "organized_links": result.get("organized_links", {})
            }
        else:
            return {
                "success": False,
                "message": f"Failed to scan links on {url}: {result.get('error', 'Unknown error')}",
                "url": url,
                "error": result.get("error", "Unknown error")
            }
            
    except Exception as e:
        logger.error(f"Error during link scanning: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to scan links: {str(e)}",
            "url": url,
            "error": str(e)
        }

if __name__ == "__main__":
    # Simple test
    import json
    
    url = "https://terragrunt.gruntwork.io/docs"
    result = crawl4ai_scan_links(url)
    
    print(json.dumps(result, indent=2))
