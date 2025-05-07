# Memory System

## Overview

RadBot uses a multi-layered semantic memory system built on top of the Qdrant vector database. This enables the agent to remember past conversations, store important information, and retrieve contextually relevant memories based on semantic similarity rather than just keyword matching.

The memory system offers different "resolutions" of memory storage:

1. **Raw Chat (Low Resolution)** - Automatically captured full conversation logs
2. **Memories (Medium Resolution)** - Important collaborative achievements, design discussions, etc.
3. **Important Facts (High Resolution)** - Explicit facts, preferences, key details

## Architecture

### Core Components

1. **QdrantMemoryService** (`memory/qdrant_memory.py`)
   - Custom implementation of ADK's BaseMemoryService interface
   - Manages storage and retrieval of memory data
   - Handles vector database connections and operations

2. **Embedding Service** (`memory/embedding.py`)
   - Converts text into vector embeddings
   - Supports multiple embedding models (Gemini, Sentence-Transformers)
   - Configured dynamically via environment variables

3. **Memory Tools** (`tools/memory/memory_tools.py`)
   - Agent-accessible tools for memory interaction
   - Includes search and storage capabilities
   - Provides structured responses for agent consumption

4. **Enhanced Memory System** (`memory/enhanced_memory/`)
   - MemoryDetector: Monitors for memory trigger keywords
   - EnhancedMemoryManager: Processes and stores memories
   - Custom tagging system for memory organization

### Memory Types

The system supports different memory types:

- `conversation_turn`: A complete exchange (user query + agent response)
- `user_query`: Individual user questions/requests
- `important_information`: Explicitly stored important facts
- `memories`: Medium-resolution collaborative achievements
- `important_fact`: High-resolution explicit facts
- `summary`: Conversation summaries

## Implementation Details

### QdrantMemoryService

The `QdrantMemoryService` class provides persistent memory capabilities by storing conversation data in a Qdrant vector database and enabling semantic search of this data.

```python
class QdrantMemoryService(BaseMemoryService):
    def __init__(
        self,
        collection_name: str = "agent_memory",
        host: Optional[str] = None,
        port: Optional[int] = None,
        url: Optional[str] = None,
        api_key: Optional[str] = None,
        vector_size: Optional[int] = None,
    ):
        # Initialize Qdrant client (local or cloud)
        if url:
            # Connect using URL (for Qdrant Cloud or remote server)
            self.qdrant_client = QdrantClient(
                url=url,
                api_key=api_key
            )
        else:
            # Connect using host/port (for local server)
            self.qdrant_client = QdrantClient(
                host=host or os.getenv("QDRANT_HOST", "localhost"),
                port=port or int(os.getenv("QDRANT_PORT", "6333"))
            )
        
        self.collection_name = collection_name
        
        # Get embedding model info
        self.embedding_model = get_embedding_model()
        self.vector_size = vector_size or self.embedding_model.vector_size
        
        # Initialize collection
        self._initialize_collection()
```

Key methods include:

- `_initialize_collection()`: Sets up Qdrant collection with proper schema
- `process_session()`: Extracts memory points from an ADK session
- `add_memory()`: Adds a memory point to the Qdrant collection
- `search_memories()`: Searches for memories using semantic similarity
- `clear_user_memory()`: Removes a user's memories from the system

### Embedding Service

The embedding service handles the creation and management of text embeddings:

```python
@dataclass
class EmbeddingModel:
    """Data class for embedding model information."""
    name: str
    vector_size: int
    client: Any  # The actual embedding client instance


def get_embedding_model() -> EmbeddingModel:
    """Initialize and return the appropriate embedding model."""
    # Determine which embedding model to use
    embed_model = os.getenv("RADBOT_EMBED_MODEL", "gemini").lower()
    
    if embed_model == "gemini":
        return _initialize_gemini_embedding()
    elif embed_model == "sentence-transformers":
        return _initialize_sentence_transformers()
    else:
        logger.warning(f"Unknown embedding model '{embed_model}', falling back to Gemini")
        return _initialize_gemini_embedding()
```

