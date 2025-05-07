# Agent Migration and Architecture Cleanup Plan

## Current Architecture Assessment

### Agent Structure
- **Root agent (beto)** - Defined in multiple files:
  - `/agent.py` - Main entry point for ADK web interface
  - `/radbot/agent.py` - Module-level wrapper
  - `/radbot/agent/agent.py` - Core implementation

- **Research agent (scout)** - Defined in:
  - `/radbot/agent/research_agent/agent.py` - Implementation
  - `/radbot/agent/research_agent/factory.py` - Creation functions

- **Built-in tools agents**:
  - **search_agent** - Uses Google's `google_search` built-in tool
  - **code_execution_agent** - Uses Google's `built_in_code_execution` built-in tool

### Current Issues
1. **Inconsistent Agent Registration**:
   - The `scout` agent is sometimes added directly to the sub-agents list
   - The built-in tool agents are registered in different ways in different places

2. **Parent-Child Relationship Problems**:
   - Agent relationship is established through multiple methods (parent_agent assignment, sub_agents list)
   - ADK 0.4.0 expects relationships to be established via sub_agents for proper transfers

3. **Monkey Patching in session.py**:
   - Excessive patching of ADK's internal agent lookup and routing functions
   - Creates brittle code that's hard to maintain and might break with ADK updates

4. **Tool Registration Inconsistencies**:
   - `transfer_to_agent` tool isn't consistently added to all agents
   - Built-in tools are sometimes added directly, sometimes via agent registration

5. **Naming Inconsistencies**:
   - Names used in transfers don't always match actual agent names
   - Agent name attributes are sometimes overwritten after creation

## Target Architecture

### Guiding Principles
1. **Standard ADK Patterns**:
   - Use ADK's official patterns for multi-agent systems
   - Avoid monkey patching completely
   - Use the proper parent-child relationship through sub_agents

2. **Agent Tool Approach**:
   - Set up specialized agents for specific tasks
   - Establish clear hierarchy with proper registration
   - Use transfer_to_agent for agent switching

### Target Agent Structure
```
root_agent (beto)
├── scout
│   ├── search_agent
│   └── code_execution_agent
├── search_agent
└── code_execution_agent
```

This structure ensures:
- Both the root agent and scout have access to built-in tool agents
- All parent-child relationships are properly established
- Transfers work natively without patching

## Migration Plan

### Phase 1: Standardize Agent Creation and Naming

1. **Update radbot/agent/agent.py**:
   - Modify `create_core_agent_for_web` to standardize agent creation
   - Ensure agent names are consistent and not overwritten
   - Implement proper parent-child relationships through sub_agents
   - Add transfer_to_agent to all agents

2. **Update radbot/agent/research_agent/factory.py**:
   - Update the create_research_agent function to ensure proper naming
   - Standardize how the agent gets its sub-agents
   - Always return an agent with name="scout"

### Phase 2: Reimplement Built-in Tool Integration

1. **Update radbot/tools/adk_builtin/search_tool.py**:
   - Fix the register_search_agent function to use proper parent-child pattern
   - Ensure transfer_to_agent is included in the agent's tools

2. **Update radbot/tools/adk_builtin/code_execution_tool.py**:
   - Follow the same pattern as search_tool.py
   - Ensure consistent registration and tool availability

### Phase 3: Remove Monkey Patching

1. **Rewrite radbot/web/api/session.py**:
   - Remove all monkey patching of ADK internals
   - Simplify the SessionRunner class to use standard ADK behavior
   - Use proper ADK initialization with app_name="beto"
   - Ensure the session manager uses consistent naming

### Phase 4: Deployment and Testing

1. **Create Test Cases**:
   - Test beto → scout transfers
   - Test beto → search_agent transfers
   - Test beto → code_execution_agent transfers
   - Test scout → beto transfers
   - Test scout → search_agent transfers
   - Test scout → code_execution_agent transfers

2. **Test Environment Variables**:
   - Test with RADBOT_ENABLE_ADK_SEARCH=true
   - Test with RADBOT_ENABLE_ADK_CODE_EXEC=true
   - Test with both enabled
   - Test with neither enabled

## Detailed Implementation Changes

