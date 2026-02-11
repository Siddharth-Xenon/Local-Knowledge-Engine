"""Check Neo4j version and vector index support."""

import asyncio
from app.graph.connection import connect, disconnect, get_session


async def main():
    await connect()
    async with get_session() as session:
        # Check version
        result = await session.run(
            "CALL dbms.components() YIELD name, versions RETURN name, versions"
        )
        records = await result.data()
        for r in records:
            print(f"Component: {r['name']}, Versions: {r['versions']}")

        # Check if vector indexes are supported
        try:
            result = await session.run(
                "SHOW INDEXES YIELD type, name WHERE type = 'VECTOR'"
            )
            records = await result.data()
            print(f"\nExisting vector indexes: {len(records)}")
            for r in records:
                print(f"  {r}")
        except Exception as e:
            print(f"\nVector index check failed: {e}")

    await disconnect()


asyncio.run(main())
