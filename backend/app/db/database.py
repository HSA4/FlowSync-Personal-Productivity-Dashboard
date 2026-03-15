"""Database Connection and Management (PostgreSQL)"""
import psycopg2
from psycopg2 import pool, extras
from psycopg2.extras import RealDictCursor
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from app.core.config import settings
from app.core.errors import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Database:
    """PostgreSQL database connection manager"""

    def __init__(self):
        self.config = {
            "host": settings.POSTGRES_HOST,
            "port": settings.POSTGRES_PORT,
            "user": settings.POSTGRES_USER,
            "password": settings.POSTGRES_PASSWORD,
            "database": settings.POSTGRES_DATABASE,
            "sslmode": settings.POSTGRES_SSL_MODE,
        }
        self._connection_pool = None
        self._min_pool_size = 1
        self._max_pool_size = 5

    def _create_pool(self):
        """Create the connection pool if it doesn't exist"""
        if self._connection_pool is None:
            try:
                self._connection_pool = pool.SimpleConnectionPool(
                    self._min_pool_size,
                    self._max_pool_size,
                    **self.config
                )
                logger.info("PostgreSQL connection pool created")
            except psycopg2.Error as e:
                logger.error("Failed to create connection pool", extra={"error": str(e)})
                raise DatabaseError(f"Failed to create database pool: {str(e)}")

    def get_connection(self):
        """Get a database connection from the pool"""
        try:
            self._create_pool()
            return self._connection_pool.getconn()
        except psycopg2.Error as e:
            logger.error("Database connection error", extra={"error": str(e)})
            raise DatabaseError(f"Failed to connect to database: {str(e)}")

    def return_connection(self, connection):
        """Return a connection to the pool"""
        if self._connection_pool and connection:
            self._connection_pool.putconn(connection)

    @contextmanager
    def get_cursor(self, dictionary: bool = True):
        """Context manager for database cursor with RealDictCursor for dict-like results"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor_factory = RealDictCursor if dictionary else None
            cursor = connection.cursor(cursor_factory=cursor_factory)
            yield cursor
            connection.commit()
        except psycopg2.Error as e:
            if connection:
                connection.rollback()
            logger.error("Database operation error", extra={"error": str(e)})
            raise DatabaseError(f"Database operation failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                self.return_connection(connection)

    def execute_query(
        self, query: str, params: Optional[tuple] = None, fetch: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """Execute a query and return results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params or ())
            if fetch:
                return cursor.fetchall()
            return None

    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except psycopg2.Error:
            return False

    def close_all(self):
        """Close all connections in the pool"""
        if self._connection_pool:
            self._connection_pool.closeall()
            self._connection_pool = None
            logger.info("All database connections closed")


# Global database instance
db = Database()