### radbot/agent/agent.py
```python
def create_core_agent_for_web(
    tools: Optional[List[Any]] = None, 
    name: str = "beto", 
    app_name: str = "beto",
    include_google_search: bool = False,
    include_code_execution: bool = False
) -> Agent:
    """
    Create an ADK Agent for web interface with all necessary configurations.
    
    Args:
        tools: Optional list of tools to include
        name: Name for the agent (must be "beto" for consistent transfers)
        app_name: Application name (must match agent name for ADK 0.4.0+)
        include_google_search: If True, register a google_search sub-agent
        include_code_execution: If True, register a code_execution sub-agent
        
    Returns:
        Configured ADK Agent for web interface
    """
    # Ensure agent name is always "beto" for consistent transfers
    if name != "beto":
        logger.warning(f"Agent name '{name}' changed to 'beto' for consistent transfers")
        name = "beto"
        
    # Ensure app_name matches agent name for ADK 0.4.0+
    if app_name != name:
        logger.warning(f"app_name '{app_name}' changed to '{name}' for ADK 0.4.0+ compatibility")
        app_name = name
        
    # Create the base agent with proper name and app_name
    agent = AgentFactory.create_web_agent(
        name=name,
        model=None,  # Will use config default
        tools=tools,
        instruction_name="main_agent",
        config=None,  # Will use global config
        register_tools=True
    )
    
    # Import required components for agent transfers
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Ensure agent has transfer_to_agent tool
    if hasattr(agent, 'tools'):
        # Check if tool already exists
        has_transfer_tool = False
        for tool in agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
            if tool_name == 'transfer_to_agent':
                has_transfer_tool = True
                break
                
        if not has_transfer_tool:
            agent.tools.append(transfer_to_agent)
            logger.info("Added transfer_to_agent tool to root agent")
    
    # Create sub-agents if requested
    sub_agents = []
    
    # Add built-in tool agents if requested
    if include_google_search or include_code_execution:
        try:
            from radbot.tools.adk_builtin import create_search_agent, create_code_execution_agent
            
            if include_google_search:
                try:
                    search_agent = create_search_agent(name="search_agent")
                    # Make sure search_agent has transfer_to_agent
                    if hasattr(search_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in search_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            search_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(search_agent)
                    logger.info("Created search_agent as sub-agent")
                except Exception as e:
                    logger.warning(f"Failed to create search agent: {str(e)}")
            
            if include_code_execution:
                try:
                    code_agent = create_code_execution_agent(name="code_execution_agent")
                    # Make sure code_agent has transfer_to_agent
                    if hasattr(code_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in code_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            code_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(code_agent)
                    logger.info("Created code_execution_agent as sub-agent")
                except Exception as e:
                    logger.warning(f"Failed to create code execution agent: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to import built-in tool factories: {str(e)}")
    
    # Create scout agent if needed
    try:
        from radbot.agent.research_agent import create_research_agent
        
        # Pass the same settings to create consistent behavior
        scout_agent = create_research_agent(
            name="scout",  # MUST be "scout" for consistent transfers
            model=None,  # Will use config default
            tools=tools,  # Pass the same tools as the root agent
            as_subagent=False,  # Get the ADK agent directly
            enable_google_search=include_google_search,
            enable_code_execution=include_code_execution,
            app_name=app_name  # Same app_name for consistency
        )
        
        # Add to sub-agents
        sub_agents.append(scout_agent)
        logger.info("Added scout agent as sub-agent")
    except Exception as e:
        logger.warning(f"Failed to create scout agent: {str(e)}")
    
    # Set sub-agents list on the agent
    if sub_agents:
        agent.sub_agents = sub_agents
        logger.info(f"Added {len(sub_agents)} sub-agents to root agent")
        
        # Log the agent tree for debugging
        sub_agent_names = [sa.name for sa in agent.sub_agents if hasattr(sa, 'name')]
        logger.info(f"Agent tree: root='{agent.name}', sub_agents={sub_agent_names}")
    
    return agent
```

