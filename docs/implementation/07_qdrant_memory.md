# Qdrant Memory System Implementation

This document details the implementation of a persistent memory system for the RaderBot agent framework using Qdrant as the vector database.

## Memory System Architecture

The memory system consists of several key components:

1. **QdrantMemoryService**: A custom implementation of ADK's MemoryService interface
2. **Embedding Service**: Handles text vectorization for storage and retrieval
3. **Memory Tools**: Agent tools for searching and managing memory
4. **Memory Ingestion Pipeline**: Process for extracting and storing conversation data

## QdrantMemoryService Implementation

### Qdrant Memory Service (`memory/qdrant_memory.py`)

```python
# raderbot/memory/qdrant_memory.py

"""
Custom memory service implementation using Qdrant as the vector database.
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Union

from dotenv import load_dotenv
import numpy as np
from qdrant_client import QdrantClient, models

from google.adk.sessions import Session
from google.adk.memory import BaseMemoryService
from raderbot.memory.embedding import get_embedding_model, embed_text

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class QdrantMemoryService(BaseMemoryService):
    """
    Memory service implementation using Qdrant as the vector database.
    
    This service implements the ADK BaseMemoryService interface to provide
    persistent memory capabilities for agents.
    """
    
    def __init__(
        self,
        collection_name: str = "agent_memory",
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        vector_size: int = None,  # Will be determined by embedding model
    ):
        """
        Initialize the Qdrant memory service.
        
        Args:
            collection_name: Name of the Qdrant collection to use
            host: Qdrant server host (for local/self-hosted)
            port: Qdrant server port (for local/self-hosted)
            url: Qdrant Cloud URL (for cloud instances)
            api_key: Qdrant Cloud API key (for cloud instances)
            vector_size: Size of embedding vectors (if None, determined from model)
        """
        # Initialize Qdrant client
        if url and api_key:
            # Connect to Qdrant Cloud
            self.client = QdrantClient(url=url, api_key=api_key)
        else:
            # Connect to local/self-hosted Qdrant
            host = host or os.getenv("QDRANT_HOST", "localhost")
            port = port or int(os.getenv("QDRANT_PORT", "6333"))
            self.client = QdrantClient(host=host, port=port)
            
        self.collection_name = collection_name
        
        # Get embedding model info
        self.embedding_model = get_embedding_model()
        self.vector_size = vector_size or self.embedding_model.vector_size
        
        # Initialize collection
        self._initialize_collection()
    
    def _initialize_collection(self):
        """
        Initialize the Qdrant collection if it doesn't exist.
        """
        try:
            # Check if collection exists
            collections = self.client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if self.collection_name not in collection_names:
                # Create the collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.vector_size,
                        distance=models.Distance.COSINE
                    ),
                    # Add payload schema for searchable fields
                    # These fields will have additional indexes to speed up filtering
                    optimizers_config=models.OptimizersConfigDiff(
                        indexing_threshold=10000  # Good balance for medium collections
                    ),
                    # Define the payload schema for indexing key fields
                    # This optimizes filtering performance
                    on_disk_payload=True  # Store payloads on disk to save RAM
                )
                
                # Create payload indexes for common filter fields
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="user_id",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="timestamp",
                    field_schema=models.PayloadSchemaType.DATETIME
                )
                
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="memory_type",
                    field_schema=models.PayloadSchemaType.KEYWORD
                )
                
                logger.info(f"Created Qdrant collection '{self.collection_name}'")
            else:
                logger.info(f"Using existing Qdrant collection '{self.collection_name}'")
        
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant collection: {str(e)}")
            raise
    
    def add_session_to_memory(self, session: Session) -> None:
        """
        Process a session and add its contents to the memory store.
        
        This method extracts key information from a session and stores it in Qdrant.
        
        Args:
            session: The session to process and store
        """
        try:
            # Extract user ID from session
            user_id = session.user_id
            
            # Process session events
            points = []
            
            # Only process sessions with events
            if not session.events:
                logger.info(f"No events found in session {session.id}, skipping memory ingestion")
                return
            
            # Extract conversation turns (user message + agent response pairs)
            current_turn = {"user": None, "agent": None}
            
            for event in session.events:
                # Skip non-text events
                if event.type.name != "TEXT":
                    continue
                    
                role = event.payload.get("author_role")
                text = event.payload.get("text", "")
                
                # Skip empty messages
                if not text.strip():
                    continue
                    
                if role == "user":
                    # If we have a complete previous turn, process it
                    if current_turn["user"] and current_turn["agent"]:
                        turn_point = self._create_memory_point(
                            user_id=user_id,
                            text=f"User: {current_turn['user']}\nAssistant: {current_turn['agent']}",
                            metadata={
                                "memory_type": "conversation_turn",
                                "session_id": session.id,
                                "user_message": current_turn["user"],
                                "agent_response": current_turn["agent"]
                            }
                        )
                        points.append(turn_point)
                        
                    # Start new turn
                    current_turn = {"user": text, "agent": None}
                    
                    # Also store individual user query
                    user_point = self._create_memory_point(
                        user_id=user_id,
                        text=text,
                        metadata={
                            "memory_type": "user_query",
                            "session_id": session.id
                        }
                    )
                    points.append(user_point)
                    
                elif role == "assistant":
                    current_turn["agent"] = text
            
            # Process the final turn if complete
            if current_turn["user"] and current_turn["agent"]:
                turn_point = self._create_memory_point(
                    user_id=user_id,
                    text=f"User: {current_turn['user']}\nAssistant: {current_turn['agent']}",
                    metadata={
                        "memory_type": "conversation_turn",
                        "session_id": session.id,
                        "user_message": current_turn["user"],
                        "agent_response": current_turn["agent"]
                    }
                )
                points.append(turn_point)
            
            # Check if we have points to store
            if not points:
                logger.info(f"No valid text events found in session {session.id}, skipping memory ingestion")
                return
                
            # Store points in Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points,
                wait=True  # Wait for operation to complete
            )
            
            logger.info(f"Successfully added {len(points)} memory points from session {session.id}")
            
        except Exception as e:
            logger.error(f"Error adding session to memory: {str(e)}")
            # In a production system, consider implementing retry logic or fallback
    
    def _create_memory_point(
        self, 
        user_id: str, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> models.PointStruct:
        """
        Create a Qdrant point for memory storage.
        
        Args:
            user_id: User identifier
            text: Text content to store
            metadata: Additional metadata for the memory point
            
        Returns:
            A Qdrant PointStruct ready for insertion
        """
        # Create a unique ID for the point
        point_id = str(uuid.uuid4())
        
        # Generate embedding for the text
        vector = embed_text(text, self.embedding_model)
        
        # Create basic payload
        payload = {
            "user_id": user_id,
            "text": text,
            "timestamp": models.FieldCondition.datetime_now(),  # Current time in ISO format
            "memory_type": metadata.get("memory_type", "general") if metadata else "general"
        }
        
        # Add additional metadata if provided
        if metadata:
            for key, value in metadata.items():
                if key not in payload:  # Avoid overwriting core fields
                    payload[key] = value
        
        # Create and return the point
        return models.PointStruct(
            id=point_id,
            vector=vector,
            payload=payload
        )
    
    def search_memory(
        self,
        app_name: str,
        user_id: str,
        query: str,
        limit: int = 5,
        filter_conditions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the memory store for relevant information.
        
        Args:
            app_name: Name of the application (for multi-app setups)
            user_id: User ID to filter results by
            query: Search query text
            limit: Maximum number of results to return
            filter_conditions: Additional filter conditions for the search
            
        Returns:
            List of relevant memory entries
        """
        try:
            # Generate embedding for the query
            query_vector = embed_text(query, self.embedding_model)
            
            # Create the filter
            must_conditions = [
                models.FieldCondition(
                    key="user_id",
                    match=models.MatchValue(value=user_id)
                )
            ]
            
            # Add additional filter conditions if provided
            if filter_conditions:
                if "memory_type" in filter_conditions:
                    must_conditions.append(
                        models.FieldCondition(
                            key="memory_type",
                            match=models.MatchValue(value=filter_conditions["memory_type"])
                        )
                    )
                
                if "min_timestamp" in filter_conditions:
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp",
                            range=models.Range(
                                gte=filter_conditions["min_timestamp"]
                            )
                        )
                    )
                    
                if "max_timestamp" in filter_conditions:
                    must_conditions.append(
                        models.FieldCondition(
                            key="timestamp",
                            range=models.Range(
                                lte=filter_conditions["max_timestamp"]
                            )
                        )
                    )
            
            search_filter = models.Filter(
                must=must_conditions
            )
            
            # Perform the search
            search_results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,  # We don't need the vectors in the response
            )
            
            # Process the results
            results = []
            for result in search_results:
                # Extract the payload
                payload = result.payload
                
                # Create a result entry with the score
                entry = {
                    "text": payload.get("text", ""),
                    "relevance_score": result.score,
                    "memory_type": payload.get("memory_type", "general"),
                    "timestamp": payload.get("timestamp"),
                }
                
                # Add other payload fields
                for key, value in payload.items():
                    if key not in entry and key != "user_id":  # Skip user_id and already added fields
                        entry[key] = value
                
                results.append(entry)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching memory: {str(e)}")
            return []
    
    def clear_user_memory(self, user_id: str) -> bool:
        """
        Clear all memory entries for a specific user.
        
        Args:
            user_id: The user ID to clear memory for
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create filter for user_id
            user_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=user_id)
                    )
                ]
            )
            
            # Delete points matching the filter
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=models.FilterSelector(
                    filter=user_filter
                ),
                wait=True
            )
            
            logger.info(f"Successfully cleared memory for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user memory: {str(e)}")
            return False
```

