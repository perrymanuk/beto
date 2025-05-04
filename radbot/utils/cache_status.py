"""Command-line utility for checking cache performance statistics."""

import argparse
import json
import sys
from typing import Dict, Any

from google.adk.tools.tool_context import ToolContext


def get_cache_stats() -> Dict[str, Any]:
    """Get cache performance statistics.
    
    Returns:
        Dictionary of statistics
    """
    if hasattr(ToolContext, "cache_telemetry"):
        return ToolContext.cache_telemetry.get_stats()
    else:
        return {"error": "Cache telemetry not available"}


def print_stats(stats: Dict[str, Any], json_format: bool = False) -> None:
    """Print cache performance statistics.
    
    Args:
        stats: Statistics dictionary
        json_format: Whether to print in JSON format
    """
    if json_format:
        print(json.dumps(stats, indent=2))
    else:
        print("Cache Performance Statistics")
        print("===========================")
        
        if "error" in stats:
            print(f"Error: {stats['error']}")
            return
        
        print(f"Total requests:      {stats.get('total_requests', 0)}")
        print(f"Cache hit rate:      {stats.get('hit_rate', 0) * 100:.1f}%")
        print(f"Cache miss rate:     {stats.get('miss_rate', 0) * 100:.1f}%")
        print(f"Avg hit latency:     {stats.get('avg_hit_latency_ms', 0):.1f} ms")
        print(f"Avg miss latency:    {stats.get('avg_miss_latency_ms', 0):.1f} ms")
        print(f"Latency reduction:   {stats.get('latency_reduction', 0) * 100:.1f}%")
        print(f"Est. token savings:  {stats.get('estimated_token_savings', 0)}")
        print(f"Uptime:              {stats.get('uptime_seconds', 0) / 60:.1f} minutes")
        
        print("\nMost Frequent Cache Entries:")
        for key, hits in stats.get('most_frequent_entries', []):
            print(f"  {key[:8]}... : {hits} hits")


def main() -> None:
    """Main function for the cache status utility."""
    parser = argparse.ArgumentParser(description="Get cache performance statistics")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    args = parser.parse_args()
    
    # Get stats
    stats = get_cache_stats()
    
    # Print stats
    print_stats(stats, args.json)


if __name__ == "__main__":
    main()