import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.connection import connect, disconnect, get_session
import logging

logging.basicConfig(level=logging.INFO)


async def main():
    print("Testing connection...")
    try:
        await connect()
        print("Connected successfully!")

        async with get_session() as session:
            result = await session.run("RETURN 1 as val")
            record = await result.single()
            print(f"Query result: {record['val']}")

    except Exception as e:
        print(f"Connection failed: {e}")
    finally:
        await disconnect()
        print("Disconnected.")


if __name__ == "__main__":
    if os.name == "nt":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