## Embedding Service Implementation

### Text Embedding Module (`memory/embedding.py`)

```python
# raderbot/memory/embedding.py

"""
Text embedding utilities for the Qdrant memory system.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class EmbeddingModel:
    """Data class for embedding model information."""
    name: str
    vector_size: int
    client: Any  # The actual embedding client instance


def get_embedding_model() -> EmbeddingModel:
    """
    Initialize and return the appropriate embedding model based on configuration.
    
    This function selects and initializes the embedding model client
    based on environment variables or configuration.
    
    Returns:
        EmbeddingModel: The configured embedding model
    """
    # Determine which embedding model to use based on environment variables
    embed_model = os.getenv("RADERBOT_EMBED_MODEL", "gemini").lower()
    
    if embed_model == "gemini":
        return _initialize_gemini_embedding()
    elif embed_model == "sentence-transformers":
        return _initialize_sentence_transformers()
    else:
        logger.warning(f"Unknown embedding model '{embed_model}', falling back to Gemini")
        return _initialize_gemini_embedding()


def _initialize_gemini_embedding() -> EmbeddingModel:
    """
    Initialize the Gemini embedding model.
    
    Returns:
        EmbeddingModel: The initialized embedding model
    """
    try:
        # Import here to prevent global dependency
        import google.generativeai as genai
        
        # Configure the client with API key
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
        
        # Return the model info
        return EmbeddingModel(
            name="gemini-embedding-001",
            vector_size=768,  # Gemini embeddings are 768-dimensional
            client=genai
        )
    except ImportError:
        logger.error("Failed to import google.generativeai. Please install with: pip install google-generativeai")
        raise


def _initialize_sentence_transformers() -> EmbeddingModel:
    """
    Initialize a sentence-transformers embedding model.
    
    Returns:
        EmbeddingModel: The initialized embedding model
    """
    try:
        # Import here to prevent global dependency
        from sentence_transformers import SentenceTransformer
        
        # Get the model name from environment or use default
        model_name = os.getenv("SENTENCE_TRANSFORMERS_MODEL", "all-MiniLM-L6-v2")
        
        # Load the model
        model = SentenceTransformer(model_name)
        
        # Return the model info
        return EmbeddingModel(
            name=model_name,
            vector_size=model.get_sentence_embedding_dimension(),
            client=model
        )
    except ImportError:
        logger.error("Failed to import sentence_transformers. Please install with: pip install sentence-transformers")
        raise


def embed_text(text: str, model: EmbeddingModel) -> List[float]:
    """
    Generate embedding vector for a text string.
    
    Args:
        text: The text to embed
        model: The embedding model to use
        
    Returns:
        List of embedding vector values
    """
    try:
        if model.name.startswith("gemini"):
            # Gemini embedding
            result = model.client.embed_content(
                model="models/embedding-001",
                content=text,
                task_type="RETRIEVAL_QUERY",
                title="Memory vector"
            )
            return result["embedding"]
        
        elif hasattr(model.client, 'encode'):
            # Sentence Transformers embedding
            embedding = model.client.encode(text)
            return embedding.tolist()
        
        else:
            logger.error(f"Unsupported embedding model: {model.name}")
            raise ValueError(f"Unsupported embedding model: {model.name}")
            
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        # Return a zero vector as fallback (in production, consider a more robust fallback)
        return [0.0] * model.vector_size
```

