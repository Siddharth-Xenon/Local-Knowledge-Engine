"""Neo4j async connection manager."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession

from app.config import settings
from app.core import GraphConnectionError


class Neo4jConnection:
    """Manages Neo4j driver lifecycle and sessions."""

    _driver: AsyncDriver | None = None

    @classmethod
    async def connect(cls) -> None:
        """Initialize the Neo4j driver."""
        if cls._driver is not None:
            return

        try:
            cls._driver = AsyncGraphDatabase.driver(
                settings.neo4j_uri,
                auth=(settings.neo4j_user, settings.neo4j_password),
            )
            # Verify connectivity
            await cls._driver.verify_connectivity()
        except Exception as e:
            cls._driver = None
            raise GraphConnectionError(
                f"Failed to connect to Neo4j: {e}",
                {"uri": settings.neo4j_uri},
            )

    @classmethod
    async def disconnect(cls) -> None:
        """Close the Neo4j driver."""
        if cls._driver is not None:
            await cls._driver.close()
            cls._driver = None

    @classmethod
    def get_driver(cls) -> AsyncDriver:
        """Get the current driver instance."""
        if cls._driver is None:
            raise GraphConnectionError("Neo4j driver not initialized")
        return cls._driver

    @classmethod
    @asynccontextmanager
    async def get_session(
        cls, database: str | None = None
    ) -> AsyncGenerator[AsyncSession, None]:
        """Get a Neo4j session as an async context manager."""
        driver = cls.get_driver()
        # Default to configured query database if not specified
        db = database or settings.query_database
        session = driver.session(database=db) if db else driver.session()
        try:
            yield session
        finally:
            await session.close()


# Convenience aliases
connect = Neo4jConnection.connect
disconnect = Neo4jConnection.disconnect
get_session = Neo4jConnection.get_session
