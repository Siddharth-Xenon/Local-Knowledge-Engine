"""Quick diagnostic: what's in the Neo4j database?"""

import asyncio
from app.graph.connection import connect, disconnect, get_session
from app.graph.repository import GraphRepository


async def main():
    await connect()

    # 1. Count nodes by label
    async with get_session() as session:
        result = await session.run(
            "MATCH (n) RETURN labels(n) AS labels, count(*) AS cnt ORDER BY cnt DESC"
        )
        records = await result.data()
        print("=== NODE COUNTS BY LABEL ===")
        for r in records:
            labels = r["labels"]
            cnt = r["cnt"]
            print(f"  {labels}: {cnt}")

    # 2. Test get_embeddable_nodes
    nodes = await GraphRepository.get_embeddable_nodes(["Rule", "Policy"])
    print(f"\n=== get_embeddable_nodes returned {len(nodes)} nodes ===")
    for n in nodes[:3]:
        node_id = n.get("id", "MISSING_ID")
        node_labels = n.get("_labels", [])
        keys = [k for k in n.keys() if k != "_labels"]
        print(f"  id={node_id}, labels={node_labels}, fields={keys}")

    # 3. Raw look at Rule nodes
    async with get_session() as session:
        result = await session.run("MATCH (n:Rule) RETURN n LIMIT 3")
        records = await result.data()
        print(f"\n=== RAW Rule nodes (first 3) ===")
        for r in records:
            props = dict(r["n"])
            print(f"  {props}")

    await disconnect()


asyncio.run(main())
