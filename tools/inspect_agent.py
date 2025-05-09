#\!/usr/bin/env python3
"""
Inspect the state of the agent system.

This script will inspect the current state of the agent system,
showing the agent tree, tools, and configurations to help debug issues.
"""

import logging
import os
import sys
import json
from typing import Dict, List, Any, Optional, Set

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def inspect_agent(agent, indent="", visited_agents=None) -> Dict[str, Any]:
    """
    Recursively inspect an agent and its sub-agents.
    
    Args:
        agent: The agent to inspect
        indent: Indentation for logging
        visited_agents: Set of agent identities already visited (to prevent circular refs)
        
    Returns:
        Dictionary with agent information
    """
    # Initialize visited_agents set if not provided
    if visited_agents is None:
        visited_agents = set()
    
    info = {}
    
    # Generate agent identity (for tracking visited agents)
    agent_id = id(agent)
    
    # If we've already visited this agent, just return a reference
    if agent_id in visited_agents:
        name = agent.name if hasattr(agent, 'name') else "unnamed"
        logger.info(f"{indent}Agent: {name} (circular reference, already visited)")
        return {"name": name, "circular_reference": True}
    
    # Add this agent to the visited set
    visited_agents.add(agent_id)
    
    # Get basic agent info
    name = agent.name if hasattr(agent, 'name') else "unnamed"
    agent_type = type(agent).__name__
    
    info["name"] = name
    info["type"] = agent_type
    
    # Log basic info
    logger.info(f"{indent}Agent: {name} (Type: {agent_type})")
    
    # Get model info
    if hasattr(agent, 'model'):
        model = agent.model
        info["model"] = str(model)
        logger.info(f"{indent}Model: {model}")
    
    # Get tools info
    if hasattr(agent, 'tools') and agent.tools:
        tool_names = []
        for tool in agent.tools:
            tool_name = None
            if hasattr(tool, 'name'):
                tool_name = tool.name
            elif hasattr(tool, '__name__'):
                tool_name = tool.__name__
            else:
                tool_name = str(tool)
            tool_names.append(tool_name)
        
        info["tools"] = tool_names
        logger.info(f"{indent}Tools: {len(tool_names)} tools")
        logger.info(f"{indent}Tool names: {', '.join(tool_names[:5])}{'...' if len(tool_names) > 5 else ''}")
    else:
        info["tools"] = []
        logger.info(f"{indent}Tools: None")
    
    # Get sub-agents info
    sub_agents_info = []
    if hasattr(agent, 'sub_agents') and agent.sub_agents:
        logger.info(f"{indent}Sub-agents: {len(agent.sub_agents)} agents")
        
        # Recursively inspect sub-agents
        for sub_agent in agent.sub_agents:
            sub_info = inspect_agent(sub_agent, indent + "  ", visited_agents)
            sub_agents_info.append(sub_info)
    else:
        logger.info(f"{indent}Sub-agents: None")
    
    info["sub_agents"] = sub_agents_info
    
    return info

def main():
    """Inspect the agent system."""
    # Import the root agent
    try:
        from radbot.agent import root_agent
        logger.info(f"Found root agent: {root_agent.name if hasattr(root_agent, 'name') else 'unnamed'}")
    except ImportError:
        logger.error("Root agent not found. Run this after initializing the main agent.")
        return 1
    except SyntaxError as e:
        logger.error(f"Syntax error in imports: {e}")
        return 1
    
    # Inspect the agent tree
    logger.info("===== AGENT TREE INSPECTION =====")
    agent_info = inspect_agent(root_agent)
    
    # Write agent info to file
    output_file = os.path.join(os.path.dirname(__file__), "agent_inspection.json")
    try:
        with open(output_file, 'w') as f:
            json.dump(agent_info, f, indent=2)
        logger.info(f"Wrote agent inspection to {output_file}")
    except Exception as e:
        logger.error(f"Failed to write agent inspection to file: {e}")
    
    # Check for specific problems
    problems = []
    
    # Check if tool registrations are working
    if not agent_info.get("tools"):
        problems.append("Root agent has no tools registered")
    
    # Check if sub-agents are registered correctly
    if not agent_info.get("sub_agents"):
        problems.append("Root agent has no sub-agents registered")
    
    # Check for circular references between agents
    def check_for_circular_refs(agent_info):
        circular_refs = []
        if agent_info.get("circular_reference"):
            circular_refs.append(agent_info["name"])
        for sub_agent in agent_info.get("sub_agents", []):
            circular_refs.extend(check_for_circular_refs(sub_agent))
        return circular_refs
    
    circular_refs = check_for_circular_refs(agent_info)
    if circular_refs:
        problems.append(f"Circular references detected for agents: {', '.join(circular_refs)}")
    
    # Report problems
    if problems:
        logger.warning("===== DETECTED PROBLEMS =====")
        for problem in problems:
            logger.warning(f"- {problem}")
    else:
        logger.info("No obvious problems detected in agent structure")
    
    logger.info("Agent inspection complete")
    return 0

if __name__ == "__main__":
    sys.exit(main())
