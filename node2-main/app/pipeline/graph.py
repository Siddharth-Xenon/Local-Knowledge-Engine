"""LangGraph state machine — compiles the verification pipeline.

Defines the graph topology: retrieve → generate → extract → verify → decide
with conditional routing for regeneration, abstention, and uncertainty.
"""

from __future__ import annotations

import logging
from typing import Any

from langgraph.graph import END, StateGraph

from app.pipeline.nodes import PipelineNodes
from app.pipeline.state import PipelineState
from app.verification.models import PolicyDecision

logger = logging.getLogger(__name__)


def build_pipeline(
    nodes: PipelineNodes,
) -> Any:
    """Build and compile the LangGraph verification pipeline.

    Returns a compiled graph that can be invoked with:
        result = await graph.ainvoke({"query": "..."})
    """
    graph = StateGraph(PipelineState)

    # ── Register nodes ──
    graph.add_node("retrieve", nodes.retrieve)
    graph.add_node("generate", nodes.generate)
    graph.add_node("extract_claims", nodes.extract_claims)
    graph.add_node("verify", nodes.verify)
    graph.add_node("regenerate", nodes.regenerate)
    graph.add_node("add_uncertainty", nodes.add_uncertainty)
    graph.add_node("create_response", nodes.create_response)
    graph.add_node("abstain", nodes.abstain)

    # ── Linear edges ──
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "extract_claims")
    graph.add_edge("extract_claims", "verify")

    # ── Conditional routing from verify ──
    graph.add_conditional_edges(
        "retrieve",
        nodes.decide_generate,
        {"generate": "generate", "abstain": "abstain"},
    )
    graph.add_conditional_edges(
        "verify",
        nodes.decide,
        {
            PolicyDecision.SERVE.value: "create_response",
            PolicyDecision.REGENERATE.value: "regenerate",
            PolicyDecision.BLOCK.value: "abstain",
            PolicyDecision.ADD_UNCERTAINTY.value: "add_uncertainty",
        },
    )

    # ── Regeneration loop ──
    graph.add_edge("regenerate", "generate")

    # ── Terminal edges ──
    graph.add_edge("create_response", END)
    graph.add_edge("abstain", END)
    graph.add_edge("add_uncertainty", "create_response")

    # ── Entry point ──
    graph.set_entry_point("retrieve")

    compiled = graph.compile()
    logger.info("Verification pipeline compiled successfully")
    return compiled
