"""Graph Builder Service for extracting knowledge graph from documents."""

import asyncio
import json
import logging
from typing import Any

from pydantic import BaseModel, Field
from neo4j_graphrag.llm.base import LLMInterface
from app.graph.connection import get_session

# from app.inference.llm_adapter import Node1LLM

logger = logging.getLogger(__name__)


class Entity(BaseModel):
    """Represents an extracted entity."""

    name: str = Field(..., description="Name of the entity")
    label: str = Field(
        ...,
        description="Type of the entity (Person, Organization, Location, Concept)",
        validation_alias="type",
    )

    class Config:
        populate_by_name = True

    description: str | None = Field(None, description="Brief description or context")


class Relationship(BaseModel):
    """Represents a relationship between two entities."""

    source: str = Field(..., description="Name of the source entity")
    target: str = Field(..., description="Name of the target entity")
    type: str = Field(
        ...,
        description="Type of relationship (e.g., WORKS_FOR, LOCATED_IN, etc.)",
    )
    description: str | None = Field(None, description="Context for the relationship")


class GraphExtraction(BaseModel):
    """Container for extracted graph elements."""

    entities: list[Entity] = Field(default_factory=list)
    relationships: list[Relationship] = Field(default_factory=list)


class GraphBuilderService:
    """Service to extract and build knowledge graph from documents using Node 1 LLM."""

    def __init__(self, llm: LLMInterface | None = None, database: str | None = None):
        self.llm = llm
        self.database = database
        # System prompt to guide the LLM
        schema = json.dumps(GraphExtraction.model_json_schema(), indent=2)
        self.system_prompt = (
            """You are a Knowledge Graph expert. Your task is to extract meaningful
        entities and relationships from the provided text chunk.\n
        Your goal is to identify and categorize entities while ensuring that specific data types such as dates, numbers, revenues, and other non-entity information are not extracted as separate nodes.
        Instead, treat these as properties associated with the relevant entities.
        1. Identify entities (Person, Organization, Location, Concept, Event, Technology).\n"
        2. Identify relationships between these entities.\n"
        3. Return ONLY a valid JSON object matching the following schema:\n"""
            f"{schema}\n"
            "4. Do not include any explanation or markdown formatting."
        )

    async def process_document(self, filename: str) -> dict[str, Any]:
        """Process all chunks for a given document filename."""
        logger.info(f"Starting graph build for document: {filename}")

        # 1. Fetch chunks for the document from Neo4j
        chunks = await self._fetch_chunks(filename)
        if not chunks:
            logger.warning(f"No chunks found for {filename}")
            return {"status": "skipped", "reason": "no_chunks"}

        total_entities = 0
        total_relationships = 0

        # 2. Process chunks concurrently
        # Limit concurrency to avoid overloading Node 1 (or OpenAI rate limits)
        semaphore = asyncio.Semaphore(1)  # Adjust based on LLM/DB limits

        async def process_chunk(chunk):
            async with semaphore:
                try:
                    extraction = await self._extract_entities(chunk["text"])
                    if extraction:
                        await self._save_graph(extraction, chunk["id"], chunk["source"])
                        return len(extraction.entities), len(extraction.relationships)
                except Exception as e:
                    logger.error(f"Failed to process chunk {chunk['id']}: {e}")
                return 0, 0

        results = await asyncio.gather(*[process_chunk(chunk) for chunk in chunks])

        for entities, relationships in results:
            total_entities += entities
            total_relationships += relationships

        logger.info(
            f"Graph build complete for {filename}. "
            f"Extracted {total_entities} entities, {total_relationships} relationships."
        )
        return {
            "status": "success",
            "entities": total_entities,
            "relationships": total_relationships,
        }

    async def _fetch_chunks(self, filename: str) -> list[dict]:
        """Retrieve chunks for a file from Neo4j."""
        query = """
        MATCH (d:Document {filename: $filename})-[:HAS_CHUNK]->(c:Element)
        RETURN c.id as id, c.text as text, c.source as source
        """
        async with get_session(database=self.database) as session:
            result = await session.run(query, filename=filename)
            return [record.data() async for record in result]

    async def _extract_entities(self, text: str) -> GraphExtraction | None:
        """Call LLM to extract entities from text."""
        try:
            # We use a simple prompt for now.
            # Ideally Node 1 supports structured output, but we'll ask for JSON text.
            prompt = f"Extract graph from this text:\n\n{text}"

            response = await self.llm.ainvoke(
                input=prompt, system_instruction=self.system_prompt
            )

            # Clean up response (remove markdown code blocks if present)
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]

            data = json.loads(content)
            return GraphExtraction(**data)

        except json.JSONDecodeError:
            logger.warning("LLM returned invalid JSON")
            return None
        except Exception as e:
            logger.error(f"LLM extraction failed: {e}")
            return None

    async def _save_graph(self, data: GraphExtraction, chunk_id: str, source: str):
        """Write extracted entities and relationships to Neo4j."""
        query = """
        MATCH (c:Element {id: $chunk_id})
        
        // 1. Merge Entities
        // We use a list comprehension in Cypher to handle the UNWIND cleanly
        FOREACH (entity IN $entities |
            MERGE (e:Entity {name: entity.name})
            ON CREATE SET 
                e.label = entity.label, 
                e.description = entity.description, 
                e.source = $source
            MERGE (c)-[:MENTIONS]->(e)
        )

        // 2. Merge Relationships
        // Since we can't MATCH inside FOREACH, we use UNWIND for relationships
        // But we need to make sure we don't drop the cardinality if relationships is empty
        WITH c
        UNWIND 
            CASE 
                WHEN size($relationships) > 0 THEN $relationships 
                ELSE [null] 
            END AS rel
        
        WITH c, rel
        WHERE rel IS NOT NULL
        MERGE (source:Entity {name: rel.source})
        ON CREATE SET source.label = "Unknown", source.source = $source
        MERGE (target:Entity {name: rel.target})
        ON CREATE SET target.label = "Unknown", target.source = $source
        
        MERGE (source)-[r:RELATED {type: rel.type}]->(target)
        SET r.description = rel.description
        """

        # Convert Pydantic models to dicts
        params = {
            "chunk_id": chunk_id,
            "source": source,
            "entities": [e.model_dump() for e in data.entities],
            "relationships": [r.model_dump() for r in data.relationships],
        }

        async with get_session(database=self.database) as session:
            await session.execute_write(lambda tx: tx.run(query, params))
