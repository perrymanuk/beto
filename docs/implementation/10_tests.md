# Testing Framework for RaderBot

This document details the testing strategy and implementation for the RaderBot agent framework.

## Testing Strategy

The testing approach for RaderBot follows a comprehensive strategy that includes:

1. **Unit Tests**: Testing individual components in isolation
2. **Integration Tests**: Testing interactions between components
3. **Mocked Tests**: Using mocks for external dependencies
4. **End-to-End Tests**: Testing the complete agent workflow
5. **ADK Evaluation Tests**: Using ADK's built-in evaluation framework

## Directory Structure

The tests are organized in a structured directory hierarchy:

```
tests/
├── unit/
│   ├── test_agent.py         # Tests for the agent module
│   ├── test_config.py        # Tests for the configuration system
│   ├── test_tools.py         # Tests for basic tools
│   └── test_memory.py        # Tests for the memory system
├── integration/
│   ├── test_agent_tools.py   # Tests for agent and tool integration
│   ├── test_agent_memory.py  # Tests for agent and memory integration
│   └── test_memory_tools.py  # Tests for memory tools
├── mocks/
│   ├── mock_qdrant.py        # Mock implementation of Qdrant
│   ├── mock_mcp_server.py    # Mock implementation of MCP server
│   └── mock_llm.py           # Mock implementation of LLM
├── fixtures/
│   ├── test_sessions/        # Session data for tests
│   ├── test_prompts/         # Test prompt configurations
│   └── test_vectors/         # Test vector data
└── e2e/
    └── test_workflows.py     # End-to-end workflow tests
```

## Unit Tests Implementation

### Agent Unit Tests (`tests/unit/test_agent.py`)

