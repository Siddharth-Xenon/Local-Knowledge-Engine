import asyncio
from unittest.mock import MagicMock
from app.pipeline.graph import build_pipeline
from app.pipeline.nodes import PipelineNodes


async def main():
    # Mock dependencies for PipelineNodes
    retrieval_service = MagicMock()
    llm = MagicMock()
    claim_extractor = MagicMock()
    verifier = MagicMock()
    policy = MagicMock()

    # Create PipelineNodes instance
    nodes = PipelineNodes(
        retrieval_service=retrieval_service,
        llm=llm,
        claim_extractor=claim_extractor,
        verifier=verifier,
        policy=policy,
    )

    # Build the graph
    app = build_pipeline(nodes)

    # Generate Mermaid Image
    try:
        image_data = app.get_graph().draw_mermaid_png()
        with open("pipeline_graph.png", "wb") as f:
            f.write(image_data)
        print("Successfully saved pipeline_graph.png")
    except Exception as e:
        print(f"Failed to generate PNG using built-in method: {e}")
        # Fallback to mermaid text if PNG fails (e.g., due to missing dependencies)
        try:
            mermaid_text = app.get_graph().draw_mermaid()
            with open("pipeline_graph.mmd", "w") as f:
                f.write(mermaid_text)
            print("Saved pipeline_graph.mmd (text format) as fallback.")
        except Exception as e2:
            print(f"Failed to generate mermaid text: {e2}")


if __name__ == "__main__":
    asyncio.run(main())
