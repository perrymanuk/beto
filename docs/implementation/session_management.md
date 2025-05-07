# Session Management

<!-- Version: 0.4.0 | Last Updated: 2025-05-07 -->


This document explains how session management is implemented in RadBot using the Google Agent Development Kit (ADK).

## Overview

RadBot uses Google ADK's `InMemorySessionService` for session management, which allows the agent to maintain conversation state across multiple interactions with the user. This service is responsible for:

- Creating new sessions for users
- Getting existing sessions
- Updating sessions with new events
- Deleting sessions when they're no longer needed

## Implementation Details

The session management is primarily handled in `radbot/agent/agent.py` through the `RadBotAgent` class. 

### Session Service Initialization

When a `RadBotAgent` is created, it initializes a session service either using a provided one or by creating a new `InMemorySessionService`:

```python
# Use provided session service or create an in-memory one
self.session_service = session_service or InMemorySessionService()

# Store app_name for use with session service
self.app_name = "radbot"
```

### Session Management Methods

The `RadBotAgent` has methods for managing sessions:

1. **Getting and creating sessions** in `process_message`:
   ```python
   session = self.session_service.get_session(
       app_name=self.app_name,
       user_id=user_id,
       session_id=session_id
   )
   
   # If no session exists, create one
   session = self.session_service.create_session(
       app_name=self.app_name,
       user_id=user_id,
       session_id=session_id
   )
   ```

2. **Resetting sessions** in `reset_session`:
   ```python
   self.session_service.delete_session(
       app_name=self.app_name,
       user_id=user_id,
       session_id=session_id
   )
   ```

## Session Parameters

The ADK `InMemorySessionService` requires several parameters for operations:

- `app_name`: The name of the application ("radbot")
- `user_id`: Unique identifier for the user
- `session_id`: Unique identifier for the conversation session

## Best Practices

1. **Consistent Session IDs**: We generate stable session IDs from user IDs to maintain continuity:
   ```python
   session_id = f"session_{user_id[:8]}"
   ```

2. **Error Handling**: We include robust error handling around session operations to ensure the agent continues functioning even if session management fails.

3. **Session Reset**: We provide a way for users to reset their conversation through the CLI interface with the `/reset` command.

## Troubleshooting

A common issue with session management occurs when the ADK version changes and method signatures are updated. If you encounter errors like:

```
InMemorySessionService.get_session() missing required keyword-only arguments: 'app_name' and 'user_id'
```

Ensure that all calls to session service methods include the required parameters (`app_name`, `user_id`, and `session_id`). The `RadBotAgent` class stores the application name as `self.app_name` and passes it to all session service method calls.