```python
# tests/unit/test_agent.py

"""
Unit tests for the agent module.
"""

import unittest
from unittest.mock import MagicMock, patch

from google.adk.agents import Agent
from google.adk.runners import Runner

from raderbot.agent import RaderBotAgent, create_agent


class TestRaderBotAgent(unittest.TestCase):
    """Unit tests for the RaderBotAgent class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock dependencies
        self.mock_session_service = MagicMock()
        self.mock_root_agent = MagicMock()
        self.mock_runner = MagicMock()
        
        # Create patches
        self.agent_patch = patch('raderbot.agent.Agent', return_value=self.mock_root_agent)
        self.runner_patch = patch('raderbot.agent.Runner', return_value=self.mock_runner)
        
        # Start patches
        self.mock_agent = self.agent_patch.start()
        self.mock_runner_class = self.runner_patch.start()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.agent_patch.stop()
        self.runner_patch.stop()
    
    def test_init(self):
        """Test agent initialization."""
        # Create agent
        agent = RaderBotAgent(
            session_service=self.mock_session_service,
            tools=["mock_tool"]
        )
        
        # Verify agent initialization
        self.mock_agent.assert_called_once()
        self.mock_runner_class.assert_called_once_with(
            agent=self.mock_root_agent,
            app_name="raderbot",
            session_service=self.mock_session_service
        )
        
        # Verify agent properties
        self.assertEqual(agent.root_agent, self.mock_root_agent)
        self.assertEqual(agent.runner, self.mock_runner)
    
    def test_add_tool(self):
        """Test adding a tool to the agent."""
        # Create agent
        agent = RaderBotAgent(session_service=self.mock_session_service)
        
        # Mock agent tools
        self.mock_root_agent.tools = []
        
        # Add a tool
        mock_tool = MagicMock()
        agent.add_tool(mock_tool)
        
        # Verify tool was added
        self.mock_root_agent.tools = [mock_tool]
    
    def test_add_tools(self):
        """Test adding multiple tools to the agent."""
        # Create agent
        agent = RaderBotAgent(session_service=self.mock_session_service)
        
        # Mock agent tools
        self.mock_root_agent.tools = []
        
        # Add multiple tools
        mock_tools = [MagicMock(), MagicMock()]
        agent.add_tools(mock_tools)
        
        # Verify tools were added
        self.mock_root_agent.tools = mock_tools
    
    def test_process_message(self):
        """Test processing a user message."""
        # Create agent
        agent = RaderBotAgent(session_service=self.mock_session_service)
        
        # Mock runner response
        mock_event1 = MagicMock()
        mock_event1.type.name = "TEXT"
        mock_event1.payload = {"author_role": "assistant", "text": "Mock response"}
        
        mock_event2 = MagicMock()
        mock_event2.type.name = "OTHER"
        
        self.mock_runner.run_async.return_value = [mock_event2, mock_event1]
        
        # Process a message
        response = agent.process_message("user123", "Hello")
        
        # Verify runner was called
        self.mock_runner.run_async.assert_called_once_with(user_id="user123", message="Hello")
        
        # Verify response
        self.assertEqual(response, "Mock response")
    
    def test_process_message_no_response(self):
        """Test processing a message with no text response."""
        # Create agent
        agent = RaderBotAgent(session_service=self.mock_session_service)
        
        # Mock runner response with no text event
        mock_event = MagicMock()
        mock_event.type.name = "OTHER"
        
        self.mock_runner.run_async.return_value = [mock_event]
        
        # Process a message
        response = agent.process_message("user123", "Hello")
        
        # Verify fallback response
        self.assertIn("apologize", response.lower())
    
    def test_add_sub_agent(self):
        """Test adding a sub-agent to the main agent."""
        # Create agent
        agent = RaderBotAgent(session_service=self.mock_session_service)
        
        # Mock agent sub_agents
        self.mock_root_agent.sub_agents = []
        
        # Add a sub-agent
        mock_sub_agent = MagicMock()
        agent.add_sub_agent(mock_sub_agent)
        
        # Verify sub-agent was added
        self.mock_root_agent.sub_agents = [mock_sub_agent]


class TestCreateAgent(unittest.TestCase):
    """Unit tests for the create_agent factory function."""
    
    @patch('raderbot.agent.RaderBotAgent')
    @patch('raderbot.agent.config_manager')
    def test_create_agent(self, mock_config_manager, mock_raderbot_agent):
        """Test creating an agent with the factory function."""
        # Mock config manager
        mock_config_manager.get_main_model.return_value = "mock-model"
        mock_config_manager.get_instruction.return_value = "Mock instruction"
        
        # Mock session service and tools
        mock_session_service = MagicMock()
        mock_tools = [MagicMock()]
        
        # Create agent
        agent = create_agent(
            session_service=mock_session_service,
            tools=mock_tools,
            model="custom-model",
            instruction_name="custom_instruction"
        )
        
        # Verify config manager was called
        mock_config_manager.get_instruction.assert_called_once_with("custom_instruction")
        
        # Verify agent was created with correct parameters
        mock_raderbot_agent.assert_called_once_with(
            session_service=mock_session_service,
            tools=mock_tools,
            model="custom-model",
            instruction=mock_config_manager.get_instruction.return_value
        )
        
        # Verify the returned agent
        self.assertEqual(agent, mock_raderbot_agent.return_value)
```

### Tool Unit Tests (`tests/unit/test_tools.py`)

```python
# tests/unit/test_tools.py

"""
Unit tests for the basic tools.
"""

import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

from raderbot.tools.basic_tools import get_current_time, get_weather


class TestTimeTool(unittest.TestCase):
    """Unit tests for the time tool."""
    
    @patch('raderbot.tools.basic_tools.ZoneInfo')
    @patch('raderbot.tools.basic_tools.datetime')
    def test_get_time_success(self, mock_datetime, mock_zoneinfo):
        """Test getting the current time successfully."""
        # Mock datetime
        mock_now = MagicMock()
        mock_now.strftime.return_value = "2023-01-01 12:00:00 UTC+0000"
        mock_datetime.datetime.now.return_value = mock_now
        
        # Mock tool context
        mock_context = MagicMock()
        mock_context.state = {}
        
        # Call the tool
        result = get_current_time("London", mock_context)
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("London", result["report"])
        self.assertIn("12:00:00", result["report"])
        
        # Verify state update
        self.assertEqual(mock_context.state["last_time_city"], "London")
    
    def test_get_time_unknown_city(self):
        """Test getting time for an unknown city."""
        # Call the tool with unknown city
        result = get_current_time("UnknownCity")
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertIn("UnknownCity", result["error_message"])
    
    @patch('raderbot.tools.basic_tools.ZoneInfo')
    def test_get_time_exception(self, mock_zoneinfo):
        """Test handling exceptions in the time tool."""
        # Mock ZoneInfo to raise exception
        mock_zoneinfo.side_effect = Exception("Mock error")
        
        # Call the tool
        result = get_current_time("London")
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertIn("error", result["error_message"].lower())


class TestWeatherTool(unittest.TestCase):
    """Unit tests for the weather tool."""
    
    def test_get_weather_success(self):
        """Test getting weather successfully."""
        # Mock tool context
        mock_context = MagicMock()
        mock_context.state = {}
        
        # Call the tool
        result = get_weather("London", mock_context)
        
        # Verify the result
        self.assertEqual(result["status"], "success")
        self.assertIn("London", result["report"])
        self.assertIn("cloudy", result["report"].lower())
        
        # Verify state update
        self.assertEqual(mock_context.state["last_weather_city"], "London")
    
    def test_get_weather_unknown_city(self):
        """Test getting weather for an unknown city."""
        # Call the tool with unknown city
        result = get_weather("UnknownCity")
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertIn("UnknownCity", result["error_message"])
    
    @patch('raderbot.tools.basic_tools.mock_weather', {})
    def test_get_weather_empty_data(self):
        """Test weather tool with empty mock data."""
        # Call the tool
        result = get_weather("London")
        
        # Verify the result
        self.assertEqual(result["status"], "error")
        self.assertIn("not available", result["error_message"].lower())
```

