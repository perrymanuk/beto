# Memory System Implementation

This document details the implementation of the memory system for the radbot agent framework, focusing on the integration with Qdrant as the vector database and the creation of memory tools for agents.

## Overview

The memory system consists of several key components:

1. **QdrantMemoryService**: Custom implementation of ADK's BaseMemoryService interface
2. **Embedding Service**: Handles text vectorization for storage and retrieval
3. **Memory Tools**: Agent tools for searching and managing memory
4. **Memory Agent Factory**: Creates agents with memory capabilities

## QdrantMemoryService

The `QdrantMemoryService` class provides persistent memory capabilities by storing conversation data in a Qdrant vector database and enabling semantic search of this data.

### Key Features

- **Flexible Connection**: Supports both local/self-hosted Qdrant instances and Qdrant Cloud
- **Collection Management**: Automatically creates and configures collections with appropriate indexes
- **Session Processing**: Extracts and stores conversation turns from ADK sessions
- **Semantic Search**: Searches for memories based on semantic similarity and filters
- **User Memory Management**: Provides the ability to clear a user's memory

### Implementation Highlights

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
        # ...
        
        # Get embedding model info
        self.embedding_model = get_embedding_model()
        self.vector_size = vector_size or self.embedding_model.vector_size
        
        # Initialize collection
        self._initialize_collection()
```

The service creates two types of memory entries from user-agent interactions:
1. **User Queries**: Individual user messages for direct retrieval
2. **Conversation Turns**: Complete user-agent exchanges for contextual retrieval

## Embedding Service

The embedding service component handles the creation and management of text embeddings, which are essential for the vector-based memory system.

### Features

- **Model Selection**: Supports multiple embedding models (Gemini, Sentence-Transformers)
- **Dynamic Configuration**: Model selection via environment variables
- **Error Handling**: Graceful fallbacks for embedding failures

### Implementation

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
    embed_model = os.getenv("radbot_EMBED_MODEL", "gemini").lower()
    
    if embed_model == "gemini":
        return _initialize_gemini_embedding()
    elif embed_model == "sentence-transformers":
        return _initialize_sentence_transformers()
    else:
        logger.warning(f"Unknown embedding model '{embed_model}', falling back to Gemini")
        return _initialize_gemini_embedding()
```

The `embed_text` function provides a unified interface for generating embeddings regardless of the underlying model:

```python
def embed_text(text: str, model: EmbeddingModel) -> List[float]:
    """Generate embedding vector for a text string."""
    # Model-specific embedding logic
    # ...
```

## Memory Tools

The memory tools provide agent-accessible interfaces to interact with the memory system through the ADK tools mechanism.

### Search Past Conversations

This tool allows the agent to search for relevant information from past conversations:

```python
def search_past_conversations(
    query: str,
    max_results: int = 5,
    time_window_days: Optional[int] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Search past conversations for relevant information."""
    # Implementation details
    # ...
```

The agent can provide a query and additional parameters to find relevant past interactions, with results returned in a structured format.

### Store Important Information

This tool enables the agent to explicitly store important information in memory:

```python
def store_important_information(
    information: str,
    memory_type: str = "important_fact",
    metadata: Optional[Dict[str, Any]] = None,
    tool_context: Optional[ToolContext] = None
) -> Dict[str, Any]:
    """Store important information in memory for future reference."""
    # Implementation details
    # ...
```

This is particularly useful for saving user preferences, important facts, or other information that should be easily retrievable later.

## Memory-Enabled Agent Factory

The `create_memory_enabled_agent` function provides a convenient way to create agents with memory capabilities:

```python
def create_memory_enabled_agent(
    session_service: Optional[SessionService] = None,
    tools: Optional[List[Any]] = None,
    memory_service: Optional[QdrantMemoryService] = None,
    instruction_name: str = "main_agent",
    name: str = "memory_enabled_agent",
) -> radbotAgent:
    """Create an agent with memory capabilities."""
    # Implementation details
    # ...
```

This factory function:
1. Creates or uses a provided QdrantMemoryService
2. Adds memory tools to the agent's tool list
3. Configures the ADK Runner with the memory service
4. Returns a fully configured radbotAgent with memory capabilities

## Memory Access Pattern

The memory system follows a specific pattern for accessing the memory service from tools:

1. Memory service is injected into the Runner at creation time
2. Tools access the memory service via `tool_context.memory_service`
3. User ID is obtained from `tool_context.user_id` or `tool_context.session.user_id`

This approach ensures that memory access is properly scoped to the current user and session context.

## Error Handling

The memory implementation includes comprehensive error handling:

1. **Connection Errors**: Graceful handling of Qdrant connection issues
2. **Missing Dependencies**: Clear error messages for missing libraries
3. **Tool Context Issues**: Proper validation of tool_context and required attributes
4. **Embedding Failures**: Fallback mechanisms for embedding generation errors

This ensures that memory-related issues don't crash the agent system and provides meaningful feedback when problems occur.

## Configuration Options

The memory system can be configured through environment variables:

- `QDRANT_HOST`, `QDRANT_PORT`: Local Qdrant connection details
- `QDRANT_URL`, `QDRANT_API_KEY`: Qdrant Cloud connection details
- `radbot_EMBED_MODEL`: Embedding model selection
- `SENTENCE_TRANSFORMERS_MODEL`: Model name for sentence-transformers (if used)

This allows for flexible deployment in different environments without code changes.

## Usage Example

```python
# Create a memory-enabled agent
agent = create_memory_enabled_agent(
    tools=[get_current_time, get_weather],
    name="memory_agent",
    instruction_name="main_agent"
)

# Process message with memory capabilities
response = agent.process_message(user_id, "What did we talk about yesterday?")
```

## Next Steps

With the memory system implemented, the next steps could include:

1. Implementing advanced memory ingestion/filtering strategies
2. Creating a background memory ingestion service
3. Adding memory visualization or inspection tools
4. Implementing memory summarization techniques