## Memory Tools Implementation

### Memory Tools (`tools/memory_tools.py`)

```python
# raderbot/tools/memory_tools.py

"""
Memory tools for the RaderBot agent framework.

These tools allow agents to interact with the memory system.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def search_past_conversations(
    query: str,
    max_results: int = 5,
    time_window_days: Optional[int] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Search past conversations for relevant information.
    
    Use this tool when you need to recall previous interactions with the user
    that might be relevant to the current conversation.
    
    Args:
        query: The search query (what to look for in past conversations)
        max_results: Maximum number of results to return (default: 5)
        time_window_days: Optional time window to restrict search (e.g., 7 for last week)
        tool_context: Tool context for accessing memory service
        
    Returns:
        dict: A dictionary containing:
              'status' (str): 'success' or 'error'
              'memories' (list, optional): List of relevant past conversations
              'error_message' (str, optional): Description of the error if failed
    """
    try:
        # Check if tool_context is available (required for memory access)
        if not tool_context:
            return {
                "status": "error",
                "error_message": "Cannot access memory without tool context."
            }
        
        # Get the memory service from tool context
        memory_service = getattr(tool_context, "memory_service", None)
        if not memory_service:
            return {
                "status": "error",
                "error_message": "Memory service not available."
            }
        
        # Get user ID from the tool context
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            return {
                "status": "error",
                "error_message": "User ID not available in tool context."
            }
        
        # Create filter conditions
        filter_conditions = {}
        
        # Add time window if specified
        if time_window_days:
            min_timestamp = (datetime.now() - timedelta(days=time_window_days)).isoformat()
            filter_conditions["min_timestamp"] = min_timestamp
        
        # Search memories
        results = memory_service.search_memory(
            app_name="raderbot",
            user_id=user_id,
            query=query,
            limit=max_results,
            filter_conditions=filter_conditions
        )
        
        # Return formatted results
        if results:
            return {
                "status": "success",
                "memories": results
            }
        else:
            return {
                "status": "success",
                "memories": [],
                "message": "No relevant memories found."
            }
        
    except Exception as e:
        logger.error(f"Error searching past conversations: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to search memory: {str(e)}"
        }


def store_important_information(
    information: str,
    memory_type: str = "important_fact",
    metadata: Optional[Dict[str, Any]] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """
    Store important information in memory for future reference.
    
    Use this tool when the user provides important information that should be
    remembered for future interactions.
    
    Args:
        information: The text information to store
        memory_type: Type of memory (e.g., 'important_fact', 'user_preference')
        metadata: Additional metadata to store with the information
        tool_context: Tool context for accessing memory service
        
    Returns:
        dict: A dictionary with status information
    """
    try:
        # Check if tool_context is available
        if not tool_context:
            return {
                "status": "error",
                "error_message": "Cannot access memory without tool context."
            }
        
        # Get the memory service
        memory_service = getattr(tool_context, "memory_service", None)
        if not memory_service:
            return {
                "status": "error",
                "error_message": "Memory service not available."
            }
        
        # Get user ID
        user_id = getattr(tool_context, "user_id", None)
        if not user_id:
            return {
                "status": "error",
                "error_message": "User ID not available in tool context."
            }
        
        # Create metadata if not provided
        metadata = metadata or {}
        metadata["memory_type"] = memory_type
        
        # Create the memory point
        point = memory_service._create_memory_point(
            user_id=user_id,
            text=information,
            metadata=metadata
        )
        
        # Store in Qdrant
        memory_service.client.upsert(
            collection_name=memory_service.collection_name,
            points=[point],
            wait=True
        )
        
        return {
            "status": "success",
            "message": f"Successfully stored information as {memory_type}."
        }
        
    except Exception as e:
        logger.error(f"Error storing important information: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Failed to store information: {str(e)}"
        }
```

