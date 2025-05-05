"""
Session management for RadBot web interface.

This module handles session management for the RadBot web interface.
"""
import asyncio
import logging
import os
from typing import Dict, Optional, Any

from fastapi import Depends

from radbot.agent.agent import RadBotAgent, create_agent

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class SessionManager:
    """Manager for web sessions and their associated agents."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, RadBotAgent] = {}
        self.lock = asyncio.Lock()
        logger.info("Session manager initialized")
    
    async def get_agent(self, session_id: str) -> Optional[RadBotAgent]:
        """Get agent for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            RadBotAgent instance or None if session not found
        """
        async with self.lock:
            return self.sessions.get(session_id)
    
    async def set_agent(self, session_id: str, agent: RadBotAgent):
        """Set agent for a session.
        
        Args:
            session_id: Session ID
            agent: RadBotAgent instance
        """
        async with self.lock:
            self.sessions[session_id] = agent
            logger.info(f"Agent set for session {session_id}")
    
    async def reset_session(self, session_id: str):
        """Reset a session.
        
        Args:
            session_id: Session ID to reset
        """
        agent = await self.get_agent(session_id)
        if agent:
            user_id = f"web_user_{session_id}"
            agent.reset_session(user_id)
            logger.info(f"Reset session {session_id}")
        else:
            logger.warning(f"Attempted to reset non-existent session {session_id}")

    async def remove_session(self, session_id: str):
        """Remove a session.
        
        Args:
            session_id: Session ID to remove
        """
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Removed session {session_id}")
            else:
                logger.warning(f"Attempted to remove non-existent session {session_id}")

# Singleton session manager
_session_manager = SessionManager()

def get_session_manager() -> SessionManager:
    """Get the session manager.
    
    Returns:
        SessionManager instance
    """
    return _session_manager

async def get_or_create_agent_for_session(
    session_id: str, 
    session_manager: SessionManager = Depends(get_session_manager)
) -> RadBotAgent:
    """Get or create an agent for a session.
    
    Args:
        session_id: Session ID
        session_manager: SessionManager instance
        
    Returns:
        RadBotAgent instance
    """
    # Check if we already have an agent for this session
    agent = await session_manager.get_agent(session_id)
    if agent:
        logger.info(f"Using existing agent for session {session_id}")
        return agent
    
    # Create a new agent for this session
    logger.info(f"Creating new agent for session {session_id}")
    
    try:
        # Try to use the create_agent function directly first
        from radbot.agent.agent import create_agent
        
        # Explicitly import session and memory services
        from google.adk.sessions import InMemorySessionService
        from radbot.memory.qdrant_memory import QdrantMemoryService
        from radbot.config import config_manager
        
        # Create a session service
        session_service = InMemorySessionService()
        
        # Create memory service
        try:
            memory_service = QdrantMemoryService()
            logger.info("Created memory service successfully")
        except Exception as e:
            logger.error(f"Failed to create memory service: {str(e)}")
            memory_service = None
        
        # Get the instruction from config
        try:
            instruction = config_manager.get_instruction("main_agent")
        except Exception as e:
            logger.warning(f"Failed to load main_agent instruction: {str(e)}")
            instruction = "You are a helpful assistant with access to tools and memory."
        
        # Get the model from config
        model = config_manager.get_main_model()
        
        # Create the agent with all components directly
        from radbot.agent.agent import RadBotAgent
        from google.adk.agents import Agent
        from google.adk.runners import Runner
        
        # Create the tools - start with basic tools
        from radbot.tools.basic import get_current_time, get_weather
        basic_tools = [get_current_time, get_weather]
        
        # Try to add memory tools
        try:
            from radbot.tools.memory.memory_tools import search_past_conversations, store_important_information
            memory_tools = [search_past_conversations, store_important_information]
            basic_tools.extend(memory_tools)
            logger.info("Added memory tools to agent")
        except Exception as e:
            logger.warning(f"Failed to add memory tools: {str(e)}")
        
        # Create the root agent
        root_agent = Agent(
            name="radbot_web_ui",
            model=model,
            instruction=instruction,
            tools=basic_tools,
            description="RadBot web UI agent"
        )
        
        # Create runner explicitly with app_name parameter
        runner = Runner(
            agent=root_agent,
            app_name="radbot",  # This is the required parameter that was missing
            session_service=session_service,
            memory_service=memory_service
        )
        
        # Monkey patch the Runner.__init__ method temporarily to avoid app_name issue
        original_runner_init = Runner.__init__
        
        def patched_runner_init(self, *args, **kwargs):
            if 'app_name' not in kwargs:
                kwargs['app_name'] = 'radbot'
            return original_runner_init(self, *args, **kwargs)
        
        # Apply the monkey patch
        Runner.__init__ = patched_runner_init
        
        try:
            # Create the RadBotAgent wrapper with the patch applied
            agent = RadBotAgent(
                name="radbot_web_ui",
                session_service=session_service,
                tools=basic_tools,
                model=model,
                instruction=instruction,
                memory_service=memory_service
            )
        finally:
            # Restore the original Runner.__init__ method
            Runner.__init__ = original_runner_init
        
        # Set app_name explicitly
        agent.app_name = "radbot"
        
        logger.info("Created agent with explicit parameter setup for web UI")
    except Exception as e:
        logger.error(f"Error creating agent: {str(e)}", exc_info=True)
        raise
    
    # Store the agent in the session manager
    await session_manager.set_agent(session_id, agent)
    
    return agent