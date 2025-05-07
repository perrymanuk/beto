"""
Agent transfer functionality for backward compatibility.

This module redirects to the ADK implementation of transfer_to_agent.
"""

import logging
from typing import Optional, Any

# Import the ADK transfer_to_agent function
from google.adk.tools.transfer_to_agent_tool import transfer_to_agent

# Setup logging
logger = logging.getLogger(__name__)

# Create a wrapper class with the same interface as expected by older code
class AgentTransferTool:
    """
    Wrapper around transfer_to_agent for backward compatibility.
    
    This class emulates the old interface while using the new ADK tool.
    """
    
    def __init__(self):
        self.name = "transfer_to_agent"
        self.description = "Transfers control to another agent"
        # Reference to the real function
        self._transfer_fn = transfer_to_agent
    
    def __call__(self, agent_name: str, **kwargs) -> Any:
        """Call the transfer_to_agent function with the given agent name."""
        logger.info(f"AgentTransferTool wrapper transferring to {agent_name}")
        return self._transfer_fn(agent_name=agent_name, **kwargs)

# For backward compatibility
transfer_to_agent_tool = AgentTransferTool()