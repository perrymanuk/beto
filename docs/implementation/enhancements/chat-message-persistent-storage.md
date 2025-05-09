# Chat Message Persistent Storage Implementation

This document outlines a plan for implementing PostgreSQL-based persistent storage for chat messages in RadBot.

## Overview

Currently, chat messages in the RadBot web interface are stored in browser localStorage, which has several limitations:
- Data is limited to a single browser and can be lost when clearing cache
- Storage size is limited (typically 5-10MB per domain)
- Data isn't accessible across devices or when switching browsers

To address these issues, we'll implement a server-side storage solution using PostgreSQL, leveraging the existing database infrastructure used for the todo system, but with a dedicated schema for chat history.

## Implementation Details

### 1. Database Schema Design

Create a dedicated schema for chat message storage with two tables:

```sql
-- Create a dedicated schema for chat messages
CREATE SCHEMA IF NOT EXISTS radbot_chathistory;

-- Create a messages table for chat history
CREATE TABLE IF NOT EXISTS radbot_chathistory.chat_messages (
    message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL,
    user_id TEXT,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    agent_name TEXT,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

-- Create indexes for efficient querying
CREATE INDEX idx_chat_messages_session_id ON radbot_chathistory.chat_messages(session_id);
CREATE INDEX idx_chat_messages_timestamp ON radbot_chathistory.chat_messages(timestamp);

-- Create a sessions table to store session metadata
CREATE TABLE IF NOT EXISTS radbot_chathistory.chat_sessions (
    session_id UUID PRIMARY KEY,
    name TEXT,
    user_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP WITH TIME ZONE,
    preview TEXT,
    is_active BOOLEAN DEFAULT true
);
```

### 2. Backend Implementation

#### 2.1 Database Connection Module

Create a dedicated connection module for chat history at `radbot/web/db/connection.py`:
- Reuse connection pooling pattern from the todo system
- Create a separate schema for chat history
- Add configuration options for connection details

#### 2.2 Database Operations Module

Create a database operations module at `radbot/web/db/chat_operations.py` with the following functionality:
- Create schema and tables if they don't exist
- Add messages to the database
- Retrieve messages by session ID
- Create, update, and manage sessions
- List available sessions
- Delete sessions (mark as inactive)

#### 2.3 API Endpoints

Add the following API endpoints:

**Messages API**:
- `POST /api/messages/{session_id}` - Create a new message
- `POST /api/messages/{session_id}/batch` - Create multiple messages at once
- `GET /api/messages/{session_id}` - Retrieve messages for a session

**Sessions API** (update existing):
- Update `/api/sessions/` to use database storage
- Update `/api/sessions/create` to create in database
- Update `/api/sessions/{session_id}/rename` to update in database
- Update `/api/sessions/{session_id}` to retrieve from database
- Add `/api/sessions/{session_id}/reset` to clear messages for a session

#### 2.4 App Initialization

Update `radbot/web/app.py` to initialize the database schema during startup:
- Create a dedicated connection pool
- Create schema and tables if they don't exist
- Register message API endpoints

### 3. Frontend Implementation

Update the frontend to sync with the server:

#### 3.1 Enhanced ChatPersistence

Modify `radbot/web/static/js/chat_persistence.js` to add server synchronization:
- Add methods to send messages to the server API
- Add methods to retrieve messages from the server
- Implement hybrid storage (localStorage + server) for offline capability
- Add automatic sync on reconnect
- Add periodic sync

#### 3.2 Message Management

Update `radbot/web/static/js/chat.js`:
- Modify the add message function to also save to server
- Add fallback to server when localStorage fails
- Add recovery from server when local storage is cleared

#### 3.3 App Initialization

Update `radbot/web/static/js/app_main.js`:
- Add periodic sync with server
- Add sync on connection restored

### 4. Configuration

Update `config.yaml` to include database settings for chat history:

```yaml
database:
  # Existing database config
  db_name: "radbot"
  user: "radbot"
  password: "radbot_password"
  host: "localhost"
  port: "5432"
  
  # Chat history specific config (optional)
  chat_history:
    schema: "radbot_chathistory" # Default schema name
    # Override connection details if needed (optional)
    db_name: null # Use main database if null
    user: null # Use main user if null
    password: null # Use main password if null
    host: null # Use main host if null
    port: null # Use main port if null
```

## Benefits

This implementation:
1. Preserves all chat messages even if browser storage is cleared or user switches devices
2. Stores both user and assistant messages for complete conversation history
3. Maintains offline functionality through the hybrid approach
4. Keeps separate schema for clean isolation from other data
5. Leverages existing database infrastructure without duplication

## Technical Notes

1. We use a hybrid approach (localStorage + server) to ensure:
   - Messages are available offline
   - Messages persist across browsers and devices
   - The application continues to work if database connection fails

2. Security considerations:
   - All messages are associated with a session ID
   - No authentication is implemented in this basic plan (could be added later)
   - Inactive sessions are not physically deleted, just marked as inactive

3. Implementation details:
   - The dedicated schema approach isolates chat data from todo data
   - Both user and assistant messages are stored with their roles
   - Metadata is stored as JSONB for flexibility
   

