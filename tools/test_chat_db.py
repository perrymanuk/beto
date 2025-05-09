#!/usr/bin/env python
"""
Test script for chat database functionality.
This script tests the chat history database connection and operations.
"""

import sys
import uuid
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to import radbot modules
sys.path.insert(0, '..')

try:
    # Import database modules
    from radbot.web.db import chat_operations
    from radbot.web.db.connection import initialize_connection_pool, CHAT_SCHEMA

    def test_db_connection():
        """Test database connection."""
        logger.info("Testing database connection...")
        result = initialize_connection_pool()
        if result:
            logger.info("✅ Database connection successful")
        else:
            logger.error("❌ Database connection failed")
        return result

    def test_schema_creation():
        """Test schema creation."""
        logger.info("Testing schema creation...")
        result = chat_operations.create_schema_if_not_exists()
        if result:
            logger.info(f"✅ Schema '{CHAT_SCHEMA}' created or already exists")
        else:
            logger.error(f"❌ Failed to create schema '{CHAT_SCHEMA}'")
        return result

    def test_session_operations():
        """Test session operations."""
        logger.info("Testing session operations...")
        
        # Generate a test session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created test session ID: {session_id}")
        
        # Create session
        session_name = f"Test Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        logger.info(f"Creating session '{session_name}'...")
        result = chat_operations.create_or_update_session(
            session_id=session_id,
            name=session_name,
            user_id="test_user"
        )
        
        if result:
            logger.info("✅ Session created successfully")
        else:
            logger.error("❌ Session creation failed")
            return False
        
        # List sessions
        logger.info("Listing sessions...")
        sessions = chat_operations.list_sessions()
        if sessions:
            logger.info(f"✅ Found {len(sessions)} sessions:")
            for session in sessions[:5]:  # Show first 5 sessions
                logger.info(f"  - {session['session_id']}: {session['name']}")
        else:
            logger.error("❌ No sessions found or listing failed")
            return False
        
        # Verify our test session is in the list
        test_session = next((s for s in sessions if s["session_id"] == session_id), None)
        if test_session:
            logger.info(f"✅ Found test session: {test_session['name']}")
        else:
            logger.error("❌ Test session not found in listing")
            return False
        
        return True

    def test_message_operations():
        """Test message operations."""
        logger.info("Testing message operations...")
        
        # Generate a test session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created test session ID: {session_id}")
        
        # Create session
        session_name = f"Message Test Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        chat_operations.create_or_update_session(
            session_id=session_id,
            name=session_name,
            user_id="test_user"
        )
        
        # Add a user message
        logger.info("Adding user message...")
        user_msg_id = chat_operations.add_message(
            session_id=session_id,
            role="user",
            content="Hello, this is a test message from the user",
            user_id="test_user"
        )
        
        if user_msg_id:
            logger.info(f"✅ User message added with ID: {user_msg_id}")
        else:
            logger.error("❌ Failed to add user message")
            return False
        
        # Add an assistant message
        logger.info("Adding assistant message...")
        asst_msg_id = chat_operations.add_message(
            session_id=session_id,
            role="assistant",
            content="Hello, this is a response from the assistant",
            agent_name="TEST_AGENT"
        )
        
        if asst_msg_id:
            logger.info(f"✅ Assistant message added with ID: {asst_msg_id}")
        else:
            logger.error("❌ Failed to add assistant message")
            return False
        
        # Get message count
        msg_count = chat_operations.get_session_message_count(session_id)
        logger.info(f"Session has {msg_count} messages")
        
        # Get messages
        logger.info("Getting messages...")
        messages = chat_operations.get_messages_by_session_id(session_id)
        
        if messages and len(messages) == 2:
            logger.info(f"✅ Retrieved {len(messages)} messages:")
            for msg in messages:
                logger.info(f"  - {msg['role']}: {msg['content'][:50]}...")
        else:
            logger.error(f"❌ Expected 2 messages, got {len(messages) if messages else 0}")
            return False
        
        return True

    def test_session_reset():
        """Test session reset."""
        logger.info("Testing session reset...")
        
        # Generate a test session ID
        session_id = str(uuid.uuid4())
        logger.info(f"Created test session ID: {session_id}")
        
        # Create session
        session_name = f"Reset Test Session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        chat_operations.create_or_update_session(
            session_id=session_id,
            name=session_name,
            user_id="test_user"
        )
        
        # Add some messages
        for i in range(5):
            chat_operations.add_message(
                session_id=session_id,
                role="user" if i % 2 == 0 else "assistant",
                content=f"Test message {i+1}",
                user_id="test_user"
            )
        
        # Verify messages exist
        count_before = chat_operations.get_session_message_count(session_id)
        logger.info(f"Session has {count_before} messages before reset")
        
        if count_before != 5:
            logger.error(f"❌ Expected 5 messages, got {count_before}")
            return False
        
        # Reset session (delete all messages)
        logger.info("Resetting session (deleting all messages)...")
        from radbot.web.db.connection import get_chat_db_connection, get_chat_db_cursor
        
        try:
            with get_chat_db_connection() as conn:
                with get_chat_db_cursor(conn, commit=True) as cursor:
                    cursor.execute(f"""
                        DELETE FROM {CHAT_SCHEMA}.chat_messages
                        WHERE session_id = %s;
                    """, (uuid.UUID(session_id),))
            
            # Verify messages were deleted
            count_after = chat_operations.get_session_message_count(session_id)
            logger.info(f"Session has {count_after} messages after reset")
            
            if count_after == 0:
                logger.info("✅ Session reset successful")
                return True
            else:
                logger.error(f"❌ Expected 0 messages after reset, got {count_after}")
                return False
        except Exception as e:
            logger.error(f"❌ Error during session reset: {e}")
            return False

    def run_tests():
        """Run all tests."""
        logger.info("=== CHAT DATABASE TESTS ===")
        
        # Run tests in sequence
        if not test_db_connection():
            logger.error("Database connection failed. Stopping tests.")
            return False
        
        if not test_schema_creation():
            logger.error("Schema creation failed. Stopping tests.")
            return False
        
        session_results = test_session_operations()
        message_results = test_message_operations()
        reset_results = test_session_reset()
        
        # Report results
        logger.info("\n=== TEST RESULTS ===")
        logger.info(f"Database Connection: {'✅ PASS' if True else '❌ FAIL'}")
        logger.info(f"Schema Creation: {'✅ PASS' if True else '❌ FAIL'}")
        logger.info(f"Session Operations: {'✅ PASS' if session_results else '❌ FAIL'}")
        logger.info(f"Message Operations: {'✅ PASS' if message_results else '❌ FAIL'}")
        logger.info(f"Session Reset: {'✅ PASS' if reset_results else '❌ FAIL'}")
        
        overall = session_results and message_results and reset_results
        logger.info(f"\nOverall Result: {'✅ PASS' if overall else '❌ FAIL'}")
        
        return overall

    if __name__ == "__main__":
        success = run_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Make sure you are running this script from the project root directory")
    sys.exit(1)
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    sys.exit(1)