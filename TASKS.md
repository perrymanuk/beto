# Tasks

This file tracks development tasks for the Raderbot project.

## Setup & Infrastructure

- [x] Create initial directory structure
- [x] Set up Python packaging (pyproject.toml)
- [x] Create basic configuration files (.env.example, Makefile)
- [ ] Set up Qdrant database (local or cloud instance)
- [ ] Configure CI/CD pipeline

## Core Implementation

- [x] Implement base Agent structure using ADK
- [x] Set up configurable agent prompts
- [x] Configure model selection system
- [x] Implement ConfigManager for centralized configuration
- [x] Implement basic tools (time, weather)
- [x] Create Runner and Session service setup

## Memory System

- [x] Implement QdrantMemoryService
- [ ] Create memory ingestion pipeline
- [x] Implement memory retrieval logic
- [x] Add memory tools (search_past_conversations, store_important_information)
- [x] Create memory-enabled agent factory

## External Integration

- [x] Set up MCP client for Home Assistant
- [x] Integrate Home Assistant tools

## Testing & Documentation

- [ ] Create unit tests for basic tools
- [ ] Create integration tests for agent workflows
- [ ] Create ADK evaluation datasets
- [x] Write implementation documentation
- [x] Document agent configuration
- [ ] Document memory system architecture

## CLI & Interfaces

- [x] Implement CLI interface
- [ ] Create scheduler for background tasks
- [x] Add logging system
