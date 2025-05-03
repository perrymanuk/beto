#!/usr/bin/env python3
"""
Crawl4AI Link Extraction Module

This module provides functionality to extract links from a webpage without
performing deep crawling. This is useful for showing available navigation
options to the user before committing to a full crawl.
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

async def _extract_links_from_url(url: str, follow_external: bool = False) -> Dict[str, Any]:
    """
    Extract all links from a URL without deep crawling.
    
    Args:
        url: The URL to process
        follow_external: Whether to include external links in the results
        
    Returns:
        Dictionary with the extraction results
    """
    logger.info(f"Extracting links from URL: {url}")
    
    # Validate URL
    if not url or not isinstance(url, str):
        error_msg = f"Invalid URL parameter: {url!r}"
        logger.error(error_msg)
        return {
            "success": False,
            "message": error_msg,
            "error": "URL must be a non-empty string"
        }
    
    try:
        # Set up browser configuration
        browser_config = BrowserConfig(
            headless=True,
            verbose=False
        )
        
        # Configure the run parameters
        run_config = CrawlerRunConfig(
            word_count_threshold=10,  # Skip very small content blocks
            verbose=False
        )
        
        # Extract domain for filtering external links
        base_domain = urlparse(url).netloc
        
        # Create crawler and process URL
        links = []
        async with AsyncWebCrawler(config=browser_config) as crawler:
            # Crawl the URL
            result = await crawler.arun(
                url=url,
                config=run_config
            )
            
            # Process the result
            if result and hasattr(result, "success") and result.success:
                # Extract title and content for the main page
                title = result.title if hasattr(result, "title") else url.split("/")[-1]
                content = result.markdown if hasattr(result, "markdown") else ""
                
                # Extract links from HTML
                if hasattr(result, "html") and result.html:
                    soup = BeautifulSoup(result.html, "html.parser")
                    
                    # Process all links
                    for a_tag in soup.find_all("a", href=True):
                        href = a_tag["href"]
                        link_text = a_tag.get_text(strip=True)
                        
                        # Skip empty links, fragments, or javascript
                        if not href or href.startswith("#") or href.startswith("javascript:"):
                            continue
                        
                        # Normalize relative URLs
                        if not href.startswith(("http://", "https://")):
                            href = urljoin(url, href)
                        
                        # Check if it's an external link
                        link_domain = urlparse(href).netloc
                        is_external = link_domain != base_domain
                        
                        # Skip external links if not requested
                        if not follow_external and is_external:
                            continue
                        
                        # Add to links list
                        links.append({
                            "url": href,
                            "text": link_text or href,  # Use URL if no link text
                            "is_external": is_external
                        })
                
                # Group links by section/category (based on URL path)
                grouped_links = {}
                for link in links:
                    link_path = urlparse(link["url"]).path
                    
                    # Try to extract a section name from the path
                    path_parts = [p for p in link_path.split("/") if p]
                    if len(path_parts) > 0:
                        # Use first path component as section
                        section = path_parts[0]
                    else:
                        section = "Main"
                    
                    # Add to section
                    if section not in grouped_links:
                        grouped_links[section] = []
                    
                    grouped_links[section].append(link)
                
                # Create the response
                return {
                    "success": True,
                    "message": f"Successfully extracted {len(links)} links from {url}",
                    "url": url,
                    "title": title,
                    "links_count": len(links),
                    "links": links,
                    "grouped_links": grouped_links,
                    "content_preview": content[:500] + "..." if len(content) > 500 else content
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to extract links from {url}",
                    "url": url,
                    "error": "Failed to process URL"
                }
    
    except Exception as e:
        logger.error(f"Error extracting links from {url}: {str(e)}")
        return {
            "success": False,
            "message": f"Error extracting links: {str(e)}",
            "url": url,
            "error": str(e)
        }

def crawl4ai_extract_links(url: str, follow_external: bool = False) -> Dict[str, Any]:
    """
    Extract all links from a URL without deep crawling.
    
    This function is useful for getting an overview of a site's structure
    before committing to a full crawl. The returned links can then be
    used to selectively crawl specific sections using crawl4ai_ingest_url.
    
    Args:
        url: The URL to extract links from
        follow_external: Whether to include external links in the results
        
    Returns:
        Dictionary containing:
        - success: Whether the operation succeeded
        - links: List of all extracted links
        - grouped_links: Links grouped by section/category
        - content_preview: Preview of the page content
    """
    logger.info(f"Crawl4AI extracting links from: {url}")
    
    # Run link extraction asynchronously
    result = run_async_safely(_extract_links_from_url(
        url=url,
        follow_external=follow_external
    ))
    
    return result
