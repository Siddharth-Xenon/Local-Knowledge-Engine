import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.connection import connect, disconnect, Neo4jConnection
import logging

logging.basicConfig(level=logging.INFO)


async def main():
    print("Verifying ingestion...")
    try:
        await connect()
        driver = Neo4jConnection.get_driver()

        async with driver.session(database="graphrag") as session:
            # List ALL documents
            print("--- Listing All Documents ---")
            result = await session.run("""
                MATCH (d:Document) 
                RETURN d.filename, d.ingested_at, count { (d)-[:HAS_CHUNK]->() } as chunks
                LIMIT 10
            """)
            records = [record async for record in result]
            if records:
                for r in records:
                    print(f"[FOUND] {r['d.filename']} | Chunks: {r['chunks']}")
            else:
                print("[NONE] No Document nodes found.")

    except Exception as e:
        print(f"Verification failed: {e}")
    finally:
        await disconnect()


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
