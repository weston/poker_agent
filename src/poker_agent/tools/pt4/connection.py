"""PostgreSQL connection management for PT4 database."""

from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

import psycopg
from psycopg.rows import dict_row

from ...config import get_settings


class PT4Connection:
    """Manages connection to PokerTracker 4 PostgreSQL database."""

    def __init__(self, connection_string: str | None = None):
        """
        Initialize PT4 connection manager.

        Args:
            connection_string: PostgreSQL connection string.
                             If not provided, uses settings.
        """
        if connection_string is None:
            settings = get_settings()
            connection_string = settings.pt4_connection_string
        self.connection_string = connection_string

    @asynccontextmanager
    async def get_connection(
        self,
    ) -> AsyncGenerator[psycopg.AsyncConnection, None]:
        """Get an async database connection."""
        async with await psycopg.AsyncConnection.connect(
            self.connection_string, row_factory=dict_row
        ) as conn:
            yield conn

    async def execute_query(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """
        Execute a query and return results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of row dictionaries
        """
        async with self.get_connection() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, params)
                rows = await cur.fetchall()
                return [dict(row) for row in rows]

    async def test_connection(self) -> bool:
        """Test if database connection works."""
        try:
            async with self.get_connection() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT 1")
                    return True
        except Exception:
            return False


# Singleton connection instance
_connection: PT4Connection | None = None


def get_pt4_connection() -> PT4Connection:
    """Get the PT4 connection singleton."""
    global _connection
    if _connection is None:
        _connection = PT4Connection()
    return _connection