## Package Initialization (`memory/__init__.py`)

```python
# raderbot/memory/__init__.py

"""
Memory system package for the RaderBot agent framework.
"""

from raderbot.memory.qdrant_memory import QdrantMemoryService
from raderbot.memory.embedding import get_embedding_model, embed_text

# Export classes for easy import
__all__ = ['QdrantMemoryService', 'get_embedding_model', 'embed_text']
```

## Integration with Agent Framework

### Runner Configuration with Memory Service

```python
# raderbot/agent_factory.py

"""
Factory functions for creating agents with full capabilities.
"""

import os
from typing import Optional, List, Any

from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import SessionService, InMemorySessionService

from raderbot.agent import RaderBotAgent
from raderbot.memory.qdrant_memory import QdrantMemoryService
from raderbot.tools.memory_tools import search_past_conversations, store_important_information

# Load environment variables
load_dotenv()

def create_memory_enabled_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    memory_service: Optional[QdrantMemoryService] = None,
) -> RaderBotAgent:
    """
    Create an agent with memory capabilities.
    
    Args:
        session_service: Optional session service for conversation state
        tools: Optional list of tools for the agent
        memory_service: Optional custom memory service (creates one if not provided)
        
    Returns:
        A configured RaderBotAgent instance with memory capabilities
    """
    # Create or use provided session service
    session_service = session_service or InMemorySessionService()
    
    # Create or use provided memory service
    if not memory_service:
        # Connect to Qdrant using environment variables
        host = os.getenv("QDRANT_HOST")
        port = os.getenv("QDRANT_PORT")
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        
        memory_service = QdrantMemoryService(
            host=host,
            port=int(port) if port else None,
            url=url,
            api_key=api_key
        )
    
    # Ensure memory tools are included
    memory_tools = [search_past_conversations, store_important_information]
    all_tools = (tools or []) + memory_tools
    
    # Create the agent
    agent = RaderBotAgent(
        session_service=session_service,
        tools=all_tools
    )
    
    # Configure the runner with memory service
    agent.runner = Runner(
        agent=agent.root_agent,
        app_name="raderbot",
        session_service=session_service,
        memory_service=memory_service
    )
    
    return agent
```