1. Database Schema Design

  We'll create a dedicated schema for chat history in the existing database:

  -- Create a dedicated schema for chat messages
  CREATE SCHEMA IF NOT EXISTS radbot_chathistory;

  -- Create a messages table for chat history
  CREATE TABLE IF NOT EXISTS radbot_chathistory.chat_messages (
      message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      session_id UUID NOT NULL,
      user_id TEXT,
      role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
      content TEXT NOT NULL,
      agent_name TEXT,
      timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
      metadata JSONB
  );

  -- Create indexes for efficient querying
  CREATE INDEX idx_chat_messages_session_id ON radbot_chathistory.chat_messages(session_id);
  CREATE INDEX idx_chat_messages_timestamp ON radbot_chathistory.chat_messages(timestamp);

  -- Create a sessions table to store session metadata
  CREATE TABLE IF NOT EXISTS radbot_chathistory.chat_sessions (
      session_id UUID PRIMARY KEY,
      name TEXT,
      user_id TEXT,
      created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
      last_message_at TIMESTAMP WITH TIME ZONE,
      preview TEXT,
      is_active BOOLEAN DEFAULT true
  );

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☐ Configure separate schema for chat history in database
     ☐ Create chat operations module with DB functions
     ☐ Add message API endpoints
     ☐ Update session API to use database instead of memory
     ☐ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 2. Configure Database Connection

  Create a separate connection module for chat history at radbot/web/db/connection.py:

  """
  Database connection handling for Chat History Storage.

  This module creates a connection pool specifically for the chat history schema.
  """

  import os
  import logging
  import psycopg2
  import psycopg2.pool
  import psycopg2.extras
  import uuid
  from contextlib import contextmanager
  from typing import Generator

  # Import configuration
  from radbot.config import config_loader

  # Setup logging
  logger = logging.getLogger(__name__)

  # --- Connection Pool Setup ---

  # Get database configuration from config.yaml
  database_config = config_loader.get_config().get("database", {})
  chat_db_config = database_config.get("chat_history", {})

  # Load schema name with a default fallback
  CHAT_SCHEMA = chat_db_config.get("schema", "radbot_chathistory")

  # Load connection details from config or environment
  DB_NAME = chat_db_config.get("db_name") or database_config.get("db_name") or os.getenv("POSTGRES_DB")
  DB_USER = chat_db_config.get("user") or database_config.get("user") or os.getenv("POSTGRES_USER")
  DB_PASSWORD = chat_db_config.get("password") or database_config.get("password") or os.getenv("POSTGRES_PASSWORD")
  DB_HOST = chat_db_config.get("host") or database_config.get("host") or os.getenv("POSTGRES_HOST", "localhost")
  DB_PORT = chat_db_config.get("port") or database_config.get("port") or os.getenv("POSTGRES_PORT", "5432")

  # Basic validation
  if not all([DB_NAME, DB_USER, DB_PASSWORD]):
      error_msg = "Database credentials (database.chat_history.db_name, database.chat_history.user, database.chat_history.password) must be set in config.yaml or as
  environment variables"
      logger.error(error_msg)
      raise ValueError(error_msg)

  # Register UUID adapter for psycopg2
  psycopg2.extensions.register_adapter(uuid.UUID, lambda u: psycopg2.extensions.adapt(str(u)))

  # Configure and initialize the connection pool
  # Adjust minconn and maxconn based on expected load
  MIN_CONN = 1
  MAX_CONN = 5  # Start conservatively

  # Global pool reference
  chat_pool = None

  def initialize_connection_pool():
      """Initialize the connection pool for chat history database."""
      global chat_pool

      try:
          chat_pool = psycopg2.pool.ThreadedConnectionPool(
              minconn=MIN_CONN,
              maxconn=MAX_CONN,
              database=DB_NAME,
              user=DB_USER,
              password=DB_PASSWORD,
              host=DB_HOST,
              port=DB_PORT
          )
          logger.info(f"Chat history database connection pool initialized (Min: {MIN_CONN}, Max: {MAX_CONN})")
          logger.info(f"Connected to PostgreSQL database '{DB_NAME}' using schema '{CHAT_SCHEMA}' at {DB_HOST}:{DB_PORT}")
          return True
      except psycopg2.OperationalError as e:
          logger.error(f"FATAL: Could not connect to database: {e}")
          # Handle fatal error gracefully - return False instead of raising
          return False

  @contextmanager
  def get_chat_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
      """Provides a database connection from the pool, managing cleanup."""
      global chat_pool

      # Initialize pool if not already initialized
      if chat_pool is None:
          if not initialize_connection_pool():
              raise RuntimeError("Could not initialize database connection pool")

      conn = None
      try:
          conn = chat_pool.getconn()
          # Set the search path to use our schema
          with conn.cursor() as cursor:
              cursor.execute(f"SET search_path TO {CHAT_SCHEMA}, public;")
          yield conn
      except psycopg2.Error as e:
          # Log or handle pool errors if necessary
          logger.error(f"Error getting connection from pool: {e}")
          raise  # Re-raise the original psycopg2 error
      finally:
          if conn:
              chat_pool.putconn(conn)  # Return connection to the pool

  @contextmanager
  def get_chat_db_cursor(conn: psycopg2.extensions.connection, commit: bool = False) -> Generator[psycopg2.extensions.cursor, None, None]:
      """Provides a cursor from a connection, handling commit/rollback."""
      with conn.cursor() as cursor:
          try:
              yield cursor
              if commit:
                  conn.commit()
          except psycopg2.Error as e:
              logger.error(f"Database operation failed. Rolling back transaction. Error: {e}")
              conn.rollback()
              raise  # Re-raise the original psycopg2 error
          # No finally block needed for cursor, 'with' handles closing

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☒ Configure separate schema for chat history in database
     ☐ Create chat operations module with DB functions
     ☐ Add message API endpoints
     ☐ Update session API to use database instead of memory
     ☐ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 3. Create Chat Operations Module

  Create radbot/web/db/chat_operations.py:

  """
  Database operations for chat message persistence.

  This module handles all operations for storing and retrieving chat messages
  using the dedicated radbot_chathistory schema.
  """
  import logging
  import uuid
  import json
  from typing import List, Dict, Any, Optional
  import psycopg2
  import psycopg2.extras

  # Use our custom connection functions
  from radbot.web.db.connection import get_chat_db_connection, get_chat_db_cursor, CHAT_SCHEMA

  logger = logging.getLogger(__name__)

  def create_schema_if_not_exists() -> bool:
      """
      Create the chat history schema and tables if they don't exist.

      Returns:
          bool: True if schema was created or already exists, False on error
      """
      try:
          with get_chat_db_connection() as conn:
              with get_chat_db_cursor(conn, commit=True) as cursor:
                  # Create schema if not exists
                  cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {CHAT_SCHEMA};")

                  # Set search path to our schema
                  cursor.execute(f"SET search_path TO {CHAT_SCHEMA}, public;")

                  # Create chat_messages table if not exists
                  cursor.execute(f"""
                      CREATE TABLE IF NOT EXISTS {CHAT_SCHEMA}.chat_messages (
                          message_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                          session_id UUID NOT NULL,
                          user_id TEXT,
                          role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
                          content TEXT NOT NULL,
                          agent_name TEXT,
                          timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          metadata JSONB
                      );
                  """)

                  # Create indexes if they don't exist
                  cursor.execute(f"""
                      DO $$
                      BEGIN
                          IF NOT EXISTS (
                              SELECT 1 FROM pg_indexes
                              WHERE schemaname = '{CHAT_SCHEMA}'
                              AND indexname = 'idx_chat_messages_session_id'
                          ) THEN
                              CREATE INDEX idx_chat_messages_session_id
                              ON {CHAT_SCHEMA}.chat_messages(session_id);
                          END IF;

                          IF NOT EXISTS (
                              SELECT 1 FROM pg_indexes
                              WHERE schemaname = '{CHAT_SCHEMA}'
                              AND indexname = 'idx_chat_messages_timestamp'
                          ) THEN
                              CREATE INDEX idx_chat_messages_timestamp
                              ON {CHAT_SCHEMA}.chat_messages(timestamp);
                          END IF;
                      END
                      $$;
                  """)

                  # Create chat_sessions table if not exists
                  cursor.execute(f"""
                      CREATE TABLE IF NOT EXISTS {CHAT_SCHEMA}.chat_sessions (
                          session_id UUID PRIMARY KEY,
                          name TEXT,
                          user_id TEXT,
                          created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          last_message_at TIMESTAMP WITH TIME ZONE,
                          preview TEXT,
                          is_active BOOLEAN DEFAULT true
                      );
                  """)

                  logger.info(f"Chat history schema and tables created or verified in schema '{CHAT_SCHEMA}'")
                  return True
      except Exception as e:
          logger.error(f"Error creating chat history schema: {e}")
          return False

  def add_message(session_id: str, role: str, content: str,
                 agent_name: Optional[str] = None,
                 user_id: Optional[str] = None,
                 metadata: Optional[Dict] = None) -> Optional[str]:
      """
      Insert a new message into the database.

      Args:
          session_id: Session identifier
          role: Message role ('user', 'assistant', 'system')
          content: Message content
          agent_name: Optional agent name for assistant messages
          user_id: Optional user identifier
          metadata: Optional metadata as dict

      Returns:
          message_id: UUID of the inserted message or None on error
      """
      # Convert session_id to UUID if string
      if isinstance(session_id, str):
          try:
              session_id = uuid.UUID(session_id)
          except ValueError:
              logger.error(f"Invalid session_id format: {session_id}")
              return None

      # Convert metadata to JSON if provided
      if metadata is not None:
          metadata = json.dumps(metadata)

      sql = f"""
          INSERT INTO {CHAT_SCHEMA}.chat_messages
          (session_id, role, content, agent_name, user_id, metadata)
          VALUES (%s, %s, %s, %s, %s, %s::jsonb)
          RETURNING message_id;
      """

      params = (session_id, role, content, agent_name, user_id, metadata)

      try:
          with get_chat_db_connection() as conn:
              with get_chat_db_cursor(conn, commit=True) as cursor:
                  cursor.execute(sql, params)
                  message_id = cursor.fetchone()[0]

                  # Update session last_message
                  update_session_last_message(conn, session_id, content, role)

                  return str(message_id)
      except Exception as e:
          logger.error(f"Error adding message: {e}")
          return None

  def get_messages_by_session_id(session_id: str, limit: int = 200, offset: int = 0) -> List[Dict[str, Any]]:
      """
      Get messages for a specific session.

      Args:
          session_id: Session identifier
          limit: Maximum number of messages to return
          offset: Number of messages to skip

      Returns:
          List of message dictionaries
      """
      # Convert session_id to UUID if string
      if isinstance(session_id, str):
          try:
              session_id = uuid.UUID(session_id)
          except ValueError:
              logger.error(f"Invalid session_id format: {session_id}")
              return []

      sql = f"""
          SELECT message_id, session_id, role, content, agent_name,
                 timestamp, user_id, metadata
          FROM {CHAT_SCHEMA}.chat_messages
          WHERE session_id = %s
          ORDER BY timestamp ASC
          LIMIT %s OFFSET %s;
      """

      params = (session_id, limit, offset)

      try:
          with get_chat_db_connection() as conn:
              with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                  cursor.execute(sql, params)
                  results = cursor.fetchall()

                  # Convert to standard dicts and format fields
                  messages = []
                  for row in results:
                      message = dict(row)
                      # Convert UUIDs to strings
                      message['message_id'] = str(message['message_id'])
                      message['session_id'] = str(message['session_id'])
                      # Convert timestamp to ISO format
                      if message['timestamp']:
                          message['timestamp'] = message['timestamp'].isoformat()
                      messages.append(message)

                  return messages
      except Exception as e:
          logger.error(f"Error getting messages for session {session_id}: {e}")
          return []

  def create_or_update_session(session_id: str, name: Optional[str] = None,
                             user_id: Optional[str] = None) -> bool:
      """
      Create or update a chat session.

      Args:
          session_id: Session identifier
          name: Optional session name
          user_id: Optional user identifier

      Returns:
          bool: True if successful, False on error
      """
      # Convert session_id to UUID if string
      if isinstance(session_id, str):
          try:
              session_id = uuid.UUID(session_id)
          except ValueError:
              logger.error(f"Invalid session_id format: {session_id}")
              return False

      # Insert or update SQL
      sql = f"""
          INSERT INTO {CHAT_SCHEMA}.chat_sessions (session_id, name, user_id)
          VALUES (%s, %s, %s)
          ON CONFLICT (session_id)
          DO UPDATE SET
              name = COALESCE(EXCLUDED.name, chat_sessions.name),
              user_id = COALESCE(EXCLUDED.user_id, chat_sessions.user_id),
              is_active = true;
      """

      params = (session_id, name, user_id)

      try:
          with get_chat_db_connection() as conn:
              with get_chat_db_cursor(conn, commit=True) as cursor:
                  cursor.execute(sql, params)
                  return True
      except Exception as e:
          logger.error(f"Error creating/updating session {session_id}: {e}")
          return False

  def update_session_last_message(conn, session_id: uuid.UUID, preview: str, role: str) -> bool:
      """
      Update session last message timestamp and preview.
      Used internally by add_message.

      Args:
          conn: Database connection
          session_id: Session identifier
          preview: Preview text (truncated message content)
          role: Message role

      Returns:
          bool: True if successful, False on error
      """
      # Only update preview for user or assistant messages
      if role not in ('user', 'assistant'):
          return True

      # Truncate preview text
      if preview and len(preview) > 100:
          preview = preview[:97] + "..."

      # Update session
      sql = f"""
          INSERT INTO {CHAT_SCHEMA}.chat_sessions
          (session_id, last_message_at, preview)
          VALUES (%s, CURRENT_TIMESTAMP, %s)
          ON CONFLICT (session_id)
          DO UPDATE SET
              last_message_at = CURRENT_TIMESTAMP,
              preview = %s;
      """

      params = (session_id, preview, preview)

      try:
          with get_chat_db_cursor(conn, commit=True) as cursor:
              cursor.execute(sql, params)
              return True
      except Exception as e:
          logger.error(f"Error updating session last message: {e}")
          return False

  def list_sessions(user_id: Optional[str] = None, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
      """
      List chat sessions, optionally filtered by user.

      Args:
          user_id: Optional user identifier to filter by
          limit: Maximum number of sessions to return
          offset: Number of sessions to skip

      Returns:
          List of session dictionaries
      """
      base_sql = f"""
          SELECT session_id, name, user_id, created_at, last_message_at, preview, is_active
          FROM {CHAT_SCHEMA}.chat_sessions
          WHERE is_active = true
      """

      params = []

      if user_id:
          base_sql += " AND user_id = %s"
          params.append(user_id)

      base_sql += """
          ORDER BY COALESCE(last_message_at, created_at) DESC
          LIMIT %s OFFSET %s;
      """

      params.extend([limit, offset])

      try:
          with get_chat_db_connection() as conn:
              with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                  cursor.execute(base_sql, tuple(params))
                  results = cursor.fetchall()

                  # Convert to standard dicts and format fields
                  sessions = []
                  for row in results:
                      session = dict(row)
                      # Convert UUID to string
                      session['session_id'] = str(session['session_id'])
                      # Convert timestamps to ISO format
                      if session.get('created_at'):
                          session['created_at'] = session['created_at'].isoformat()
                      if session.get('last_message_at'):
                          session['last_message_at'] = session['last_message_at'].isoformat()
                      sessions.append(session)

                  return sessions
      except Exception as e:
          logger.error(f"Error listing sessions: {e}")
          return []

  def get_session_message_count(session_id: str) -> int:
      """
      Get count of messages in a session.

      Args:
          session_id: Session identifier

      Returns:
          int: Number of messages in the session
      """
      # Convert session_id to UUID if string
      if isinstance(session_id, str):
          try:
              session_id = uuid.UUID(session_id)
          except ValueError:
              logger.error(f"Invalid session_id format: {session_id}")
              return 0

      sql = f"""
          SELECT COUNT(*)
          FROM {CHAT_SCHEMA}.chat_messages
          WHERE session_id = %s;
      """

      try:
          with get_chat_db_connection() as conn:
              with conn.cursor() as cursor:
                  cursor.execute(sql, (session_id,))
                  result = cursor.fetchone()
                  return result[0] if result else 0
      except Exception as e:
          logger.error(f"Error getting message count for session {session_id}: {e}")
          return 0

  def delete_session(session_id: str) -> bool:
      """
      Delete a chat session (mark as inactive).
      Note: This doesn't actually delete data, just marks the session as inactive.

      Args:
          session_id: Session identifier

      Returns:
          bool: True if successful, False on error
      """
      # Convert session_id to UUID if string
      if isinstance(session_id, str):
          try:
              session_id = uuid.UUID(session_id)
          except ValueError:
              logger.error(f"Invalid session_id format: {session_id}")
              return False

      sql = f"""
          UPDATE {CHAT_SCHEMA}.chat_sessions
          SET is_active = false
          WHERE session_id = %s;
      """

      try:
          with get_chat_db_connection() as conn:
              with get_chat_db_cursor(conn, commit=True) as cursor:
                  cursor.execute(sql, (session_id,))
                  return True
      except Exception as e:
          logger.error(f"Error deleting session {session_id}: {e}")
          return False

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☒ Configure separate schema for chat history in database
     ☒ Create chat operations module with DB functions
     ☐ Add message API endpoints
     ☐ Update session API to use database instead of memory
     ☐ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 4. Add Message API Endpoints

  Create radbot/web/api/messages.py:

  """
  Message API endpoints for RadBot web interface.

  This module provides API endpoints for storing and retrieving chat messages.
  """
  import logging
  from typing import Dict, List, Optional, Any
  from pydantic import BaseModel, Field
  from fastapi import APIRouter, HTTPException, Path, Query

  from radbot.web.db import chat_operations

  # Set up logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # Pydantic models for request/response
  class MessageModel(BaseModel):
      """Message model for API responses."""
      message_id: str
      session_id: str
      role: str
      content: str
      agent_name: Optional[str] = None
      timestamp: str
      user_id: Optional[str] = None
      metadata: Optional[Dict[str, Any]] = None

  class MessageCreateRequest(BaseModel):
      """Request model for creating a new message."""
      role: str = Field(..., description="Message role: 'user', 'assistant', or 'system'")
      content: str = Field(..., description="Message content")
      agent_name: Optional[str] = Field(None, description="Agent name for assistant messages")
      user_id: Optional[str] = Field(None, description="User identifier")
      metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

  class MessagesResponse(BaseModel):
      """Response model for messages list."""
      messages: List[MessageModel]
      total_count: int
      has_more: bool

  class BatchMessageCreateRequest(BaseModel):
      """Request model for batch creating messages."""
      messages: List[MessageCreateRequest]

  # Create router function for registration
  def register_messages_router(app):
      """Register messages router with the FastAPI app."""
      router = APIRouter(
          prefix="/api/messages",
          tags=["messages"],
      )

      @router.post("/{session_id}", status_code=201)
      async def create_message(
          session_id: str = Path(..., description="Session identifier"),
          request: MessageCreateRequest = None
      ):
          """
          Create a new message.

          Args:
              session_id: Session identifier
              request: Message creation request

          Returns:
              Dict with status and message_id
          """
          logger.info(f"Creating message for session {session_id}")

          if not request:
              raise HTTPException(status_code=400, detail="Message content is required")

          # Validate role
          if request.role not in ('user', 'assistant', 'system'):
              raise HTTPException(status_code=400, detail="Role must be 'user', 'assistant', or 'system'")

          # Create chat session if it doesn't exist
          chat_operations.create_or_update_session(session_id)

          try:
              message_id = chat_operations.add_message(
                  session_id=session_id,
                  role=request.role,
                  content=request.content,
                  agent_name=request.agent_name,
                  user_id=request.user_id,
                  metadata=request.metadata
              )

              if not message_id:
                  raise HTTPException(status_code=500, detail="Failed to create message")

              return {"status": "success", "message_id": message_id}
          except Exception as e:
              logger.error(f"Error creating message: {e}")
              raise HTTPException(status_code=500, detail=f"Error creating message: {str(e)}")

      @router.post("/{session_id}/batch", status_code=201)
      async def create_messages_batch(
          session_id: str = Path(..., description="Session identifier"),
          request: BatchMessageCreateRequest = None
      ):
          """
          Create multiple messages at once.

          Args:
              session_id: Session identifier
              request: Batch message creation request

          Returns:
              Dict with status and list of created message IDs
          """
          if not request or not request.messages:
              raise HTTPException(status_code=400, detail="Messages are required")

          logger.info(f"Batch creating {len(request.messages)} messages for session {session_id}")

          # Create chat session if it doesn't exist
          chat_operations.create_or_update_session(session_id)

          try:
              message_ids = []
              for msg in request.messages:
                  # Validate role
                  if msg.role not in ('user', 'assistant', 'system'):
                      raise HTTPException(status_code=400,
                                        detail=f"Role must be 'user', 'assistant', or 'system' (got '{msg.role}')")

                  message_id = chat_operations.add_message(
                      session_id=session_id,
                      role=msg.role,
                      content=msg.content,
                      agent_name=msg.agent_name,
                      user_id=msg.user_id,
                      metadata=msg.metadata
                  )

                  if message_id:
                      message_ids.append(message_id)

              if not message_ids:
                  raise HTTPException(status_code=500, detail="Failed to create any messages")

              return {"status": "success", "message_ids": message_ids, "count": len(message_ids)}
          except HTTPException:
              raise  # Re-raise HTTP exceptions
          except Exception as e:
              logger.error(f"Error batch creating messages: {e}")
              raise HTTPException(status_code=500, detail=f"Error batch creating messages: {str(e)}")

      @router.get("/{session_id}")
      async def get_messages(
          session_id: str = Path(..., description="Session identifier"),
          limit: int = Query(200, ge=1, le=500, description="Maximum number of messages to return"),
          offset: int = Query(0, ge=0, description="Number of messages to skip")
      ):
          """
          Get messages for a session.

          Args:
              session_id: Session identifier
              limit: Maximum number of messages to return
              offset: Number of messages to skip

          Returns:
              MessagesResponse with messages list, total count, and has_more flag
          """
          logger.info(f"Getting messages for session {session_id} (limit={limit}, offset={offset})")

          try:
              # Get total count first (for pagination)
              total_count = chat_operations.get_session_message_count(session_id)

              # Get messages with limit+1 to check if there are more
              messages = chat_operations.get_messages_by_session_id(
                  session_id=session_id,
                  limit=limit + 1,  # Get one extra to check if there are more
                  offset=offset
              )

              # Check if there are more messages
              has_more = len(messages) > limit
              if has_more:
                  messages = messages[:limit]  # Remove the extra message

              return MessagesResponse(
                  messages=messages,
                  total_count=total_count,
                  has_more=has_more
              )
          except Exception as e:
              logger.error(f"Error getting messages: {e}")
              raise HTTPException(status_code=500, detail=f"Error getting messages: {str(e)}")

      # Register the router with the app
      app.include_router(router)
      logger.info("Messages router registered")

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☒ Configure separate schema for chat history in database
     ☒ Create chat operations module with DB functions
     ☒ Add message API endpoints
     ☐ Update session API to use database instead of memory
     ☐ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 5. Update Sessions API to Use Database

  Modify radbot/web/api/sessions.py to use the database:

  """
  Sessions API endpoints for RadBot web interface.

  This module provides API endpoints for managing multiple chat sessions.
  """
  import logging
  import uuid
  from typing import Dict, List, Optional, Any
  from pydantic import BaseModel
  from fastapi import APIRouter, Depends, HTTPException, Path, Query

  from radbot.web.api.session import (
      SessionManager,
      get_session_manager,
      get_or_create_runner_for_session,
  )
  from radbot.web.db import chat_operations

  # Set up logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # Pydantic models for request/response
  class SessionMetadata(BaseModel):
      """Session metadata for API responses."""
      id: str
      name: str
      created_at: str
      last_message_at: Optional[str] = None
      preview: Optional[str] = None

  class CreateSessionRequest(BaseModel):
      """Request model for creating a new session."""
      name: Optional[str] = None
      user_id: Optional[str] = None

  class RenameSessionRequest(BaseModel):
      """Request model for renaming a session."""
      name: str

  class SessionsListResponse(BaseModel):
      """Response model for listing sessions."""
      sessions: List[SessionMetadata]
      active_session_id: Optional[str] = None

  # Register the router with FastAPI
  def register_sessions_router(app):
      """Register the sessions router with the FastAPI app."""
      router = APIRouter(
          prefix="/api/sessions",
          tags=["sessions"],
      )

      @router.get("/", response_model=SessionsListResponse)
      async def list_sessions(
          user_id: Optional[str] = None,
          limit: int = Query(20, ge=1, le=100),
          offset: int = Query(0, ge=0),
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """List all sessions for the current user."""
          logger.info("Listing sessions for user %s", user_id or "anonymous")

          # Create the response with placeholder data - in a real system
          # we would query a database for user's sessions
          sessions = []
          active_session_id = None

          try:
              # Get sessions from database
              db_sessions = chat_operations.list_sessions(
                  user_id=user_id,
                  limit=limit,
                  offset=offset
              )

              # Transform to API model
              for db_session in db_sessions:
                  session_meta = SessionMetadata(
                      id=db_session["session_id"],
                      name=db_session["name"] or f"Session {db_session['created_at']}",
                      created_at=db_session["created_at"],
                      last_message_at=db_session["last_message_at"],
                      preview=db_session["preview"] or "New session"
                  )
                  sessions.append(session_meta)

              # If there's at least one session, use the first as active
              if sessions:
                  active_session_id = sessions[0].id

              logger.info("Found %d sessions for user", len(sessions))

              return SessionsListResponse(
                  sessions=sessions,
                  active_session_id=active_session_id
              )
          except Exception as e:
              logger.error("Error listing sessions: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error listing sessions: {str(e)}")

      @router.post("/create", response_model=SessionMetadata, status_code=201)
      async def create_session(
          request: CreateSessionRequest,
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """Create a new session."""
          logger.info("Creating new session with name: %s", request.name)

          try:
              # Generate a new session ID
              session_id = str(uuid.uuid4())
              user_id = request.user_id or f"web_user_{session_id}"

              # Create the session in the backend
              runner = await get_or_create_runner_for_session(session_id, session_manager)

              # Default name if not provided
              session_name = request.name or f"Session {session_id[:8]}"

              # Create in database
              success = chat_operations.create_or_update_session(
                  session_id=session_id,
                  name=session_name,
                  user_id=user_id
              )

              if not success:
                  raise HTTPException(status_code=500, detail="Failed to create session in database")

              # Get current timestamp
              import datetime
              created_at = datetime.datetime.now().isoformat()

              # Return session metadata
              return SessionMetadata(
                  id=session_id,
                  name=session_name,
                  created_at=created_at,
                  preview="New session started"
              )
          except HTTPException:
              raise
          except Exception as e:
              logger.error("Error creating session: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

      @router.put("/{session_id}/rename", response_model=SessionMetadata)
      async def rename_session(
          session_id: str = Path(...),
          request: RenameSessionRequest = None,
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """Rename a session."""
          if not request or not request.name:
              raise HTTPException(status_code=400, detail="Name is required")

          logger.info("Renaming session %s to %s", session_id, request.name)

          try:
              # Check if session exists in the manager
              runner = await session_manager.get_runner(session_id)
              if not runner:
                  raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

              # Update in database
              success = chat_operations.create_or_update_session(
                  session_id=session_id,
                  name=request.name
              )

              if not success:
                  raise HTTPException(status_code=500, detail="Failed to rename session in database")

              # Get session details
              sessions = chat_operations.list_sessions(limit=1)
              db_session = next((s for s in sessions if s["session_id"] == session_id), None)

              if not db_session:
                  raise HTTPException(status_code=404, detail=f"Session {session_id} not found in database")

              return SessionMetadata(
                  id=session_id,
                  name=request.name,
                  created_at=db_session["created_at"],
                  last_message_at=db_session.get("last_message_at"),
                  preview=db_session.get("preview", "Session renamed")
              )
          except HTTPException:
              raise
          except Exception as e:
              logger.error("Error renaming session: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error renaming session: {str(e)}")

      @router.delete("/{session_id}")
      async def delete_session(
          session_id: str = Path(...),
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """Delete a session."""
          logger.info("Deleting session %s", session_id)

          try:
              # Check if session exists in the manager
              runner = await session_manager.get_runner(session_id)
              if not runner:
                  raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

              # Remove from session manager
              await session_manager.remove_session(session_id)

              # Mark as inactive in database
              success = chat_operations.delete_session(session_id)

              if not success:
                  logger.warning(f"Failed to mark session {session_id} as inactive in database")

              return {"status": "success", "message": f"Session {session_id} deleted"}
          except HTTPException:
              raise
          except Exception as e:
              logger.error("Error deleting session: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error deleting session: {str(e)}")

      @router.get("/{session_id}")
      async def get_session(
          session_id: str = Path(...),
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """Get session details."""
          logger.info("Getting details for session %s", session_id)

          try:
              # Check if session exists in the manager
              runner = await session_manager.get_runner(session_id)
              if not runner:
                  raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

              # Get session from database
              sessions = chat_operations.list_sessions(limit=1)
              db_session = next((s for s in sessions if s["session_id"] == session_id), None)

              if not db_session:
                  # Create session in database if it exists in manager but not in DB
                  chat_operations.create_or_update_session(
                      session_id=session_id,
                      name=f"Session {session_id[:8]}"
                  )

                  import datetime
                  # Return basic info
                  return {
                      "id": session_id,
                      "name": f"Session {session_id[:8]}",
                      "created_at": datetime.datetime.now().isoformat(),
                      "preview": "New session"
                  }

              # Return session data from database
              return {
                  "id": session_id,
                  "name": db_session.get("name", f"Session {session_id[:8]}"),
                  "created_at": db_session["created_at"],
                  "last_message_at": db_session.get("last_message_at"),
                  "preview": db_session.get("preview", "Session data")
              }
          except HTTPException:
              raise
          except Exception as e:
              logger.error("Error getting session: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error getting session: {str(e)}")

      @router.post("/{session_id}/reset")
      async def reset_session(
          session_id: str = Path(...),
          session_manager: SessionManager = Depends(get_session_manager)
      ):
          """Reset a session (clear messages but keep session)."""
          logger.info("Resetting session %s", session_id)

          try:
              # Check if session exists
              runner = await session_manager.get_runner(session_id)
              if not runner:
                  raise HTTPException(status_code=404, detail=f"Session {session_id} not found")

              # Reset the session in the runner
              # This depends on your backend implementation

              # For database, we could do a soft reset by creating a new session with the same ID
              # and preserving metadata, but clearing messages
              # This is a simplified approach - in a real implementation, you might want to:
              # 1. Archive the old messages instead of deleting them
              # 2. Use a transaction to ensure atomicity
              try:
                  # Delete all messages for this session
                  # In a real implementation, you might want to move them to an archive table
                  with get_chat_db_connection() as conn:
                      with get_chat_db_cursor(conn, commit=True) as cursor:
                          cursor.execute(f"""
                              DELETE FROM {CHAT_SCHEMA}.chat_messages
                              WHERE session_id = %s;
                          """, (uuid.UUID(session_id),))

                  # Update session preview
                  chat_operations.create_or_update_session(
                      session_id=session_id,
                      preview="Session reset"
                  )
              except Exception as db_error:
                  logger.error(f"Database error during session reset: {db_error}")
                  # Continue even if database reset fails

              return {"status": "success", "message": f"Session {session_id} reset"}
          except HTTPException:
              raise
          except Exception as e:
              logger.error("Error resetting session: %s", str(e), exc_info=True)
              raise HTTPException(status_code=500, detail=f"Error resetting session: {str(e)}")

      # Register the router with the app
      app.include_router(router)
      logger.info("Sessions router registered")

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☒ Configure separate schema for chat history in database
     ☒ Create chat operations module with DB functions
     ☒ Add message API endpoints
     ☒ Update session API to use database instead of memory
     ☐ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 6. Update Frontend to Sync with Server

  Modify radbot/web/static/js/chat_persistence.js to add server synchronization:

  /**
   * Chat persistence module for RadBot UI with server synchronization
   * Handles both localStorage-based and server-based message storage
   */

  export class ChatPersistence {
    constructor(options = {}) {
      this.maxMessagesPerChat = options.maxMessagesPerChat || 200;
      this.storagePrefix = options.storagePrefix || 'radbot_chat_';
      this.useSessionOnly = options.useSessionOnly || false;
      this.messageCache = {}; // In-memory cache
      this.saveBatchTimeout = null;
      this.serverSyncEnabled = options.serverSyncEnabled !== false; // Enable by default

      // Session metadata - will be initialized by session manager
      this.sessionsIndexKey = 'radbot_sessions_index';

      // Listen for storage events from other tabs
      window.addEventListener('storage', this.handleStorageEvent.bind(this));

      // Track online status for server sync
      this.isOnline = window.navigator.onLine;
      window.addEventListener('online', () => {
        console.log('Browser went online, triggering sync');
        this.isOnline = true;
        this.syncWithServer(window.state?.sessionId);
      });

      window.addEventListener('offline', () => {
        console.log('Browser went offline, disabling sync');
        this.isOnline = false;
      });
    }

    // Get the appropriate storage object
    getStorage() {
      return this.useSessionOnly ? sessionStorage : localStorage;
    }

    // Save messages with debounced writes to improve performance
    saveMessages(chatId, messages) {
      if (!chatId || !Array.isArray(messages)) {
        console.error('Invalid parameters for saveMessages:', { chatId, messageCount: messages ? messages.length : 0 });
        return false;
      }

      // Make sure messages are valid before saving
      const validMessages = this.validateMessages(messages);

      // Update in-memory cache first
      this.messageCache[chatId] = validMessages.slice(-this.maxMessagesPerChat);

      console.log(`Saving ${this.messageCache[chatId].length} messages to localStorage for session ${chatId}`);

      // Function to actually perform the save
      const performSave = () => {
        try {
          const storage = this.getStorage();
          const key = `${this.storagePrefix}${chatId}`;

          // Stringify messages
          const json = JSON.stringify(this.messageCache[chatId]);

          // Verify we have actual data
          if (!json || json === '[]' || json === 'null') {
            console.warn('Attempting to save empty data to localStorage:', json);
          }

          // Save to storage
          storage.setItem(key, json);

          // Verify it was saved correctly
          const savedData = storage.getItem(key);
          if (savedData) {
            console.log(`Successfully saved ${this.messageCache[chatId].length} messages to localStorage. Data size: ${savedData.length} bytes`);

            // Trigger server sync if online and enabled
            if (this.serverSyncEnabled && this.isOnline) {
              this.syncWithServer(chatId);
            }

            return true;
          } else {
            console.error('Failed to save messages - no data found after save');
            return false;
          }
        } catch (e) {
          console.error('Error saving messages:', e);
          return false;
        }
      };

      // Batch save to storage
      clearTimeout(this.saveBatchTimeout);
      this.saveBatchTimeout = setTimeout(() => {
        try {
          if (performSave()) {
            return true;
          }

          // If save failed, try cleanup and retry
          console.log('Initial save failed, trying cleanup...');
          this.cleanupOldData();

          if (performSave()) {
            return true;
          }

          // If still failing, try session storage
          console.log('Save still failing after cleanup, trying session storage...');
          this.useSessionOnly = true;
          return this.saveMessages(chatId, messages);
        } catch (e) {
          console.error('Failed to save chat history:', e);
          return false;
        }
      }, 300);

      return true;
    }

    // Get messages for a specific chat
    getMessages(chatId) {
      if (!chatId) {
        console.warn('getMessages called with empty chatId');
        return [];
      }

      // Check in-memory cache first
      if (this.messageCache[chatId]) {
        console.log(`Using cached messages for ${chatId}: ${this.messageCache[chatId].length} messages`);
        return [...this.messageCache[chatId]];
      }

      // Try to load from storage
      try {
        const storage = this.getStorage();
        const key = `${this.storagePrefix}${chatId}`;
        console.log(`Attempting to retrieve messages from storage key: ${key}`);

        // First try getting the item directly
        let data = storage.getItem(key);

        // Log all keys for debugging
        const keys = [];
        for (let i = 0; i < storage.length; i++) {
          keys.push(storage.key(i));
        }
        console.log('All keys in storage:', keys);

        // Try to match key by exact match or substring
        if (!data) {
          const matchingKey = keys.find(k => k === key || k.includes(chatId));
          if (matchingKey) {
            console.log(`Found matching key: ${matchingKey}`);
            data = storage.getItem(matchingKey);
          }
        }

        if (data) {
          try {
            console.log(`Raw data from storage: ${data.substring(0, 50)}...`);
            const messages = JSON.parse(data);
            // Validate and cache
            this.messageCache[chatId] = this.validateMessages(messages);
            console.log(`Successfully loaded ${this.messageCache[chatId].length} messages for chat ${chatId}`);
            return [...this.messageCache[chatId]];
          } catch (parseError) {
            console.error('Error parsing chat data:', parseError, 'Raw data:', data);
            return [];
          }
        } else {
          console.log(`No saved chat data found for chat ${chatId}`);

          // Try loading from server if enabled and online
          if (this.serverSyncEnabled && this.isOnline) {
            console.log(`Attempting to load messages from server for chat ${chatId}`);
            // We can't await here, so we'll return an empty array for now
            // and the server sync will update the cache asynchronously
            this.loadMessagesFromServer(chatId)
              .then(success => {
                if (success) {
                  console.log(`Successfully loaded messages from server for chat ${chatId}`);
                } else {
                  console.log(`No messages found on server for chat ${chatId}`);
                }
              })
              .catch(error => {
                console.error(`Error loading messages from server for chat ${chatId}:`, error);
              });
          }
        }
      } catch (e) {
        console.error('Error loading chat data', e);
      }

      return [];
    }

    // Add a single message to the chat history
    addMessage(chatId, message) {
      // Get existing messages
      const messages = this.getMessages(chatId);

      // Add the new message
      messages.push(message);

      // Save the updated messages locally
      const saveResult = this.saveMessages(chatId, messages);

      // Send to server if server sync is enabled and online
      if (this.serverSyncEnabled && this.isOnline) {
        this.sendMessageToServer(chatId, message)
          .catch(error => console.error('Error sending message to server:', error));
      }

      return saveResult;
    }

    // Clear chat history for a specific chat ID
    clearChat(chatId) {
      if (!chatId) return false;

      // Clear in-memory cache
      if (this.messageCache[chatId]) {
        delete this.messageCache[chatId];
      }

      // Clear from storage
      try {
        const storage = this.getStorage();
        const key = `${this.storagePrefix}${chatId}`;
        storage.removeItem(key);

        // Notify server if enabled and online
        if (this.serverSyncEnabled && this.isOnline) {
          fetch(`/api/sessions/${chatId}/reset`, { method: 'POST' })
            .catch(error => console.error('Error resetting session on server:', error));
        }

        return true;
      } catch (e) {
        console.error('Error clearing chat data', e);
        return false;
      }
    }

    // Handle storage events from other tabs
    handleStorageEvent(event) {
      // Only process our own storage keys
      if (event.key && event.key.startsWith(this.storagePrefix)) {
        const chatId = event.key.replace(this.storagePrefix, '');

        // Clear cache for this chat ID to force a reload from storage
        if (this.messageCache[chatId]) {
          delete this.messageCache[chatId];
        }

        // Dispatch an event that chat data has changed
        window.dispatchEvent(new CustomEvent('chatDataChanged', {
          detail: { chatId, source: 'storage' }
        }));
      }
    }

    // Check if error is due to quota exceeded
    isQuotaExceeded(e) {
      return (
        e instanceof DOMException &&
        (e.code === 22 || // Chrome
         e.code === 1014 || // Firefox
         e.name === 'QuotaExceededError' ||
         e.name === 'NS_ERROR_DOM_QUOTA_REACHED')
      );
    }

    // Cleanup old data to free space
    cleanupOldData() {
      const storage = this.getStorage();

      // Get all keys related to our app
      const chatKeys = [];
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key && key.startsWith(this.storagePrefix)) {
          const chatId = key.replace(this.storagePrefix, '');
          chatKeys.push({
            key,
            chatId,
            size: (storage.getItem(key) || '').length
          });
        }
      }

      // Sort by size (largest first) and remove some
      chatKeys.sort((a, b) => b.size - a.size);

      // Remove the largest items to free space
      for (let i = 0; i < Math.min(chatKeys.length, 3); i++) {
        try {
          storage.removeItem(chatKeys[i].key);
          console.log(`Removed large chat history: ${chatKeys[i].chatId} (${chatKeys[i].size} bytes)`);
        } catch (e) {
          console.error('Error removing item during cleanup', e);
        }
      }
    }

    // Validate messages array - ensure it has the right structure
    validateMessages(messages) {
      if (!Array.isArray(messages)) {
        console.warn('validateMessages: messages is not an array:', messages);
        return [];
      }

      // Filter out invalid messages
      const filteredMessages = messages.filter(msg => {
        const isValid = (
          msg &&
          typeof msg === 'object' &&
          (msg.role === 'user' || msg.role === 'assistant' || msg.role === 'system') &&
          typeof msg.content === 'string'
        );

        if (!isValid) {
          console.warn('Filtering out invalid message:', msg);
        }

        return isValid;
      });

      console.log(`validateMessages: ${filteredMessages.length}/${messages.length} messages passed validation`);
      return filteredMessages;
    }

    // Get list of all saved chats
    getAllChats() {
      const storage = this.getStorage();
      const chats = [];

      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key && key.startsWith(this.storagePrefix)) {
          const chatId = key.replace(this.storagePrefix, '');
          chats.push(chatId);
        }
      }

      return chats;
    }

    // Get the last message for a chat
    getLastMessage(chatId) {
      if (!chatId) return null;

      // Check cache first
      if (this.messageCache[chatId] && this.messageCache[chatId].length > 0) {
        return this.messageCache[chatId][this.messageCache[chatId].length - 1];
      }

      // Try to get from storage
      const messages = this.getMessages(chatId);
      if (messages && messages.length > 0) {
        return messages[messages.length - 1];
      }

      return null;
    }

    // --- Server Synchronization Methods ---

    // Sync messages with server
    async syncWithServer(sessionId) {
      if (!this.serverSyncEnabled || !this.isOnline || !sessionId) {
        return false;
      }

      console.log(`Syncing messages with server for session ${sessionId}`);

      try {
        // Get all local messages
        const messages = this.getMessages(sessionId);

        if (!messages || messages.length === 0) {
          // Try loading from server if no local messages
          return await this.loadMessagesFromServer(sessionId);
        }

        // Send to server in batches
        const batchSize = 50;
        for (let i = 0; i < messages.length; i += batchSize) {
          const batch = messages.slice(i, i + batchSize);
          await this.sendMessagesToServer(sessionId, batch);
        }

        console.log(`Successfully synced ${messages.length} messages with server for session ${sessionId}`);
        return true;
      } catch (e) {
        console.error(`Error syncing with server for session ${sessionId}:`, e);
        return false;
      }
    }

    // Send a batch of messages to server
    async sendMessagesToServer(sessionId, messages) {
      if (!sessionId || !messages || !this.isOnline || messages.length === 0) {
        return false;
      }

      try {
        // Convert messages to API format
        const apiMessages = messages.map(msg => ({
          role: msg.role,
          content: msg.content,
          agent_name: msg.agent,
          metadata: {
            client_id: msg.id,
            client_timestamp: msg.timestamp
          }
        }));

        // Send batch request
        const response = await fetch(`/api/messages/${sessionId}/batch`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ messages: apiMessages })
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        console.log(`Successfully sent ${data.count} messages to server for session ${sessionId}`);
        return true;
      } catch (e) {
        console.error(`Error sending messages to server for session ${sessionId}:`, e);
        return false;
      }
    }

    // Send a single message to server
    async sendMessageToServer(sessionId, message) {
      if (!sessionId || !message || !this.isOnline) {
        return false;
      }

      try {
        // Convert message to API format
        const apiMessage = {
          role: message.role,
          content: message.content,
          agent_name: message.agent,
          metadata: {
            client_id: message.id,
            client_timestamp: message.timestamp
          }
        };

        // Send request
        const response = await fetch(`/api/messages/${sessionId}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(apiMessage)
        });

        if (!response.ok) {
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        console.log(`Successfully sent message to server for session ${sessionId}`);
        return true;
      } catch (e) {
        console.error(`Error sending message to server for session ${sessionId}:`, e);
        return false;
      }
    }

    // Load messages from server
    async loadMessagesFromServer(sessionId) {
      if (!sessionId || !this.isOnline) {
        return false;
      }

      try {
        // Get messages from server
        const response = await fetch(`/api/messages/${sessionId}`);

        // Handle 404 or other errors gracefully
        if (!response.ok) {
          if (response.status === 404) {
            console.log(`No messages found on server for session ${sessionId}`);
            return false;
          }
          throw new Error(`Server returned ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.messages || data.messages.length === 0) {
          console.log(`No messages found on server for session ${sessionId}`);
          return false;
        }

        // Convert server messages to client format
        const serverMessages = data.messages.map(msg => ({
          id: msg.metadata?.client_id || msg.message_id,
          role: msg.role,
          content: msg.content,
          agent: msg.agent_name,
          timestamp: msg.metadata?.client_timestamp || Date.parse(msg.timestamp)
        }));

        console.log(`Loaded ${serverMessages.length} messages from server for session ${sessionId}`);

        // Get any existing local messages
        const localMessages = this.getMessages(sessionId);

        // Merge messages without duplicates (keeping client IDs where possible)
        const mergedMessages = this.mergeMessages(localMessages, serverMessages);

        // Update cache and localStorage
        this.messageCache[sessionId] = mergedMessages;
        this.saveMessages(sessionId, mergedMessages);

        return true;
      } catch (e) {
        console.error(`Error loading messages from server for session ${sessionId}:`, e);
        return false;
      }
    }
  }

  // Create and merge message objects from different sources
  export function mergeMessages(localMessages, serverMessages) {
    // Create a map of existing messages by ID
    const messageMap = new Map();

    // Add local messages to the map
    localMessages.forEach(msg => {
      if (msg.id) {
        messageMap.set(msg.id, msg);
      }
    });

    // Add/update with server messages
    serverMessages.forEach(msg => {
      if (msg.id) {
        // Server message takes precedence if it exists in both
        messageMap.set(msg.id, msg);
      }
    });

    // Convert back to array and sort by timestamp
    return Array.from(messageMap.values())
      .sort((a, b) => {
        const timeA = a.timestamp || 0;
        const timeB = b.timestamp || 0;
        return timeA - timeB;
      });
  }

  // Create a message object with consistent structure
  export function createMessageObject(role, content, agentName = null) {
    return {
      id: crypto.randomUUID ? crypto.randomUUID() : generateUUID(),
      role: role,
      content: content,
      timestamp: Date.now(),
      agent: agentName
    };
  }

  // Generate a UUID for message IDs if crypto.randomUUID is not available
  export function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
      return v.toString(16);
    });
  }

  Also update radbot/web/static/js/app_main.js to add periodic synchronization:

  // Add to the init function
  function init() {
      // ... existing initialization ...

      // Schedule periodic server sync (every 60 seconds)
      if (window.chatPersistence && window.chatPersistence.serverSyncEnabled) {
          setInterval(() => {
              if (window.state && window.state.sessionId && window.navigator.onLine) {
                  console.log("Running scheduled server sync...");
                  window.chatPersistence.syncWithServer(window.state.sessionId)
                      .catch(error => console.error("Error during server sync:", error));
              }
          }, 60000); // Every minute
      }
  }

