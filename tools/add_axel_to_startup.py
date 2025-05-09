#\!/usr/bin/env python3
"""
Add Axel agent to the RadBot startup.

This script modifies the agent_core.py file to automatically create 
and register the Axel agent during initial agent creation.
"""

import os
import re
import sys
from typing import Optional

# Add the parent directory to the path so we can import radbot
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def add_axel_to_startup() -> bool:
    """
    Modify agent_core.py to add Axel to the startup process.
    
    Returns:
        True if successful, False otherwise.
    """
    # Find the agent_core.py file
    agent_core_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'radbot', 
        'agent', 
        'agent_core.py'
    )
    
    if not os.path.exists(agent_core_path):
        print(f"Error: Could not find agent_core.py at {agent_core_path}")
        return False
    
    # Read the current content
    with open(agent_core_path, 'r') as f:
        content = f.read()
    
    # Check if Axel is already imported
    if "from radbot.agent.specialized_agent_factory import create_specialized_agents" in content:
        print("Axel import already found in agent_core.py")
        return True
    
    # Add the import statements
    import_regex = r"from radbot\.agent\.agent_tools_setup import \(\s*tools,\s*setup_before_agent_call,\s*search_agent,\s*code_execution_agent,\s*scout_agent\s*\)"
    
    # Define the updated import statement
    updated_import = """from radbot.agent.agent_tools_setup import (
    tools,
    setup_before_agent_call,
    search_agent,
    code_execution_agent,
    scout_agent
)

# Import specialized agents factory
from radbot.agent.specialized_agent_factory import create_specialized_agents"""
    
    # Replace the import statement
    if re.search(import_regex, content):
        content = re.sub(import_regex, updated_import, content)
    else:
        print("Could not find the import statement to replace")
        return False
    
    # Add the code to create specialized agents 
    root_agent_regex = r"root_agent = Agent\(\s*model=model_name,\s*name=\"beto\",\s*instruction=instruction,\s*global_instruction=f\"\"\"Today's date: {today}\"\"\",\s*sub_agents=\[search_agent, code_execution_agent, scout_agent\],\s*tools=tools,\s*before_agent_callback=setup_before_agent_call,\s*generate_content_config=types\.GenerateContentConfig\(temperature=0\.2\),\s*\)"
    
    # Define the updated root_agent creation code
    updated_root_agent = """root_agent = Agent(
    model=model_name,
    name="beto",
    instruction=instruction,
    global_instruction=f\"\"\"Today's date: {today}\"\"\",
    sub_agents=[search_agent, code_execution_agent, scout_agent],
    tools=tools,
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

# Create specialized agents (including Axel)
specialized_agents = create_specialized_agents(root_agent)
logger.info(f"Created {len(specialized_agents)} specialized agents (including Axel)")"""
    
    # Replace the root_agent creation code
    if re.search(root_agent_regex, content):
        content = re.sub(root_agent_regex, updated_root_agent, content)
    else:
        print("Could not find the root_agent creation code to replace")
        return False
    
    # Write the updated content
    with open(agent_core_path, 'w') as f:
        f.write(content)
    
    print(f"Successfully updated {agent_core_path} to add Axel to startup")
    return True

def main():
    """Add Axel to startup."""
    success = add_axel_to_startup()
    if success:
        print("Successfully added Axel to RadBot startup")
        return 0
    else:
        print("Failed to add Axel to RadBot startup")
        return 1

if __name__ == "__main__":
    sys.exit(main())