The `embed_text()` function provides a unified interface for generating embeddings regardless of the underlying model.

### Memory Tools

#### Search Past Conversations

```python
def search_past_conversations(
    query: str,
    max_results: int = 5,
    time_window_days: Optional[int] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Search past conversations for relevant information."""
    # Extract memory service from tool context
    memory_service = getattr(tool_context, "memory_service", None)
    if not memory_service:
        return {"error": "Memory service not available"}
    
    # Extract user ID from tool context
    user_id = getattr(tool_context, "user_id", None)
    if not user_id and hasattr(tool_context, "session"):
        user_id = getattr(tool_context.session, "user_id", None)
    if not user_id:
        return {"error": "User ID not available in tool context"}
    
    # Perform the memory search
    try:
        # Convert time window to timestamp if provided
        from_time = None
        if time_window_days:
            from_time = datetime.now() - timedelta(days=time_window_days)
        
        # Execute the search
        results = memory_service.search_memories(
            query,
            user_id=user_id,
            limit=max_results,
            from_time=from_time
        )
        
        # Format results for agent consumption
        return {
            "success": True,
            "query": query,
            "results_count": len(results),
            "results": [
                {
                    "text": result.text,
                    "timestamp": result.timestamp.isoformat() if hasattr(result, "timestamp") else None,
                    "memory_type": result.memory_type if hasattr(result, "memory_type") else None,
                    "similarity": result.similarity if hasattr(result, "similarity") else None,
                }
                for result in results
            ]
        }
    except Exception as e:
        return {"error": f"Error searching memories: {str(e)}"}
```

#### Store Important Information

```python
def store_important_information(
    information: str,
    memory_type: str = "important_fact",
    metadata: Optional[Dict[str, Any]] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Store important information in memory for future reference."""
    # Extract memory service from tool context
    memory_service = getattr(tool_context, "memory_service", None)
    if not memory_service:
        return {"error": "Memory service not available"}
    
    # Extract user ID from tool context
    user_id = getattr(tool_context, "user_id", None)
    if not user_id and hasattr(tool_context, "session"):
        user_id = getattr(tool_context.session, "user_id", None)
    if not user_id:
        return {"error": "User ID not available in tool context"}
    
    # Store the information in memory
    try:
        memory_service.add_memory(
            text=information,
            user_id=user_id,
            memory_type=memory_type,
            metadata=metadata or {}
        )
        return {
            "success": True,
            "message": f"Successfully stored information as {memory_type}",
            "stored_text": information
        }
    except Exception as e:
        return {"error": f"Error storing information: {str(e)}"}
```

## Enhanced Memory System

The Enhanced Memory System extends the core memory functionality with a multi-layered approach.

### MemoryDetector

The `MemoryDetector` monitors user input for predefined keywords/phrases and custom tags.

```python
class MemoryDetector:
    def __init__(
        self, 
        memory_triggers: Optional[List[str]] = None,
        fact_triggers: Optional[List[str]] = None
    ):
        """Initialize with custom triggers or use defaults."""
        self.memory_triggers = memory_triggers or [
            "we designed", "we built", "our plan for", "achieved together",
            "this setup for", "memory goal:", "let's save this", "memory:",
            "remember this conversation", "save this design", "save our work",
            "store this idea"
        ]
        
        self.fact_triggers = fact_triggers or [
            "important:", "remember this fact:", "my preference is",
            "I always do", "key detail:", "memorize this:", "fact:",
            "never forget:", "critical info:", "note this:", "remember:",
            "store this fact"
        ]
    
    def detect_memory_triggers(self, message: str) -> Dict[str, Any]:
        """
        Detect memory triggers in the message and extract relevant info.
        Returns a dict with detection results.
        """
        result = {
            "detected": False,
            "memory_type": None,
            "text": None,
            "tags": self._extract_tags(message),
            "reference_previous": False
        }
        
        # Check for memory triggers
        for trigger in self.memory_triggers:
            if trigger.lower() in message.lower():
                result["detected"] = True
                result["memory_type"] = "memories"
                result["text"] = self._extract_text(message, trigger)
                result["reference_previous"] = self._check_previous_reference(message)
                return result
        
        # Check for fact triggers
        for trigger in self.fact_triggers:
            if trigger.lower() in message.lower():
                result["detected"] = True
                result["memory_type"] = "important_fact"
                result["text"] = self._extract_text(message, trigger)
                result["reference_previous"] = self._check_previous_reference(message)
                return result
        
        return result
```