⏺ Update Todos
  ⎿  ☒ Create database schema for chat message storage
     ☒ Configure separate schema for chat history in database
     ☒ Create chat operations module with DB functions
     ☒ Add message API endpoints
     ☒ Update session API to use database instead of memory
     ☒ Update frontend to sync with server
     ☐ Update app initialization to create schema

⏺ 7. Update App Initialization to Create Schema

  Finally, modify radbot/web/app.py to initialize the database schema during startup:

  """
  Web application for RadBot interface.

  This module contains the FastAPI application and web UI routes.
  """
  import logging
  import os
  import json
  from pathlib import Path
  from typing import Dict, Any, Optional

  from fastapi import FastAPI, HTTPException, Request, Response, status
  from fastapi.responses import HTMLResponse, JSONResponse
  from fastapi.staticfiles import StaticFiles
  from starlette.middleware.sessions import SessionMiddleware

  from radbot.web.api.session import register_session_router, get_session_manager
  from radbot.web.api.sessions import register_sessions_router
  from radbot.web.api.events import register_events_router
  from radbot.web.api.agent_info import register_agent_info_router

  # Import the messages router and chat operations
  from radbot.web.api.messages import register_messages_router
  from radbot.web.db import chat_operations
  from radbot.web.db.connection import initialize_connection_pool

  # Set up logging
  logging.basicConfig(level=logging.INFO)
  logger = logging.getLogger(__name__)

  # Create FastAPI app
  app = FastAPI(
      title="RadBot Web Interface",
      description="Web interface for RadBot",
      version="1.0.0"
  )

  # Add session middleware
  app.add_middleware(
      SessionMiddleware,
      secret_key=os.getenv("SESSION_SECRET", "radbot_default_secret_change_me"),
      max_age=3600 * 24 * 30  # 30 days
  )

  # Register API routes
  register_session_router(app)
  register_sessions_router(app)
  register_events_router(app)
  register_agent_info_router(app)
  register_messages_router(app)  # Register the new messages router

  # Serve static files
  app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")

  # Home page
  @app.get("/", response_class=HTMLResponse)
  async def get_index():
      """Serve the index.html page."""
      index_path = Path(__file__).parent / "templates" / "index.html"
      if not index_path.exists():
          raise HTTPException(status_code=404, detail="Template not found")

      with open(index_path, "r") as f:
          content = f.read()

      return content

  # Get Claude templates
  @app.get("/api/claude-templates")
  async def get_claude_templates():
      """Get Claude prompt templates from config."""
      # Simple hardcoded templates for now
      templates = {
          "json": "Format your response as JSON",
          "summarize": "Summarize the following information in 3 bullet points: $input",
          "explain": "Explain the following concept in simple terms: $input",
          "research": "Research the following topic and provide a comprehensive analysis: $input"
      }

      return {"templates": templates}

  # Startup event to initialize database
  @app.on_event("startup")
  async def startup_event():
      """Initialize services on application startup."""
      logger.info("Starting RadBot web application")

      # Initialize database connection pool
      if not initialize_connection_pool():
          logger.error("Failed to initialize database connection pool")
          # We continue anyway, as the app might not require database access

      # Create database schema for chat history
      if not chat_operations.create_schema_if_not_exists():
          logger.error("Failed to create chat history schema")
          # We continue anyway, as the app might not require chat history

      logger.info("RadBot web application startup complete")

  # Shutdown event
  @app.on_event("shutdown")
  async def shutdown_event():
      """Clean up resources on application shutdown."""
      logger.info("Shutting down RadBot web application")

      # Close any remaining session runners
      session_manager = get_session_manager()
      if session_manager:
          await session_manager.close_all_sessions()

      logger.info("RadBot web application shutdown complete")