### radbot/agent/research_agent/factory.py
```python
def create_research_agent(
    name: str = "scout",
    model: Optional[str] = None,
    custom_instruction: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    as_subagent: bool = True,
    enable_google_search: bool = False,
    enable_code_execution: bool = False,
    app_name: str = "beto"
) -> Union[ResearchAgent, Any]:
    """
    Create a research agent with the specified configuration.
    
    Args:
        name: Name of the agent (should be "scout" for consistent transfers)
        model: LLM model to use (defaults to config setting)
        custom_instruction: Optional custom instruction to override the default
        tools: List of tools to provide to the agent
        as_subagent: Whether to return the ResearchAgent or the underlying ADK agent
        enable_google_search: Whether to enable Google Search capability
        enable_code_execution: Whether to enable Code Execution capability
        app_name: Application name (should match the parent agent name for ADK 0.4.0+)
        
    Returns:
        Union[ResearchAgent, Any]: The created agent instance
    """
    # Ensure agent name is always "scout" for consistent transfers
    if name != "scout":
        logger.warning(f"Agent name '{name}' changed to 'scout' for consistent transfers")
        name = "scout"
        
    # Use default model from config if not specified
    if model is None:
        model = config_manager.get_main_model()
        logger.info(f"Using model from config: {model}")
    
    # Create the research agent with explicit name and app_name
    research_agent = ResearchAgent(
        name=name,
        model=model,
        instruction=custom_instruction,  # Will use default if None
        tools=tools,
        enable_sequential_thinking=True,
        enable_google_search=enable_google_search,
        enable_code_execution=enable_code_execution,
        app_name=app_name  # Should match parent agent name
    )
    
    # Import required components for agent transfers
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Get the ADK agent
    adk_agent = research_agent.get_adk_agent()
    
    # Ensure agent has transfer_to_agent tool
    if hasattr(adk_agent, 'tools'):
        # Check if tool already exists
        has_transfer_tool = False
        for tool in adk_agent.tools:
            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
            if tool_name == 'transfer_to_agent':
                has_transfer_tool = True
                break
                
        if not has_transfer_tool:
            adk_agent.tools.append(transfer_to_agent)
            logger.info("Added transfer_to_agent tool to scout agent")
    
    # Create built-in tool sub-agents if requested
    sub_agents = []
    
    if enable_google_search or enable_code_execution:
        try:
            from radbot.tools.adk_builtin import create_search_agent, create_code_execution_agent
            
            if enable_google_search:
                try:
                    search_agent = create_search_agent(name="search_agent")
                    # Make sure search_agent has transfer_to_agent
                    if hasattr(search_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in search_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            search_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(search_agent)
                    logger.info("Created search_agent as sub-agent for scout")
                except Exception as e:
                    logger.warning(f"Failed to create search agent for scout: {str(e)}")
            
            if enable_code_execution:
                try:
                    code_agent = create_code_execution_agent(name="code_execution_agent")
                    # Make sure code_agent has transfer_to_agent
                    if hasattr(code_agent, 'tools'):
                        has_transfer_tool = False
                        for tool in code_agent.tools:
                            tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)
                            if tool_name == 'transfer_to_agent':
                                has_transfer_tool = True
                                break
                                
                        if not has_transfer_tool:
                            code_agent.tools.append(transfer_to_agent)
                            
                    sub_agents.append(code_agent)
                    logger.info("Created code_execution_agent as sub-agent for scout")
                except Exception as e:
                    logger.warning(f"Failed to create code execution agent for scout: {str(e)}")
        except Exception as e:
            logger.warning(f"Failed to import built-in tool factories for scout: {str(e)}")
    
    # Set sub-agents list on the scout agent
    if sub_agents and hasattr(adk_agent, 'sub_agents'):
        adk_agent.sub_agents = sub_agents
        logger.info(f"Added {len(sub_agents)} sub-agents to scout agent")
        
        # Log the agent tree for debugging
        sub_agent_names = [sa.name for sa in adk_agent.sub_agents if hasattr(sa, 'name')]
        logger.info(f"Scout agent tree: root='scout', sub_agents={sub_agent_names}")
    
    # Return either the ResearchAgent wrapper or the underlying ADK agent
    if as_subagent:
        return research_agent
    else:
        # Double-check agent name before returning
        if hasattr(adk_agent, 'name') and adk_agent.name != name:
            logger.warning(f"ADK Agent name mismatch: '{adk_agent.name}' not '{name}' - fixing")
            adk_agent.name = name
            
        return adk_agent
```