## Memory Ingestion Pipeline

```python
# raderbot/memory/ingestion.py

"""
Memory ingestion pipeline for the RaderBot agent framework.

This module provides utilities for processing and ingesting session data into memory.
"""

import logging
import time
from typing import List, Optional
from threading import Thread, Event

from google.adk.sessions import Session, SessionService

from raderbot.memory.qdrant_memory import QdrantMemoryService

logger = logging.getLogger(__name__)

class MemoryIngestionService:
    """
    Service for ingesting session data into memory.
    
    This service can run as a background process to periodically ingest
    completed sessions into the memory system.
    """
    
    def __init__(
        self,
        session_service: SessionService,
        memory_service: QdrantMemoryService,
        interval_seconds: int = 300,  # Default: ingest every 5 minutes
    ):
        """
        Initialize the memory ingestion service.
        
        Args:
            session_service: The session service to get sessions from
            memory_service: The memory service to store data in
            interval_seconds: Time between ingestion runs in seconds
        """
        self.session_service = session_service
        self.memory_service = memory_service
        self.interval_seconds = interval_seconds
        self.stop_event = Event()
        self.ingestion_thread = None
        self.processed_sessions = set()  # Track already processed sessions
    
    def start(self):
        """Start the background ingestion thread."""
        if self.ingestion_thread and self.ingestion_thread.is_alive():
            logger.warning("Memory ingestion thread is already running")
            return
            
        self.stop_event.clear()
        self.ingestion_thread = Thread(target=self._ingestion_loop, daemon=True)
        self.ingestion_thread.start()
        logger.info("Started memory ingestion service")
    
    def stop(self):
        """Stop the background ingestion thread."""
        if not self.ingestion_thread or not self.ingestion_thread.is_alive():
            return
            
        self.stop_event.set()
        self.ingestion_thread.join(timeout=5.0)
        
        if self.ingestion_thread.is_alive():
            logger.warning("Memory ingestion thread did not terminate cleanly")
        else:
            logger.info("Stopped memory ingestion service")
    
    def _ingestion_loop(self):
        """Background loop for periodic memory ingestion."""
        while not self.stop_event.is_set():
            try:
                self.ingest_recent_sessions()
            except Exception as e:
                logger.error(f"Error in memory ingestion loop: {str(e)}")
                
            # Wait for the next run or until stop is requested
            self.stop_event.wait(self.interval_seconds)
    
    def ingest_recent_sessions(self, max_sessions: int = 50) -> int:
        """
        Ingest recent sessions into memory.
        
        Args:
            max_sessions: Maximum number of sessions to process in one batch
            
        Returns:
            Number of sessions processed
        """
        # Get list of sessions
        # Note: This is a simplified approach. The actual implementation
        # would depend on the SessionService API for retrieving sessions.
        try:
            # Placeholder for getting recent sessions
            # In a real implementation, this would call an API on the session service
            # to get recently completed or modified sessions
            recent_sessions = []  # self.session_service.get_recent_sessions(limit=max_sessions)
            
            if not recent_sessions:
                logger.debug("No new sessions found to ingest")
                return 0
                
            count = 0
            for session in recent_sessions:
                # Skip already processed sessions
                if session.id in self.processed_sessions:
                    continue
                    
                # Skip empty sessions
                if not session.events:
                    continue
                    
                # Ingest the session
                try:
                    self.memory_service.add_session_to_memory(session)
                    self.processed_sessions.add(session.id)
                    count += 1
                except Exception as e:
                    logger.error(f"Error ingesting session {session.id}: {str(e)}")
            
            logger.info(f"Processed {count} new sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error retrieving sessions for ingestion: {str(e)}")
            return 0
    
    def ingest_single_session(self, session: Session) -> bool:
        """
        Ingest a single session into memory.
        
        Args:
            session: The session to ingest
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Skip if already processed
            if session.id in self.processed_sessions:
                logger.debug(f"Session {session.id} already processed, skipping")
                return True
                
            # Skip empty sessions
            if not session.events:
                logger.debug(f"Session {session.id} has no events, skipping")
                return True
                
            # Ingest the session
            self.memory_service.add_session_to_memory(session)
            self.processed_sessions.add(session.id)
            logger.info(f"Successfully ingested session {session.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting session {session.id}: {str(e)}")
            return False
```

## Next Steps

With the Qdrant memory system implemented, the next steps are:

1. Set up MCP integration for Home Assistant
2. Create documentation for implementation
3. Write tests for the framework