# radbot Architecture

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document provides an overview of the radbot architecture, detailing the key components and their interactions.

## Overview

radbot is a modular AI agent framework built on Google's Agent Development Kit (ADK). It uses Gemini models for reasoning, Qdrant for persistent memory, MCP for external service communication, and optionally A2A for inter-agent communication.

## Key Components

### 1. Agent Framework (ADK)

- **Core Agent**: Main orchestrator for user interactions
- **Sub-Agents**: Specialized agents for specific tasks
- **Runner**: Manages agent execution and session state
- **SessionService**: Handles conversation state

### 2. Memory System (Qdrant)

- **QdrantMemoryService**: Custom implementation of ADK's MemoryService
- **Memory Storage**: Stores vectorized conversation data
- **Memory Retrieval**: Semantic search for relevant past context

### 3. Tool System

- **Basic Tools**: Time, weather, and other utility functions
- **Memory Tools**: Search past conversations
- **MCP Tools**: Integration with external services (Home Assistant)
- **A2A Tools**: (Optional) Communication with external agents

### 4. External Integration

- **MCP Client**: Connection to Home Assistant via Model Context Protocol
- **A2A Client**: (Optional) Connection to external agents via Agent2Agent Protocol

## Data Flow

1. User submits query through interface
2. Runner manages session and invokes main agent
3. Main agent processes query, potentially accessing:
   - Memory via QdrantMemoryService
   - Basic tools for simple functions
   - MCP tools for Home Assistant control
   - Sub-agents for specialized tasks
4. Response is synthesized and returned to user
5. Conversation is stored in session history and potentially in long-term memory

## Architecture Diagram

```
User <---> CLI/Interface <---> ADK Runner <---> Main Agent <---> LLM (Gemini)
                                   |               |
                                   v               v
                            SessionService    Tool System
                                   |          /    |    \
                                   v         /     |     \
                           QdrantMemoryService  Basic   MCP Tools
                                   |           Tools       |
                                   v                       v
                             Qdrant Database         Home Assistant
                                                        (MCP)
```