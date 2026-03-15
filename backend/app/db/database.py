"""Database Connection and Management"""
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

from app.core.config import settings
from app.core.errors import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Database:
    """Database connection manager"""

    def __init__(self):
        self.config = {
            "host": settings.MYSQL_HOST,
            "port": settings.MYSQL_PORT,
            "user": settings.MYSQL_USER,
            "password": settings.MYSQL_PASSWORD,
            "database": settings.MYSQL_DATABASE,
            "autocommit": False,
            "pool_name": "flowsync_pool",
            "pool_size": 5,
        }
        self._connection_pool = None

    def get_connection(self):
        """Get a database connection from the pool"""
        try:
            if self._connection_pool is None:
                self._connection_pool = mysql.connector.pooling.MySQLConnectionPool(
                    **self.config
                )
            return self._connection_pool.get_connection()
        except Error as e:
            logger.error("Database connection error", extra={"error": str(e)})
            raise DatabaseError(f"Failed to connect to database: {str(e)}")

    @contextmanager
    def get_cursor(self, dictionary: bool = True):
        """Context manager for database cursor"""
        connection = None
        cursor = None
        try:
            connection = self.get_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except Error as e:
            if connection:
                connection.rollback()
            logger.error("Database operation error", extra={"error": str(e)})
            raise DatabaseError(f"Database operation failed: {str(e)}")
        finally:
            if cursor:
                cursor.close()
            if connection:
                connection.close()

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
        except Error:
            return False


# Global database instance
db = Database()
