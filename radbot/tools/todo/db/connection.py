"""
Database connection handling for the Todo Tool.

This module encapsulates database connection management
using the psycopg2 library with connection pooling.
"""

import os
import logging
import psycopg2
import psycopg2.pool
import psycopg2.extras  # For RealDictCursor
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

# Load from config.yaml or fall back to environment variables
DB_NAME = database_config.get("db_name") or os.getenv("POSTGRES_DB")
DB_USER = database_config.get("user") or os.getenv("POSTGRES_USER")
DB_PASSWORD = database_config.get("password") or os.getenv("POSTGRES_PASSWORD")
DB_HOST = database_config.get("host") or os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = database_config.get("port") or os.getenv("POSTGRES_PORT", "5432")

# Basic validation
if not all([DB_NAME, DB_USER, DB_PASSWORD]):
    error_msg = "Database credentials (database.db_name, database.user, database.password) must be set in config.yaml or as environment variables (POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD)"
    logger.error(error_msg)
    raise ValueError(error_msg)

# Register UUID adapter for psycopg2
psycopg2.extensions.register_adapter(uuid.UUID, lambda u: psycopg2.extensions.adapt(str(u)))

# Configure and initialize the connection pool
# Adjust minconn and maxconn based on expected load
MIN_CONN = 1
MAX_CONN = 5  # Start conservatively

try:
    pool = psycopg2.pool.ThreadedConnectionPool(
        minconn=MIN_CONN,
        maxconn=MAX_CONN,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    logger.info(f"Database connection pool initialized (Min: {MIN_CONN}, Max: {MAX_CONN})")
    logger.info(f"Connected to PostgreSQL database '{DB_NAME}' at {DB_HOST}:{DB_PORT}")
except psycopg2.OperationalError as e:
    logger.error(f"FATAL: Could not connect to database: {e}")
    # Handle fatal error appropriately - maybe exit or raise
    raise


@contextmanager
def get_db_connection() -> Generator[psycopg2.extensions.connection, None, None]:
    """Provides a database connection from the pool, managing cleanup."""
    conn = None
    try:
        conn = pool.getconn()
        yield conn
    except psycopg2.Error as e:
        # Log or handle pool errors if necessary
        logger.error(f"Error getting connection from pool: {e}")
        raise  # Re-raise the original psycopg2 error
    finally:
        if conn:
            pool.putconn(conn)  # Return connection to the pool


@contextmanager
def get_db_cursor(conn: psycopg2.extensions.connection, commit: bool = False) -> Generator[psycopg2.extensions.cursor, None, None]:
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