"""
Factory for creating voice-enabled agents.

This module provides factories for creating Google ADK agents that are
configured for voice input and output.
"""

import logging
import os
from typing import List, Any, Optional

from google.adk.agents import Agent, BaseAgent

from radbot.config import config_manager

# Set up logging
logger = logging.getLogger(__name__)

def create_voice_enabled_agent(
    name: str = "voice_agent",
    description: str = "A helpful assistant that can chat via voice.",
    instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    model: Optional[str] = None
) -> BaseAgent:
    """
    Create a voice-enabled ADK agent.
    
    Args:
        name: Name of the agent
        description: Description of the agent
        instruction: Instruction for the agent
        tools: List of tools to include
        model: Model to use
        
    Returns:
        BaseAgent: Voice-enabled ADK agent
    """
    # Use default instruction if not provided
    if instruction is None:
        try:
            instruction = config_manager.get_instruction("voice_agent")
        except Exception as e:
            logger.warning(f"Failed to load voice_agent instruction: {e}")
            instruction = """
            You are a voice-enabled assistant with a focus on natural conversation.
            
            Important guidelines for voice output:
            1. Keep responses concise and conversational. People are listening, not reading.
            2. Avoid markdown formatting, code blocks, tables, or any other formatted text.
            3. Use simple, clear language. Mention when something would be better shown visually.
            4. Break complex information into shorter sentences and chunks.
            5. Be mindful of pacing - don't list many options all at once.
            
            Respond naturally as if you're having a spoken conversation. 
            """
    
    # Use model from environment or config if not provided
    if model is None:
        # Try to get from environment first
        model = os.environ.get("VOICE_ENABLED_MODEL", None)
        
        # If not in environment, use the main model from config
        if not model:
            model = config_manager.get_main_model()
            logger.info(f"Using main model from config: {model}")
    
    # Create tools list if not provided
    if tools is None:
        tools = []
    
    # Create the agent
    agent = Agent(
        name=name,
        model=model,
        description=description,
        instruction=instruction,
        tools=tools
    )
    
    logger.info(f"Created voice-enabled agent with model {model}")
    return agent
