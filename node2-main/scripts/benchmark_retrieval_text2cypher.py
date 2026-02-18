import asyncio
import logging
import os
import sys
import time
from typing import Any, Dict, List

# Add project root to path to allow imports from app
sys.path.append(os.getcwd())

from langsmith import traceable
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import Text2CypherRetriever
from neo4j_graphrag.schema import get_schema

from app.config import settings
from app.inference.factory import LLMFactory
from app.inference.llm_adapter import Node1LLM
from app.inference.types import ThinkingLevel

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# Configure LangSmith
if settings.langsmith_tracing:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project


# Benchmark Queries
QUERIES = questions = [
    # Performance / Simple Retrieval
    "When did Apple’s stock reach its lowest price during the COVID-19 pandemic?",
    "What was Apple’s lowest opening and closing stock price during the pandemic?",
    "Summarize Apple’s stock price trend during the first half of 2020.",
    # Retrieval & Grounding
    "What macroeconomic factors during COVID-19 affected Apple’s stock price?",
    "Describe Apple’s stock price movement between February and September 2020.",
    "How did Apple’s product launch delays affect its stock price in 2020?",
    # Reasoning with Evidence
    "Did COVID-19 cause long-term damage to Apple’s stock value?",
    "Compare Apple and Microsoft stock behavior during COVID-19 based on the document.",
    "Why did Apple’s stock recover after the March 2020 crash according to the document?",
    # Hallucination Stress Tests
    "What was Apple’s stock price on April 15, 2020?",
    "Did Apple’s stock increase specifically because of government stimulus packages?",
    "Which Apple executive decisions caused the biggest stock drop during COVID-19?",
    # Abstention & Safety
    "How will future pandemics affect Apple’s stock price?",
    "What did financial analysts say about Apple’s stock performance in 2022?",
    "Predict Apple’s stock price in the next global crisis based on this document.",
]


@traceable(run_type="chain", name="Text2Cypher Benchmark")
async def run_benchmark():
    logger.info("Starting Text2Cypher Benchmarking (Concurrent)...")

    # Connect to Neo4j (Sync Driver for simplicity in benchmark)
    URI = settings.neo4j_uri
    AUTH = (settings.neo4j_user, settings.neo4j_password)
    DB = settings.query_database

    try:
        driver = GraphDatabase.driver(URI, auth=AUTH)
        logger.info("Connected to Neo4j.")
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {e}")
        return

    # Define LLM Configurations to test
    llm_configs = [
        {
            "name": "Deepseek r1",
            "model": "deepseek-r1:8b-llama-distill-q4_K_M",
            "type": "node1",
            # "thinking_level": ThinkingLevel.LOW,
        },
        # {
        #     "name": "Gemini Pro",
        #     "model": "gemini-3-pro-preview",
        #     "type": "gemini",
        #     "thinking_level": ThinkingLevel.LOW,
        # },
        # {
        #     "name": "Gemini Pro",
        #     "model": "gemini-3-pro-preview",
        #     "type": "gemini",
        #     "thinking_level": ThinkingLevel.LOW,
        # },
    ]

    results = []
    sem = asyncio.Semaphore(1)  # Limit concurrency to 5

    try:
        # Pre-fetch schema once to ensure fair comparison if cached (though library fetches it)
        # Note: Text2CypherRetriever fetches schema internally during init or execution usually.
        # We pass it explicitly if possible to save time, but Factory does standard init.

        for config in llm_configs:
            logger.info(f"--- Testing Config: {config['name']} ---")

            try:
                # 1. Create LLM
                if config["type"] == "node1":
                    llm = Node1LLM(model_name=config["model"], timeout=120)
                else:
                    llm = LLMFactory.create(
                        model_name=config["model"],
                        thinking_level=config["thinking_level"],
                    )

                # 2. Create Retriever
                # We replicate Factory logic here to use our sync driver
                examples = [
                    """
                    Question: "What companies did Apple acquire?"
                    Cypher: MATCH (a:Entity {name: 'Apple'})-[r:RELATED]->(b:Entity) WHERE r.type = 'ACQUIRED' RETURN b.name
                    """,
                    """
                    Question: "How are Apple and Steve Jobs related?"
                    Cypher: MATCH (a:Entity {name: 'Apple'})-[r:RELATED]-(b:Entity {name: 'Steve Jobs'}) RETURN r.type, r.description""",
                    "Make sure you consider relationship.type to understand the relationship between nodes.",
                ]

                retriever = Text2CypherRetriever(
                    driver=driver,
                    llm=llm,
                    examples=examples,
                    neo4j_database=DB,
                    # We let it fetch schema or pass it if we wanted to optimization
                    neo4j_schema=get_schema(driver, database=settings.query_database),
                )

                # 3. Run Queries Concurrently
                tasks = []
                for q in QUERIES:
                    tasks.append(benchmark_query(sem, retriever, q, config, results))

                await asyncio.gather(*tasks)

            except Exception as e:
                logger.error(f"Failed configuration {config['name']}: {e}")

    finally:
        driver.close()
        logger.info("Neo4j driver closed.")

    # Print Summary
    print("\n" + "=" * 80)
    print(f"{'LLM':<15} | {'Query':<40} | {'Time(s)':<8} | {'Items':<5} | {'Cypher'}")
    print("=" * 80)
    for r in results:
        q_short = (r["query"][:37] + "...") if len(r["query"]) > 37 else r["query"]
        cypher_short = (
            (r["cypher"][:40] + "...")
            if r["cypher"] and len(r["cypher"]) > 40
            else r["cypher"]
        )
        print(
            f"{r['llm']:<15} | {q_short:<40} | {r['time_sec']:<8} | {r['total_results']:<5} | {cypher_short}"
        )
    print("=" * 80)


async def benchmark_query(sem, retriever, q, config, results):
    async with sem:
        await asyncio.to_thread(run_query, retriever, q, config, results)


def format_result_items(items):
    formatted_items = []
    for item in items:
        content = getattr(item, "content", None) or str(item)
        formatted_items.append(content)
    return formatted_items


@traceable(run_type="tool", name="Run Query")
def run_query(retriever, q, config, results):
    logger.info(f"Query: {q}")
    start_time = time.time()
    try:
        # search() returns RetrieverResult
        result = retriever.search(query_text=q)
        duration = time.time() - start_time

        # Extract generated cypher if exposed (might depend on implementation)
        # Text2CypherRetriever usually returns items, metadata might contain cypher
        generated_cypher = (
            result.metadata.get("cypher", "N/A") if result.metadata else "N/A"
        )
        num_results = len(result.items)

        results.append(
            {
                "llm": config["name"],
                "query": q,
                "time_sec": round(duration, 4),
                "total_results": num_results,
                "cypher": generated_cypher,
                "error": None,
                "answers": format_result_items(result.items),
            }
        )
        logger.info(f"  -> Found {num_results} items in {duration:.2f}s")
        return results

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"  -> Error: {e}")
        results.append(
            {
                "llm": config["name"],
                "query": q,
                "time_sec": round(duration, 4),
                "total_results": 0,
                "cypher": "ERROR",
                "error": str(e),
            }
        )


if __name__ == "__main__":
    asyncio.run(run_benchmark())