### EnhancedMemoryManager

The `EnhancedMemoryManager` processes messages, detects memory triggers, and stores memories.

```python
class EnhancedMemoryManager:
    def __init__(
        self, 
        memory_service: Optional[Any] = None,
        detector: Optional[MemoryDetector] = None
    ):
        """Initialize with memory service and detector."""
        self.memory_service = memory_service
        self.detector = detector or MemoryDetector()
        self.conversation_history = []  # Keep track of recent messages
    
    def process_message(
        self, 
        message: str, 
        user_id: str
    ) -> Dict[str, Any]:
        """
        Process a user message for memory triggers and store if detected.
        Returns info about the detected memory or None if none detected.
        """
        # Add message to conversation history
        self.conversation_history.append(message)
        if len(self.conversation_history) > 10:
            self.conversation_history.pop(0)  # Keep only last 10 messages
        
        # Detect memory triggers
        detection = self.detector.detect_memory_triggers(message)
        
        # If memory trigger detected, store the memory
        if detection["detected"] and detection["text"]:
            # If referring to previous message, use that instead
            if detection["reference_previous"] and len(self.conversation_history) > 1:
                text_to_store = self.conversation_history[-2]
            else:
                text_to_store = detection["text"]
            
            # Store the memory with tags as metadata
            metadata = {"tags": detection["tags"]} if detection["tags"] else {}
            try:
                self.memory_service.add_memory(
                    text=text_to_store,
                    user_id=user_id,
                    memory_type=detection["memory_type"],
                    metadata=metadata
                )
                return {
                    "success": True,
                    "memory_type": detection["memory_type"],
                    "text": text_to_store,
                    "tags": detection["tags"]
                }
            except Exception as e:
                return {"error": f"Failed to store memory: {str(e)}"}
        
        return {"success": False, "message": "No memory triggers detected"}
```

### EnhancedMemoryAgent

The enhanced memory agent integrates the memory detection and storage capabilities into the agent's message processing flow.

## Memory Tiers and Triggers

### Memory Tiers

1. **General Chat (`conversation_turn`, `user_query`)**
   - Automatically captured raw chat
   - Low resolution (full text)
   - No user action needed

2. **Memories (`memory_type="memories"`)**
   - Collaborative achievements, design discussions, etc.
   - Medium resolution (summarized/relevant text)
   - Triggered by specific keywords (e.g., "we designed", "our plan for", "memory goal:")

3. **Important Facts (`memory_type="important_fact"`)**
   - Explicit facts, preferences, key details
   - High resolution (concise text)
   - Triggered by specific keywords (e.g., "important:", "remember this fact:", "key detail:")

### Trigger Keywords

#### For Memories (`memory_type="memories"`)

- "we designed"
- "we built"
- "our plan for"
- "achieved together"
- "this setup for"
- "memory goal:"
- "let's save this"
- "memory:"
- "remember this conversation"
- "save this design"
- "save our work"
- "store this idea"

#### For Important Facts (`memory_type="important_fact"`)

- "important:"
- "remember this fact:"
- "my preference is"
- "I always do"
- "key detail:"
- "memorize this:"
- "fact:"
- "never forget:"
- "critical info:"
- "note this:"
- "remember:"
- "store this fact"

### Custom Tagging

Users can include custom tags in their messages using two formats:

1. Hashtag format: `#beto_tag_name`
2. Mention format: `@beto_tag_name`

