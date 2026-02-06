import pytest

from app.graph.connection import Neo4jConnection


@pytest.mark.asyncio
async def test_neo4j_connection():
    """Test that we can connect to Neo4j and run a simple query."""
    # 1. Connect
    print("\nAttempting to connect to Neo4j...")
    await Neo4jConnection.connect()

    try:
        # 2. Get a session and run a query
        print("Getting session and running query...")
        async with Neo4jConnection.get_session() as session:
            result = await session.run("RETURN 1 AS value")
            record = await result.single()
            assert record["value"] == 1
            print("Successfully connected to Neo4j and executed query!")

    finally:
        # 3. Disconnect
        print("Disconnecting...")
        await Neo4jConnection.disconnect()