### radbot/tools/adk_builtin/search_tool.py
```python
def create_search_agent(
    name: str = "search_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "search_agent",
) -> Agent:
    """
    Create an agent with Google Search capabilities.
    
    Args:
        name: Name for the agent (should be "search_agent" for consistent transfers)
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        
    Returns:
        Agent with Google Search tool
    """
    # Ensure agent name is always "search_agent" for consistent transfers
    if name != "search_agent":
        logger.warning(f"Agent name '{name}' changed to 'search_agent' for consistent transfers")
        name = "search_agent"
        
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (must be a Gemini 2 model)
    model_name = model or cfg.get_main_model()
    if not any(name in model_name.lower() for name in ["gemini-2", "gemini-2.0", "gemini-2.5"]):
        logger.warning(
            f"Model {model_name} may not be compatible with google_search tool. "
            "Google Search tool requires Gemini 2 models."
        )
    
    # Get the instruction
    try:
        instruction = cfg.get_instruction(instruction_name)
    except FileNotFoundError:
        # Use a minimal instruction if the named one isn't found
        logger.warning(
            f"Instruction '{instruction_name}' not found for search agent, "
            "using minimal instruction"
        )
        instruction = (
            "You are a web search agent. When asked about recent events, news, "
            "or facts that may have changed since your training, use the Google Search "
            "tool to find current information. Always cite your sources clearly. "
            "When you don't need to search, answer from your knowledge. "
            "When your task is complete, transfer back to the main agent using "
            "transfer_to_agent(agent_name='beto') or transfer to another agent "
            "if needed using transfer_to_agent(agent_name='agent_name')."
        )
    
    # Import transfer_to_agent
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Create the search agent with both google_search and transfer_to_agent tools
    search_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction,
        description="A specialized agent that can search the web using Google Search.",
        tools=[google_search, transfer_to_agent]
    )
    
    # Enable search explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        from google.genai import types
        search_agent.config = types.GenerateContentConfig()
        search_agent.config.tools = [types.Tool(google_search=types.ToolGoogleSearch())]
        logger.info("Explicitly configured Google Search tool for Vertex AI")
    
    logger.info(f"Created search agent '{name}' with google_search tool")
    return search_agent
```

### radbot/tools/adk_builtin/code_execution_tool.py
```python
def create_code_execution_agent(
    name: str = "code_execution_agent",
    model: Optional[str] = None,
    config: Optional[ConfigManager] = None,
    instruction_name: str = "code_execution_agent",
) -> Agent:
    """
    Create an agent with Code Execution capabilities.
    
    Args:
        name: Name for the agent (should be "code_execution_agent" for consistent transfers)
        model: Optional model override (defaults to config's main_model)
        config: Optional config manager (uses global if not provided)
        instruction_name: Name of instruction to load from config
        
    Returns:
        Agent with Code Execution tool
    """
    # Ensure agent name is always "code_execution_agent" for consistent transfers
    if name != "code_execution_agent":
        logger.warning(f"Agent name '{name}' changed to 'code_execution_agent' for consistent transfers")
        name = "code_execution_agent"
        
    # Use provided config or default
    cfg = config or config_manager
    
    # Get the model name (must be a Gemini 2 model)
    model_name = model or cfg.get_main_model()
    if not any(name in model_name.lower() for name in ["gemini-2", "gemini-2.0", "gemini-2.5"]):
        logger.warning(
            f"Model {model_name} may not be compatible with built_in_code_execution tool. "
            "Code Execution tool requires Gemini 2 models."
        )
    
    # Get the instruction
    try:
        instruction = cfg.get_instruction(instruction_name)
    except FileNotFoundError:
        # Use a minimal instruction if the named one isn't found
        logger.warning(
            f"Instruction '{instruction_name}' not found for code execution agent, "
            "using minimal instruction"
        )
        instruction = (
            "You are a code execution agent. You can help users by writing and executing "
            "Python code to perform calculations, data manipulation, or solve problems. "
            "When asked to write code, use the built_in_code_execution tool to run the code "
            "and return the results. Always explain the code you write and its output. "
            "When your task is complete, transfer back to the main agent using "
            "transfer_to_agent(agent_name='beto') or transfer to another agent "
            "if needed using transfer_to_agent(agent_name='agent_name')."
        )
    
    # Import transfer_to_agent
    from google.adk.tools.transfer_to_agent_tool import transfer_to_agent
    
    # Create the code execution agent with both built_in_code_execution and transfer_to_agent tools
    code_agent = Agent(
        name=name,
        model=model_name,
        instruction=instruction,
        description="A specialized agent that can execute Python code securely.",
        tools=[built_in_code_execution, transfer_to_agent]
    )
    
    # Enable code execution explicitly if using Vertex AI
    if cfg.is_using_vertex_ai():
        from google.genai import types
        code_agent.config = types.GenerateContentConfig()
        code_agent.config.tools = [types.Tool(code_execution=types.ToolCodeExecution())]
        logger.info("Explicitly configured code execution tool for Vertex AI")
    
    logger.info(f"Created code execution agent '{name}' with built_in_code_execution tool")
    return code_agent
```