### Memory Unit Tests (`tests/unit/test_memory.py`)

```python
# tests/unit/test_memory.py

"""
Unit tests for the memory system.
"""

import unittest
from unittest.mock import MagicMock, patch
import uuid

from raderbot.memory.qdrant_memory import QdrantMemoryService
from raderbot.memory.embedding import EmbeddingModel, embed_text


class TestQdrantMemoryService(unittest.TestCase):
    """Unit tests for the QdrantMemoryService class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Qdrant client
        self.mock_client = MagicMock()
        
        # Create patches
        self.client_patch = patch('raderbot.memory.qdrant_memory.QdrantClient', return_value=self.mock_client)
        self.embed_patch = patch('raderbot.memory.qdrant_memory.embed_text')
        
        # Start patches
        self.mock_client_class = self.client_patch.start()
        self.mock_embed = self.embed_patch.start()
        
        # Mock embedding model
        self.mock_model = MagicMock()
        self.mock_model.vector_size = 768
        
        # Mock get_embedding_model
        self.model_patch = patch('raderbot.memory.qdrant_memory.get_embedding_model', return_value=self.mock_model)
        self.mock_get_model = self.model_patch.start()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.client_patch.stop()
        self.embed_patch.stop()
        self.model_patch.stop()
    
    def test_init_local(self):
        """Test initialization with local Qdrant."""
        # Create memory service
        service = QdrantMemoryService(
            host="localhost",
            port=6333
        )
        
        # Verify client initialization
        self.mock_client_class.assert_called_once_with(host="localhost", port=6333)
        
        # Verify collection initialization
        self.mock_client.get_collections.assert_called_once()
    
    def test_init_cloud(self):
        """Test initialization with Qdrant Cloud."""
        # Create memory service
        service = QdrantMemoryService(
            url="https://example.qdrant.cloud",
            api_key="mock-key"
        )
        
        # Verify client initialization
        self.mock_client_class.assert_called_once_with(url="https://example.qdrant.cloud", api_key="mock-key")
        
        # Verify collection initialization
        self.mock_client.get_collections.assert_called_once()
    
    def test_create_memory_point(self):
        """Test creating a memory point."""
        # Create memory service
        service = QdrantMemoryService()
        
        # Set up mock embedding
        self.mock_embed.return_value = [0.1] * 768
        
        # Call _create_memory_point
        result = service._create_memory_point(
            user_id="user123",
            text="Test memory",
            metadata={"memory_type": "test"}
        )
        
        # Verify embedding was generated
        self.mock_embed.assert_called_once_with("Test memory", self.mock_model)
        
        # Verify result structure
        self.assertEqual(result.vector, self.mock_embed.return_value)
        self.assertEqual(result.payload["user_id"], "user123")
        self.assertEqual(result.payload["text"], "Test memory")
        self.assertEqual(result.payload["memory_type"], "test")
    
    @patch('raderbot.memory.qdrant_memory.uuid.uuid4')
    def test_search_memory(self, mock_uuid):
        """Test searching memory."""
        # Set up mock UUID
        mock_uuid.return_value = uuid.UUID('12345678-1234-5678-1234-567812345678')
        
        # Create memory service
        service = QdrantMemoryService()
        
        # Set up mock embedding
        self.mock_embed.return_value = [0.1] * 768
        
        # Set up mock search results
        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.payload = {
            "text": "Test memory",
            "memory_type": "conversation_turn",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        self.mock_client.search.return_value = [mock_result]
        
        # Call search_memory
        results = service.search_memory(
            app_name="raderbot",
            user_id="user123",
            query="Test query",
            limit=5
        )
        
        # Verify embedding was generated
        self.mock_embed.assert_called_once_with("Test query", self.mock_model)
        
        # Verify search was called
        self.mock_client.search.assert_called_once()
        
        # Verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["text"], "Test memory")
        self.assertEqual(results[0]["relevance_score"], 0.95)
        self.assertEqual(results[0]["memory_type"], "conversation_turn")
```

