"""
Tools for transferring between agents in a multi-agent system.
"""

import logging
from typing import Dict, Any, Optional

from google.adk.agents import QueryResponse
from google.adk.tools import FunctionTool

logger = logging.getLogger(__name__)


def transfer_to_agent(agent_name: str, message: Optional[str] = None) -> Dict[str, Any]:
    """
    Transfer control to another agent.
    
    Args:
        agent_name: The name of the agent to transfer to
        message: Optional message to send to the transferred agent
    
    Returns:
        A dictionary confirming the transfer
    """
    logger.info(f"Transferring to agent: {agent_name}")
    
    # Create a transfer response using ADK 0.3.0 structure
    response = QueryResponse(
        transfer_to_agent_response={
            "target_app_name": agent_name,
            "message": message or "",
        }
    )
    
    # Return a confirmation
    return {
        "status": "success",
        "transferredTo": agent_name,
        "message": message or f"Transferred to {agent_name}"
    }


def create_transfer_tool() -> FunctionTool:
    """
    Create a function tool for transferring between agents.
    
    Returns:
        FunctionTool for transfer_to_agent
    """
    return FunctionTool(
        name="transfer_to_agent",
        description="Transfer control to another agent",
        parameters={
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "The name of the agent to transfer to (e.g., 'radbot_web', 'technical_research_agent')"
                },
                "message": {
                    "type": "string",
                    "description": "Optional message to send to the transferred agent"
                }
            },
            "required": ["agent_name"]
        }
    )