### radbot/web/api/session.py (Simplified Version)
```python
"""
Session management for RadBot web interface.

This module handles session management for the RadBot web interface.
It creates and manages ADK Runner instances directly with the root agent from agent.py.
"""
import asyncio
import logging
import os
import sys
from typing import Dict, Optional, Any, Union
from google.genai.types import Content, Part

from fastapi import Depends

# Set up logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import needed ADK components
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import root_agent directly from agent.py
from agent import root_agent

# Session class that manages Runner
class SessionRunner:
    """Enhanced ADK Runner for web sessions."""
    
    def __init__(self, user_id: str, session_id: str):
        """Initialize a SessionRunner for a specific user.
        
        Args:
            user_id: Unique user identifier
            session_id: Session identifier
        """
        self.user_id = user_id
        self.session_id = session_id
        self.session_service = InMemorySessionService()
        
        # The app_name must match the root agent's name for ADK 0.4.0+
        app_name = root_agent.name if hasattr(root_agent, 'name') else "beto"
        logger.info(f"Using app_name='{app_name}' for session management")
        
        # Create the runner with proper app_name
        self.runner = Runner(
            agent=root_agent,
            app_name=app_name,
            session_service=self.session_service
        )
        
        # Log the agent tree for debugging
        self._log_agent_tree()
    
    def _log_agent_tree(self):
        """Log the agent tree structure for debugging."""
        logger.info("===== AGENT TREE STRUCTURE =====")
        
        # Check root agent
        if hasattr(root_agent, 'name'):
            logger.info(f"ROOT AGENT: name='{root_agent.name}'")
        else:
            logger.warning("ROOT AGENT: No name attribute")
        
        # Check sub-agents
        if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
            sub_agent_names = [sa.name for sa in root_agent.sub_agents if hasattr(sa, 'name')]
            logger.info(f"SUB-AGENTS: {sub_agent_names}")
            
            # Check each sub-agent
            for i, sa in enumerate(root_agent.sub_agents):
                sa_name = sa.name if hasattr(sa, 'name') else f"unnamed-{i}"
                logger.info(f"SUB-AGENT {i}: name='{sa_name}'")
                
                # Check if sub-agent has its own sub-agents
                if hasattr(sa, 'sub_agents') and sa.sub_agents:
                    sa_sub_names = [ssa.name for ssa in sa.sub_agents if hasattr(ssa, 'name')]
                    logger.info(f"  SUB-AGENTS OF '{sa_name}': {sa_sub_names}")
        else:
            logger.warning("ROOT AGENT: No sub_agents found")
        
        logger.info("===============================")
    
    def process_message(self, message: str) -> dict:
        """Process a user message and return the agent's response with event data.
        
        Args:
            message: The user's message text
                
        Returns:
            Dictionary containing the agent's response text and event data
        """
        try:
            # Create Content object with the user's message
            user_message = Content(
                parts=[Part(text=message)],
                role="user"
            )
            
            # Get the app_name from the runner
            app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else "beto"
            
            # Get or create a session with the user_id and session_id
            session = self.session_service.get_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            if not session:
                logger.info(f"Creating new session for user {self.user_id} with app_name='{app_name}'")
                session = self.session_service.create_session(
                    app_name=app_name,
                    user_id=self.user_id,
                    session_id=self.session_id
                )
            
            # Use the runner to process the message
            logger.info(f"Running agent with message: {message[:50]}{'...' if len(message) > 50 else ''}")
            
            # Log key parameters
            logger.info(f"USER_ID: '{self.user_id}'")
            logger.info(f"SESSION_ID: '{self.session_id}'")
            logger.info(f"APP_NAME: '{app_name}'")
            
            # Run with consistent parameters
            events = list(self.runner.run(
                user_id=self.user_id,
                session_id=session.id,
                new_message=user_message
            ))
            
            # Process events
            logger.info(f"Received {len(events)} events from runner")
            
            # Initialize variables for collecting event data
            final_response = None
            processed_events = []
            
            for event in events:
                # Extract event type and create a base event object
                event_type = self._get_event_type(event)
                event_data = {
                    "type": event_type,
                    "timestamp": self._get_current_timestamp()
                }
                
                # Process based on event type
                if event_type == "tool_call":
                    event_data.update(self._process_tool_call_event(event))
                elif event_type == "agent_transfer":
                    event_data.update(self._process_agent_transfer_event(event))
                elif event_type == "planner":
                    event_data.update(self._process_planner_event(event))
                elif event_type == "model_response":
                    event_data.update(self._process_model_response_event(event))
                    # Check if this is the final response
                    if hasattr(event, 'is_final_response') and event.is_final_response():
                        final_response = event_data.get("text", "")
                else:
                    # Generic event processing
                    event_data.update(self._process_generic_event(event))
                
                processed_events.append(event_data)
                
                # Store the event in the events storage
                # Import here to avoid circular imports
                from radbot.web.api.events import add_event
                add_event(self.session_id, event_data)
                
                # If no final response has been found yet, try to extract it
                if final_response is None:
                    final_response = self._extract_response_from_event(event)
            
            if not final_response:
                logger.warning("No text response found in events")
                final_response = "I apologize, but I couldn't generate a response."
            
            # Return both the text response and the processed events
            return {
                "response": final_response,
                "events": processed_events
            }
        
        except Exception as e:
            logger.error(f"Error in process_message: {str(e)}", exc_info=True)
            error_message = f"I apologize, but I encountered an error processing your message. Please try again. Error: {str(e)}"
            return {
                "response": error_message,
                "events": []
            }
    
    def _extract_response_from_event(self, event):
        """Extract response text from various event types."""
        # Method 1: Check if it's a final response
        if hasattr(event, 'is_final_response') and event.is_final_response():
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return part.text
                            
        # Method 2: Check for content directly
        if hasattr(event, 'content'):
            if hasattr(event.content, 'text') and event.content.text:
                return event.content.text
                
        # Method 3: Check for message attribute
        if hasattr(event, 'message'):
            if hasattr(event.message, 'content'):
                return event.message.content
        
        return None
        
    def _get_current_timestamp(self):
        """Get the current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    def _get_event_type(self, event):
        """Determine the type of event."""
        # For tool events in ADK 0.4.0, check for function_call / tool_calls attribute
        if hasattr(event, 'function_call') or hasattr(event, 'tool_calls'):
            return "tool_call"
            
        # Check for tool result event
        if hasattr(event, 'function_response') or hasattr(event, 'tool_results'):
            return "tool_call"
        
        # Try to get type attribute
        if hasattr(event, 'type'):
            return str(event.type)
        
        # Check for tool call events
        if (hasattr(event, 'tool_name') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             'toolName' in event.payload)):
            return "tool_call"
        
        # Check for agent transfer events
        if (hasattr(event, 'to_agent') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             'toAgent' in event.payload)):
            return "agent_transfer"
        
        # Check for planner events
        if (hasattr(event, 'plan') or 
            (hasattr(event, 'payload') and 
             isinstance(event.payload, dict) and 
             ('plan' in event.payload or 'planStep' in event.payload))):
            return "planner"
        
        # Check for model response events
        if hasattr(event, 'is_final_response'):
            return "model_response"
        
        # Check for content which indicates model response (ADK 0.4.0+)
        if hasattr(event, 'content') or hasattr(event, 'message'):
            return "model_response"
        
        # Default category
        return "other"
    
    def _process_tool_call_event(self, event):
        """Process a tool call event."""
        # Implementation details omitted for brevity
        # This would extract tool name, input, and output from the event
        return {"category": "tool_call", "summary": "Tool Call"}
    
    def _process_agent_transfer_event(self, event):
        """Process an agent transfer event."""
        # Implementation details omitted for brevity
        # This would extract to_agent and from_agent information
        return {"category": "agent_transfer", "summary": "Agent Transfer"}
    
    def _process_planner_event(self, event):
        """Process a planner event."""
        # Implementation details omitted for brevity
        # This would extract plan or plan step information
        return {"category": "planner", "summary": "Planner Event"}
    
    def _process_model_response_event(self, event):
        """Process a model response event."""
        # Implementation details omitted for brevity
        # This would extract text content from the response
        return {"category": "model_response", "summary": "Model Response"}
    
    def _process_generic_event(self, event):
        """Process a generic event."""
        # Implementation details omitted for brevity
        # This would provide a basic representation of unknown event types
        return {"category": "other", "summary": "Other Event"}
    
    def reset_session(self):
        """Reset the session conversation history."""
        try:
            # Get the app_name from the runner
            app_name = self.runner.app_name if hasattr(self.runner, 'app_name') else "beto"
            
            # Delete and recreate the session
            self.session_service.delete_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            # Create a new session
            session = self.session_service.create_session(
                app_name=app_name,
                user_id=self.user_id,
                session_id=self.session_id
            )
            
            logger.info(f"Reset session for user {self.user_id}")
            return True
        except Exception as e:
            logger.error(f"Error resetting session: {str(e)}")
            return False

# Singleton session manager
class SessionManager:
    """Manager for web sessions and their associated runners."""
    
    def __init__(self):
        """Initialize session manager."""
        self.sessions: Dict[str, SessionRunner] = {}
        self.lock = asyncio.Lock()
        logger.info("Session manager initialized")
    
    async def get_runner(self, session_id: str) -> Optional[SessionRunner]:
        """Get runner for a session."""
        async with self.lock:
            return self.sessions.get(session_id)
    
    async def set_runner(self, session_id: str, runner: SessionRunner):
        """Set runner for a session."""
        async with self.lock:
            self.sessions[session_id] = runner
            logger.info(f"Runner set for session {session_id}")
    
    async def reset_session(self, session_id: str):
        """Reset a session."""
        runner = await self.get_runner(session_id)
        if runner:
            runner.reset_session()
            logger.info(f"Reset session {session_id}")
        else:
            logger.warning(f"Attempted to reset non-existent session {session_id}")
    
    async def remove_session(self, session_id: str):
        """Remove a session."""
        async with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Removed session {session_id}")
            else:
                logger.warning(f"Attempted to remove non-existent session {session_id}")

# Singleton session manager instance
_session_manager = SessionManager()

# Session manager dependency
def get_session_manager() -> SessionManager:
    """Get the session manager."""
    return _session_manager

# Runner dependency for FastAPI
async def get_or_create_runner_for_session(
    session_id: str, 
    session_manager: SessionManager = Depends(get_session_manager)
) -> SessionRunner:
    """Get or create a SessionRunner for a session."""
    # Check if we already have a runner for this session
    runner = await session_manager.get_runner(session_id)
    if runner:
        logger.info(f"Using existing runner for session {session_id}")
        return runner
    
    # Create a new runner for this session
    logger.info(f"Creating new session runner for session {session_id}")
    
    try:
        # Create user_id from session_id
        user_id = f"web_user_{session_id}"
        
        # Create new runner
        runner = SessionRunner(user_id=user_id, session_id=session_id)
        logger.info(f"Created new SessionRunner for user {user_id}")
        
        # Store the runner in the session manager
        await session_manager.set_runner(session_id, runner)
        
        return runner
    except Exception as e:
        logger.error(f"Error creating session runner: {str(e)}", exc_info=True)
        raise
```