## Integration Tests Implementation

### Agent-Memory Integration Tests (`tests/integration/test_agent_memory.py`)

```python
# tests/integration/test_agent_memory.py

"""
Integration tests for agent and memory integration.
"""

import unittest
from unittest.mock import MagicMock, patch
import tempfile
import os

from raderbot.agent_factory import create_memory_enabled_agent
from raderbot.memory.qdrant_memory import QdrantMemoryService
from raderbot.tools.memory_tools import search_past_conversations


class TestAgentMemoryIntegration(unittest.TestCase):
    """Integration tests for agent and memory integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for test collection
        self.temp_dir = tempfile.TemporaryDirectory()
        
        # Create patches
        self.qdrant_client_patch = patch('raderbot.memory.qdrant_memory.QdrantClient')
        
        # Start patches
        self.mock_qdrant_client = self.qdrant_client_patch.start()
        
        # Mock collection methods
        self.mock_client = MagicMock()
        self.mock_qdrant_client.return_value = self.mock_client
        
        # Mock collections
        mock_collections = MagicMock()
        mock_collections.collections = []
        self.mock_client.get_collections.return_value = mock_collections
        
        # Mock search results
        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.payload = {
            "text": "User: What is the weather?\nAssistant: It's sunny today.",
            "memory_type": "conversation_turn",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        self.mock_client.search.return_value = [mock_result]
        
        # Mock embedding
        self.embed_patch = patch('raderbot.memory.embedding.embed_text', return_value=[0.1] * 768)
        self.mock_embed = self.embed_patch.start()
        
        # Mock embedding model
        self.model_patch = patch('raderbot.memory.embedding.get_embedding_model')
        self.mock_get_model = self.model_patch.start()
        
        mock_model = MagicMock()
        mock_model.vector_size = 768
        self.mock_get_model.return_value = mock_model
        
        # Mock runner
        self.runner_patch = patch('google.adk.runners.Runner')
        self.mock_runner = self.runner_patch.start()
        
        # Mock session service
        self.session_service_patch = patch('google.adk.sessions.InMemorySessionService')
        self.mock_session_service = self.session_service_patch.start()
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.qdrant_client_patch.stop()
        self.embed_patch.stop()
        self.model_patch.stop()
        self.runner_patch.stop()
        self.session_service_patch.stop()
        
        # Clean up temporary directory
        self.temp_dir.cleanup()
    
    def test_create_memory_enabled_agent(self):
        """Test creating an agent with memory capabilities."""
        # Create memory-enabled agent
        agent = create_memory_enabled_agent()
        
        # Verify memory service was initialized
        self.assertTrue(hasattr(agent, "runner"))
        
        # Check if runner was initialized with memory service
        self.mock_runner.assert_called_once()
        kwargs = self.mock_runner.call_args.kwargs
        self.assertIn("memory_service", kwargs)
        
        # Verify the agent has memory tools
        has_memory_tools = False
        for tool in agent.root_agent.tools:
            if tool.__name__ == "search_past_conversations":
                has_memory_tools = True
                break
        self.assertTrue(has_memory_tools)
    
    def test_search_past_conversations_tool(self):
        """Test the search_past_conversations tool."""
        # Create mock tool context with memory service
        mock_context = MagicMock()
        mock_context.memory_service = QdrantMemoryService()
        mock_context.user_id = "user123"
        
        # Call search_past_conversations
        result = search_past_conversations(
            query="Weather",
            max_results=5,
            tool_context=mock_context
        )
        
        # Verify embedding was created
        self.mock_embed.assert_called_once()
        
        # Verify search was performed
        self.mock_client.search.assert_called_once()
        
        # Verify result
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["memories"]), 1)
        self.assertIn("weather", result["memories"][0]["text"].lower())
```

