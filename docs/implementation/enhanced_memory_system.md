# Enhanced Memory System

## Overview

The Enhanced Memory System implements a multi-layered approach to storing and retrieving memories as described in the Memory System Upgrade design document. It provides different "resolutions" of memory:

1. **Raw Chat (Low Resolution)** - Automatically captured full conversation logs (already implemented)
2. **Memories (Medium Resolution)** - Important collaborative achievements, design discussions, etc.
3. **Important Facts (High Resolution)** - Explicit facts, preferences, key details

The system enables manual triggering of higher-resolution memory storage using keywords and custom tags.

## Components

### MemoryDetector

Located in `radbot/memory/enhanced_memory/memory_detector.py`, this component:

- Monitors user input for predefined keywords/phrases
- Detects custom tags with the `beto_` prefix
- Extracts relevant text for storage
- Determines if the memory refers to the current message or previous messages

### EnhancedMemoryManager

Located in `radbot/memory/enhanced_memory/memory_manager.py`, this component:

- Processes user messages through the MemoryDetector
- Maintains conversation history for context
- Handles the storage of memories using the appropriate memory type
- Manages custom tags in memory metadata

### EnhancedMemoryAgent

Located in `radbot/agent/enhanced_memory_agent_factory.py`, this component:

- Extends the base RadBotAgent with enhanced memory capabilities
- Automatically detects and processes memory triggers in user messages
- Stores memories with appropriate memory types and custom tags
- Integrates with the existing memory system

## Memory Tiers

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

## Trigger Keywords

### For Memories (`memory_type="memories"`)

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

### For Important Facts (`memory_type="important_fact"`)

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

## Custom Tagging

Users can include custom tags in their messages using two formats:

1. Hashtag format: `#beto_tag_name`
2. Mention format: `@beto_tag_name`

These tags are extracted and stored in the memory's metadata, allowing for better organization and retrieval of memories.

## Text Extraction Rules

- By default, the information text to be stored is extracted from the user's current message where the keyword was detected
- If the keyword appears at the beginning, only the text after the keyword is stored
- If the user specifies "last message", "previous message", etc., text is extracted from prior turns in the conversation history

## Usage

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
from radbot.memory.enhanced_memory import get_memory_detector
from radbot.memory.enhanced_memory import create_enhanced_memory_manager
from radbot.agent.enhanced_memory_agent_factory import create_enhanced_memory_agent

# Custom memory triggers
custom_memory_triggers = ["save this design", "document this"]
custom_fact_triggers = ["note down", "critical information"]

# Create custom memory detector
detector = get_memory_detector(
    memory_triggers=custom_memory_triggers,
    fact_triggers=custom_fact_triggers
)

# Create memory manager with custom detector
memory_manager = create_enhanced_memory_manager(
    detector_config={
        "memory_triggers": custom_memory_triggers,
        "fact_triggers": custom_fact_triggers
    }
)

# Create agent with custom memory manager
agent = create_enhanced_memory_agent(
    memory_manager_config={
        "detector_config": {
            "memory_triggers": custom_memory_triggers,
            "fact_triggers": custom_fact_triggers
        }
    }
)
```

## Testing

Run the unit tests to verify the enhanced memory system functionality:

```bash
pytest tests/unit/test_enhanced_memory.py
```

## Integration with Existing Memory System

The enhanced memory system builds on top of the existing Qdrant-based memory system:

- Uses the same Qdrant collection (`radbot_memories`)
- Leverages the existing `store_important_information` tool
- Maintains backward compatibility with existing memory types
- Extends functionality with new memory types and custom tagging

## Future Considerations

As noted in the design document, future enhancements may include:

1. Automated processing of `conversation_turn` into `memories` (cron job)
2. Implementing memory pruning or expiry policies
3. Improving keyword detection and text extraction sophistication
4. Potential use of separate Qdrant collections for different memory types
5. Developing a tool to list/manage custom `beto_` tags
