#\!/usr/bin/env python3
"""
Fix circular references in the agent tree.

This script addresses the circular references between agents by updating the
agent registration approach to use a safer pattern.
"""

import logging
import os
import sys
import re
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def fix_agent_factory():
    """
    Fix the specialized agent factory to handle circular references better.
    
    This function updates the specialized_agent_factory.py file to use a safer
    approach for bidirectional links between agents.
    """
    # Find the specialized_agent_factory.py file
    factory_py_path = os.path.join(os.path.dirname(__file__), '..', 'radbot', 'agent', 'specialized_agent_factory.py')
    
    if not os.path.exists(factory_py_path):
        logger.error(f"Could not find specialized_agent_factory.py at {factory_py_path}")
        return False
    
    logger.info(f"Found specialized_agent_factory.py at {factory_py_path}")
    
    # Read the file
    with open(factory_py_path, 'r') as f:
        content = f.read()
    
    # Find the part where we add bidirectional links
    scout_axel_link_pattern = r'if scout_agent:[^}]*\# Make Scout aware of Axel[^}]*\# Make Axel aware of Scout[^}]*'
    scout_axel_section = re.search(scout_axel_link_pattern, content, re.DOTALL)
    
    if not scout_axel_section:
        logger.error("Could not find Scout-Axel bidirectional link section")
        return False
    
    # Extract the section
    scout_axel_code = scout_axel_section.group(0)
    logger.info("Found Scout-Axel bidirectional link section")
    
    # Create the improved code that uses a safer pattern
    improved_code = """
        if scout_agent:
            # Create bidirectional links more safely
            
            # First, create weak references to avoid full circular references
            from weakref import proxy
            
            # Make Scout aware of Axel
            scout_sub_agents = list(scout_agent.sub_agents) if hasattr(scout_agent, 'sub_agents') and scout_agent.sub_agents else []
            
            # Check if Axel is already in Scout's sub_agents
            axel_already_added = False
            for agent in scout_sub_agents:
                if hasattr(agent, 'name') and agent.name == "axel_agent":
                    axel_already_added = True
                    break
                    
            if not axel_already_added:
                # Add a weak reference to avoid strong circular refs
                scout_sub_agents.append(proxy(axel_agent))
                scout_agent.sub_agents = scout_sub_agents
                logger.info("Added Scout → Axel reference (using proxy)")
                
            # Store Axel's scout reference separately
            # Note: We don't create a full bidirectional link to avoid serialization issues
            if not hasattr(axel_agent, '_associated_agents'):
                axel_agent._associated_agents = {}
            
            axel_agent._associated_agents['scout'] = scout_agent.name
            logger.info("Added Axel → Scout reference (using named reference)")
            
            # Also create a helper function to find associated agents at runtime
            def find_agent_by_name(agent_tree, name, visited=None):
                if visited is None:
                    visited = set()
                
                agent_id = id(agent_tree)
                if agent_id in visited:
                    return None
                
                visited.add(agent_id)
                
                if hasattr(agent_tree, 'name') and agent_tree.name == name:
                    return agent_tree
                
                if hasattr(agent_tree, 'sub_agents') and agent_tree.sub_agents:
                    for sub_agent in agent_tree.sub_agents:
                        result = find_agent_by_name(sub_agent, name, visited)
                        if result:
                            return result
                
                return None
            
            # Add the helper to axel agent
            axel_agent.find_agent_by_name = find_agent_by_name
            logger.info("Added find_agent_by_name helper to Axel agent")
"""
    
    # Replace the original code with the improved code
    updated_content = content.replace(scout_axel_code, improved_code)
    
    # Write the updated content back to the file
    if content != updated_content:
        with open(factory_py_path, 'w') as f:
            f.write(updated_content)
        logger.info(f"Updated {factory_py_path} with improved bidirectional link code")
    else:
        logger.warning("No changes made to the file - content is identical")
        
    return True

def main():
    """Fix circular references."""
    success = fix_agent_factory()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
