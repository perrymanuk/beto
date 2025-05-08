"""
Agent info API endpoint for RadBot web interface.

This module provides an API endpoint for retrieving agent and model information.
"""
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends

from radbot.config import config_manager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/agent-info",
    tags=["agent-info"],
)

@router.get("")
async def get_agent_info() -> Dict[str, Any]:
    """Get information about the current agent and models.
    
    Returns:
        Dict containing agent information.
    """
    # Get the main agent and model information
    main_model = config_manager.get_main_model()
    scout_model = config_manager.get_agent_model("scout_agent")
    search_model = config_manager.get_agent_model("search_agent")
    code_model = config_manager.get_agent_model("code_execution_agent")
    todo_model = config_manager.get_agent_model("todo_agent")
    
    # Log all the models for debugging
    logger.info(f"Main model: {main_model}")
    logger.info(f"Scout agent model: {scout_model}")
    logger.info(f"Search agent model: {search_model}")
    logger.info(f"Code execution agent model: {code_model}")
    logger.info(f"Todo agent model: {todo_model}")
    
    info = {
        "agent_name": "BETO",  # Default main agent name
        "model": main_model,
        "agent_models": {
            "beto": main_model,
            "scout_agent": scout_model,
            "scout": scout_model,  # Add lowercase version for easier lookup
            "search_agent": search_model,
            "code_execution_agent": code_model,
            "todo_agent": todo_model,
        }
    }
    
    logger.info(f"Providing agent info: {info}")
    return info

# Register agent_info router in the main FastAPI app
def register_agent_info_router(app):
    """Register agent_info router with the FastAPI app.
    
    Args:
        app: FastAPI application
    """
    app.include_router(router)
    logger.info("Registered agent_info router")