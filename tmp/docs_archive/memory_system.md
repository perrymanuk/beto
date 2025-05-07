# Memory System

## Overview

radbot uses a semantic memory system built on top of the Qdrant vector database. This enables the agent to remember past conversations, store important information, and retrieve contextually relevant memories based on semantic similarity rather than just keyword matching.

## Components

### QdrantMemoryService (`memory/qdrant_memory.py`)

The primary component responsible for storing and retrieving memories from the Qdrant vector database.

#### Key Features:

- **Persistent Storage**: Memories persist across sessions and restarts
- **Vector Search**: Semantic search using embedding vectors
- **Filtered Retrieval**: Ability to filter memories by user, type, and timestamp
- **Memory Types**: Support for different memory types (conversation, user queries, etc.)
- **Flexible Configuration**: Support for local Qdrant, homelab, or Qdrant Cloud

### Embedding Service (`memory/embedding.py`)

Handles the creation of vector embeddings for text.

#### Key Features:

- **Text Embedding**: Converts text into vector representations
- **Model Management**: Handles loading and configuring embedding models
- **Caching**: Optional caching of embedding results for efficiency

### Memory Tools (`tools/memory_tools.py`)

Agent tools for interacting with the memory system.

#### Key Tools:

- `search_memory`: Search for relevant past conversations
- `store_important_information`: Store specific information for later retrieval
- `summarize_conversation`: Create a summary of the current conversation

## Configuration

### Qdrant Setup

radbot supports three deployment options for Qdrant:

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

### Memory Types

The system supports different memory types:

- `conversation_turn`: A complete exchange (user query + agent response)
- `user_query`: Individual user questions/requests
- `important_information`: Explicitly stored important facts
- `summary`: Conversation summaries

## Usage

### Creating a Memory-Enabled Agent

```python
from radbot.memory.qdrant_memory import QdrantMemoryService
from radbot.agent.agent import AgentFactory
from radbot.tools.memory_tools import get_memory_tools

# Create memory service
memory_service = QdrantMemoryService(
    collection_name="agent_memory",
    # Connect to homelab Qdrant
    url="http://qdrant.service.consul:6333"
)

# Get memory tools
memory_tools = get_memory_tools(memory_service)

# Create agent with memory
agent = AgentFactory.create_memory_enabled_agent(
    memory_service=memory_service,
    memory_tools=memory_tools
)
```

### Memory Workflows

#### Conversation Storage

1. User interacts with agent through a session
2. When session ends or at regular intervals, `add_session_to_memory` is called
3. Session is processed into individual memory points
4. Memory points are stored in Qdrant with embeddings

#### Memory Retrieval

1. Agent receives a query from user
2. `search_memory` tool is called to find relevant past context
3. Retrieved context is added to the agent's prompt
4. Agent responds with awareness of past interactions

## Future Improvements

Planned enhancements to the memory system:

1. **Memory Management**: Tools for users to delete or edit specific memories
2. **Hierarchical Memory**: Short/medium/long-term memory structures
3. **Memory Consolidation**: Automatic summarization and pruning of older memories
4. **Memory Reflections**: Ability to draw insights from patterns across memories
5. **Multi-User Support**: Enhanced filtering and privacy controls for multi-user scenarios
6. **Memory Ingestion Pipeline**: Support for ingesting external knowledge