## Testing Plan

1. Create a test script in `/tools/test_agent_transfers.py` to validate transfers between agents.

2. Create an integration test file in `/tests/integration/test_agent_transfers.py`.

3. Test the following scenarios:
   - Agent creation with proper names and tools
   - beto → scout transfers
   - beto → search_agent transfers
   - beto → code_execution_agent transfers
   - scout → beto transfers
   - scout → search_agent transfers
   - scout → code_execution_agent transfers

## Deployment Instructions

1. Implement the changes one file at a time, starting with the agent factory classes.

2. Update the instructions files for the various agents to ensure they know how to use transfer_to_agent.

3. Ensure environment variables are properly set:
   ```
   RADBOT_ENABLE_ADK_SEARCH=true
   RADBOT_ENABLE_ADK_CODE_EXEC=true
   ```

4. Monitor logs after deployment to verify proper agent tree structure.

## Benefits of This Approach

1. **Cleaner Code**: Eliminates monkey patching of ADK internals.

2. **ADK Compatibility**: Uses standard ADK patterns for agent hierarchy.

3. **Proper Agent Naming**: Consistent, predictable agent names for transfers.

4. **Maintainability**: Simpler code that follows ADK's design principles.

5. **Future Compatibility**: Less likely to break with ADK updates.

6. **Debugging**: Better logging and transparency in agent relationships.