## Mock Implementations

### Mock Qdrant Client (`tests/mocks/mock_qdrant.py`)

```python
# tests/mocks/mock_qdrant.py

"""
Mock implementation of Qdrant client for testing.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
import uuid


@dataclass
class MockVector:
    """Mock vector for Qdrant points."""
    values: List[float]
    name: Optional[str] = None


@dataclass
class MockPoint:
    """Mock point for Qdrant storage."""
    id: str
    vector: Union[List[float], Dict[str, List[float]]]
    payload: Dict[str, Any]


class MockCollection:
    """Mock implementation of a Qdrant collection."""
    
    def __init__(self, name: str, vector_size: int):
        """Initialize the mock collection."""
        self.name = name
        self.vector_size = vector_size
        self.points = {}
    
    def add_point(self, point: MockPoint) -> None:
        """Add a point to the collection."""
        self.points[point.id] = point
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 10,
        query_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search the collection using a query vector.
        
        Args:
            query_vector: The query vector
            limit: Maximum number of results
            query_filter: Optional filter
            
        Returns:
            List of search results
        """
        # This is a very simplified cosine similarity calculation
        # In a real implementation, we would use vector math libraries
        results = []
        for point_id, point in self.points.items():
            # Skip if filter doesn't match
            if query_filter and not self._matches_filter(point, query_filter):
                continue
                
            # Calculate dummy similarity score (simplified)
            score = 0.5  # Default middle score
            
            # Add to results
            results.append({
                "id": point_id,
                "score": score,
                "payload": point.payload,
                "vector": point.vector
            })
        
        # Sort by score and limit results
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    def _matches_filter(self, point: MockPoint, query_filter: Dict[str, Any]) -> bool:
        """
        Check if a point matches a filter.
        
        Args:
            point: The point to check
            query_filter: The filter to apply
            
        Returns:
            True if the point matches the filter, False otherwise
        """
        # This is a very simplified filter implementation
        # In a real implementation, we would use more complex logic
        
        # Check must conditions
        if "must" in query_filter:
            for condition in query_filter["must"]:
                field = condition.get("key")
                if field not in point.payload:
                    return False
                    
                # Check match condition
                match = condition.get("match", {})
                if match:
                    if point.payload[field] != match.get("value"):
                        return False
        
        return True


class MockQdrantClient:
    """Mock implementation of Qdrant client."""
    
    def __init__(self, host: Optional[str] = None, port: Optional[int] = None):
        """Initialize the mock client."""
        self.collections = {}
    
    def create_collection(
        self,
        collection_name: str,
        vectors_config: Dict[str, Any]
    ) -> None:
        """
        Create a collection.
        
        Args:
            collection_name: Name of the collection
            vectors_config: Vector configuration
        """
        vector_size = vectors_config.get("size", 768)
        self.collections[collection_name] = MockCollection(collection_name, vector_size)
    
    def upsert(
        self,
        collection_name: str,
        points: List[Dict[str, Any]],
        wait: bool = True
    ) -> Dict[str, Any]:
        """
        Insert or update points in a collection.
        
        Args:
            collection_name: Name of the collection
            points: Points to insert or update
            wait: Whether to wait for the operation to complete
            
        Returns:
            Operation status
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
            
        collection = self.collections[collection_name]
        
        for point in points:
            point_id = point.get("id") or str(uuid.uuid4())
            vector = point.get("vector", [0.0] * collection.vector_size)
            payload = point.get("payload", {})
            
            collection.add_point(MockPoint(
                id=point_id,
                vector=vector,
                payload=payload
            ))
        
        return {"status": "ok"}
    
    def search(
        self,
        collection_name: str,
        query_vector: List[float],
        query_filter: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        with_payload: bool = True,
        with_vectors: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Search a collection.
        
        Args:
            collection_name: Name of the collection
            query_vector: Query vector
            query_filter: Optional filter
            limit: Maximum number of results
            with_payload: Whether to include payload in results
            with_vectors: Whether to include vectors in results
            
        Returns:
            List of search results
        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} does not exist")
            
        collection = self.collections[collection_name]
        
        results = collection.search(
            query_vector=query_vector,
            limit=limit,
            query_filter=query_filter
        )
        
        # Format results according to parameters
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result["id"],
                "score": result["score"]
            }
            
            if with_payload:
                formatted_result["payload"] = result["payload"]
                
            if with_vectors:
                formatted_result["vector"] = result["vector"]
                
            formatted_results.append(formatted_result)
            
        return formatted_results
```