These tags are extracted and stored in the memory's metadata, allowing for better organization and retrieval of memories.

## Configuration

### Qdrant Setup

RadBot supports three deployment options for Qdrant:

1. **Local Qdrant Server** (development)
   ```
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   ```

2. **Homelab Qdrant Server** (testing)
   ```
   QDRANT_URL=http://qdrant.service.consul:6333
   ```

3. **Qdrant Cloud** (production)
   ```
   QDRANT_URL=https://your-cluster-url.qdrant.io
   QDRANT_API_KEY=your-qdrant-api-key
   ```

### Collection Structure

The memory system uses a Qdrant collection with the following structure:

- **Vector Space**: Dimension depends on embedding model (typically 768-1536)
- **Distance Metric**: COSINE similarity
- **Indexed Fields**:
  - `user_id` (keyword): For filtering by user
  - `timestamp` (datetime): For time-based filtering
  - `memory_type` (keyword): For filtering by memory type

### Environment Variables

- `QDRANT_HOST`, `QDRANT_PORT`: Local Qdrant connection details
- `QDRANT_URL`, `QDRANT_API_KEY`: Qdrant Cloud connection details
- `RADBOT_EMBED_MODEL`: Embedding model selection ("gemini" or "sentence-transformers")
- `SENTENCE_TRANSFORMERS_MODEL`: Model name for sentence-transformers (if used)

## Usage

### Creating a Memory-Enabled Agent

```python
from radbot.memory.qdrant_memory import QdrantMemoryService
from radbot.agent.memory_agent_factory import create_memory_enabled_agent

# Create an agent with memory capabilities
agent = create_memory_enabled_agent(
    instruction_name="main_agent",
    name="memory_agent"
)

# Process a message with automatic memory handling
response = agent.process_message("user123", "Tell me about the weather")
```

### Creating an Enhanced Memory Agent

```python
from radbot.agent.enhanced_memory_agent_factory import create_enhanced_memory_agent

# Create an enhanced memory agent
agent = create_enhanced_memory_agent(
    name="my_memory_agent",
    instruction_name="main_agent"
)

# Process a message with memory triggers
response = agent.process_message(
    user_id="user123",
    message="important: always use Python 3.10+ for this project #beto_coding"
)
```

### Customizing Memory Triggers

```python
from radbot.agent.enhanced_memory_agent_factory import create_enhanced_memory_agent

# Create agent with custom memory triggers
agent = create_enhanced_memory_agent(
    name="custom_memory_agent",
    memory_manager_config={
        "detector_config": {
            "memory_triggers": ["save this design", "document this"],
            "fact_triggers": ["note down", "critical information"]
        }
    }
)
```

## Memory Workflows

### Conversation Storage

1. User interacts with agent through a session
2. Conversation turns are automatically stored as low-resolution memories
3. Memory triggers in user messages create medium/high-resolution memories
4. Custom tags provide organization for memories

### Memory Retrieval

1. Agent receives a query from user
2. `search_past_conversations` tool is called to find relevant past context
3. Retrieved context is added to the agent's prompt
4. Agent responds with awareness of past interactions

## Testing

Run the unit tests to verify memory system functionality:

```bash
# Test basic memory functionality
pytest tests/unit/test_memory.py

# Test enhanced memory functionality
pytest tests/unit/test_enhanced_memory.py
```

## Future Improvements

Planned enhancements to the memory system:

1. **Memory Management**: Tools for users to delete or edit specific memories
2. **Hierarchical Memory**: Short/medium/long-term memory structures
3. **Memory Consolidation**: Automatic summarization and pruning of older memories
4. **Memory Reflections**: Ability to draw insights from patterns across memories
5. **Multi-User Support**: Enhanced filtering and privacy controls for multi-user scenarios
6. **Memory Ingestion Pipeline**: Support for ingesting external knowledge
7. **Memory Visualization**: User interface for browsing and managing memories
8. **Progressive Memory**: Automated processing of raw conversations into higher-level memories