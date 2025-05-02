#!/usr/bin/env python3
"""
Direct Home Assistant API check script.

Makes a direct REST API call to Home Assistant to get all states and filters for specific entities.
"""

import os
import sys
import json
import argparse
import requests
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_all_states(ha_url: str, ha_token: str) -> Optional[List[Dict[str, Any]]]:
    """
    Make a direct REST API call to Home Assistant to get all entity states.
    
    Args:
        ha_url: Home Assistant URL
        ha_token: Home Assistant auth token
        
    Returns:
        List of entity state objects or None if the request fails
    """
    # Ensure URL ends with /api/states
    if not ha_url.endswith('/api/states'):
        ha_url = f"{ha_url.rstrip('/')}/api/states"
        
    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json",
    }
    
    try:
        response = requests.get(ha_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4xx/5xx responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making request to Home Assistant: {e}")
        return None

def filter_entities(entities: List[Dict[str, Any]], search_term: str, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Filter entities by search term and optionally by domain.
    
    Args:
        entities: List of entity state objects
        search_term: Term to search for in entity IDs and friendly names
        domain: Optional domain to filter by
        
    Returns:
        List of matching entity state objects
    """
    search_term = search_term.lower()
    results = []
    
    for entity in entities:
        entity_id = entity.get('entity_id', '').lower()
        friendly_name = entity.get('attributes', {}).get('friendly_name', '').lower()
        
        # Apply domain filter if provided
        if domain and not entity_id.startswith(f"{domain}."):
            continue
            
        # Check if search term is in entity ID or friendly name
        if search_term in entity_id or search_term in friendly_name:
            results.append(entity)
            
    return results

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Check Home Assistant entities directly via REST API')
    parser.add_argument('--search', '-s', help='Search term to filter entities by', default='')
    parser.add_argument('--domain', '-d', help='Domain to filter entities by (e.g., light, switch)')
    parser.add_argument('--url', help='Home Assistant URL (overrides HA_URL env var)')
    parser.add_argument('--token', help='Home Assistant token (overrides HA_TOKEN env var)')
    parser.add_argument('--list-domains', action='store_true', help='List all available domains')
    parser.add_argument('--output', '-o', help='Output file path for full JSON results')
    args = parser.parse_args()
    
    # Get Home Assistant URL and token
    ha_url = args.url or os.getenv('HA_URL')
    ha_token = args.token or os.getenv('HA_TOKEN')
    
    if not ha_url or not ha_token:
        print("Error: Home Assistant URL and token are required.")
        print("Set HA_URL and HA_TOKEN environment variables or use --url and --token options.")
        sys.exit(1)
    
    print(f"Connecting to Home Assistant at {ha_url}...")
    entities = get_all_states(ha_url, ha_token)
    
    if not entities:
        print("Failed to retrieve entities from Home Assistant.")
        sys.exit(1)
    
    print(f"Successfully retrieved {len(entities)} entities from Home Assistant.")
    
    # If requested, write full JSON output to a file
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(entities, f, indent=2)
        print(f"Full entity list written to {args.output}")
    
    # List domains if requested
    if args.list_domains:
        domains = set()
        for entity in entities:
            entity_id = entity.get('entity_id', '')
            if '.' in entity_id:
                domain = entity_id.split('.')[0]
                domains.add(domain)
        
        print(f"\nAvailable domains ({len(domains)}):")
        for domain in sorted(domains):
            # Count entities in each domain
            count = sum(1 for e in entities if e.get('entity_id', '').split('.')[0] == domain)
            print(f"  - {domain}: {count} entities")
    
    # Filter entities if a search term is provided
    if args.search or args.domain:
        matched_entities = filter_entities(entities, args.search, args.domain)
        
        print(f"\nMatched {len(matched_entities)} entities:")
        for entity in matched_entities:
            entity_id = entity.get('entity_id', '')
            state = entity.get('state', '')
            friendly_name = entity.get('attributes', {}).get('friendly_name', '')
            
            print(f"  - {entity_id}: {state} ({friendly_name})")
            
        if not matched_entities:
            print("No entities matched the search criteria.")
            
            # If searching for a specific entity ID, check if the domain exists
            if '.' in args.search:
                domain = args.search.split('.')[0]
                domain_exists = any(e.get('entity_id', '').startswith(f"{domain}.") for e in entities)
                
                if domain_exists:
                    print(f"The domain '{domain}' exists but no entity with ID '{args.search}' was found.")
                else:
                    print(f"The domain '{domain}' does not exist in your Home Assistant instance.")
    
if __name__ == '__main__':
    main()