## Evaluation Tests Using ADK's Framework

ADK includes an evaluation framework that allows testing agent behavior using predefined test cases.

### Simple Example Evaluation Set (`tests/eval/simple.evalset.json`)

```json
{
  "evalset": {
    "name": "RaderBot Core Functionality",
    "description": "Basic tests for RaderBot agent functionality",
    "eval_cases": [
      {
        "name": "time_query",
        "description": "Test time tool functionality",
        "user_query": "What time is it in New York?",
        "eval_tests": [
          {
            "name": "contains_time_and_city",
            "description": "Response should contain time and the city name",
            "eval_fn": {
              "fn_name": "response_contains_all",
              "params": {
                "substrings": ["time", "New York"]
              }
            }
          },
          {
            "name": "tool_used",
            "description": "The time tool should be used",
            "eval_fn": {
              "fn_name": "used_tool",
              "params": {
                "tool_name": "get_current_time"
              }
            }
          }
        ]
      },
      {
        "name": "weather_query",
        "description": "Test weather tool functionality",
        "user_query": "What's the weather like in London?",
        "eval_tests": [
          {
            "name": "contains_weather_and_city",
            "description": "Response should contain weather information and the city name",
            "eval_fn": {
              "fn_name": "response_contains_all",
              "params": {
                "substrings": ["weather", "London"]
              }
            }
          },
          {
            "name": "tool_used",
            "description": "The weather tool should be used",
            "eval_fn": {
              "fn_name": "used_tool",
              "params": {
                "tool_name": "get_weather"
              }
            }
          }
        ]
      },
      {
        "name": "memory_query",
        "description": "Test memory functionality",
        "user_query": "What did we talk about yesterday?",
        "eval_tests": [
          {
            "name": "memory_search_used",
            "description": "The memory search tool should be used",
            "eval_fn": {
              "fn_name": "used_tool",
              "params": {
                "tool_name": "search_past_conversations"
              }
            }
          }
        ]
      }
    ]
  }
}
```

### Running Evaluation Tests

To run evaluation tests with ADK:

```bash
adk eval --evalset tests/eval/simple.evalset.json --agent-file raderbot/agent.py --agent-name main_agent
```

## End-to-End Testing

For end-to-end testing, we test complete workflows:

```python
# tests/e2e/test_workflows.py

"""
End-to-end tests for RaderBot workflows.
"""

import unittest
from unittest.mock import MagicMock, patch
import os
import tempfile

from raderbot.agent_factory import create_memory_enabled_agent
from raderbot.tools.mcp_tools import home_assistant_mcp


class TestAgentWorkflows(unittest.TestCase):
    """End-to-end tests for agent workflows."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create patches
        self.qdrant_patch = patch('raderbot.memory.qdrant_memory.QdrantClient')
        self.embed_patch = patch('raderbot.memory.embedding.embed_text', return_value=[0.1] * 768)
        self.model_patch = patch('raderbot.memory.embedding.get_embedding_model')
        self.mcp_patch = patch('raderbot.tools.mcp_tools.MCPToolset')
        
        # Start patches
        self.mock_qdrant = self.qdrant_patch.start()
        self.mock_embed = self.embed_patch.start()
        self.mock_get_model = self.model_patch.start()
        self.mock_mcp = self.mcp_patch.start()
        
        # Mock embedding model
        mock_model = MagicMock()
        mock_model.vector_size = 768
        self.mock_get_model.return_value = mock_model
        
        # Mock MCP toolset
        mock_toolset = MagicMock()
        self.mock_mcp.return_value = mock_toolset
        
        # Set up mock Qdrant client
        mock_client = MagicMock()
        self.mock_qdrant.return_value = mock_client
        
        # Mock collections
        mock_collections = MagicMock()
        mock_collections.collections = []
        mock_client.get_collections.return_value = mock_collections
        
        # Mock search results
        mock_result = MagicMock()
        mock_result.score = 0.95
        mock_result.payload = {
            "text": "User: What is the weather?\nAssistant: It's sunny today.",
            "memory_type": "conversation_turn",
            "timestamp": "2023-01-01T12:00:00Z"
        }
        mock_client.search.return_value = [mock_result]
        
        # Setup environment variables
        os.environ["HA_MCP_SSE_URL"] = "http://fake-ha-host:8123/api/mcp_server/sse"
        os.environ["HA_AUTH_TOKEN"] = "fake-token"
        
        # Initialize Home Assistant MCP
        home_assistant_mcp.toolset = mock_toolset
        
    def tearDown(self):
        """Tear down test fixtures."""
        # Stop patches
        self.qdrant_patch.stop()
        self.embed_patch.stop()
        self.model_patch.stop()
        self.mcp_patch.stop()
        
        # Clear environment variables
        if "HA_MCP_SSE_URL" in os.environ:
            del os.environ["HA_MCP_SSE_URL"]
        if "HA_AUTH_TOKEN" in os.environ:
            del os.environ["HA_AUTH_TOKEN"]
    
    @patch('google.adk.runners.Runner')
    def test_basic_question_workflow(self, mock_runner_class):
        """Test the workflow for answering a basic question."""
        # Mock runner response
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        
        mock_event = MagicMock()
        mock_event.type.name = "TEXT"
        mock_event.payload = {"author_role": "assistant", "text": "The answer is 42."}
        mock_runner.run_async.return_value = [mock_event]
        
        # Create agent
        agent = create_memory_enabled_agent()
        
        # Process a basic question
        response = agent.process_message("user123", "What is the answer to life?")
        
        # Verify runner was called
        mock_runner.run_async.assert_called_once()
        
        # Verify response
        self.assertEqual(response, "The answer is 42.")
    
    @patch('google.adk.runners.Runner')
    def test_time_query_workflow(self, mock_runner_class):
        """Test the workflow for answering a time question."""
        # Mock runner response
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        
        mock_event = MagicMock()
        mock_event.type.name = "TEXT"
        mock_event.payload = {"author_role": "assistant", "text": "The time in New York is 12:00:00."}
        mock_runner.run_async.return_value = [mock_event]
        
        # Create agent
        agent = create_memory_enabled_agent()
        
        # Process a time question
        response = agent.process_message("user123", "What time is it in New York?")
        
        # Verify runner was called
        mock_runner.run_async.assert_called_once()
        
        # Verify response
        self.assertEqual(response, "The time in New York is 12:00:00.")
    
    @patch('google.adk.runners.Runner')
    def test_home_assistant_workflow(self, mock_runner_class):
        """Test the workflow for a Home Assistant command."""
        # Mock runner response
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner
        
        mock_event = MagicMock()
        mock_event.type.name = "TEXT"
        mock_event.payload = {"author_role": "assistant", "text": "I've turned on the living room lights."}
        mock_runner.run_async.return_value = [mock_event]
        
        # Create agent
        agent = create_memory_enabled_agent()
        
        # Add Home Assistant MCP toolset
        agent.add_tool(home_assistant_mcp.toolset)
        
        # Process a Home Assistant command
        response = agent.process_message("user123", "Turn on the living room lights.")
        
        # Verify runner was called
        mock_runner.run_async.assert_called_once()
        
        # Verify response
        self.assertEqual(response, "I've turned on the living room lights.")
```

## Running the Tests

The tests can be run using the standard unittest framework or pytest:

```bash
# Using unittest
python -m unittest discover -s tests

# Using pytest
pytest tests/

# Running a specific test file
pytest tests/unit/test_agent.py

# Running a specific test
pytest tests/unit/test_agent.py::TestRaderBotAgent::test_init
```

## CI/CD Integration

The tests can be integrated into a CI/CD pipeline using GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        python -m pytest --cov=raderbot tests/
    - name: Upload coverage report
      uses: codecov/codecov-action@v1
```

## Next Steps

After implementing the testing framework:

1. Run the tests to ensure all components work correctly
2. Address any issues found during testing
3. Set up continuous integration for automated testing
4. Create additional tests for edge cases and error handling