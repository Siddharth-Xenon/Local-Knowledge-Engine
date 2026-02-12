"""Claim extractor — extracts atomic claims from LLM responses.

Primary: LangChain structured output via Node1ChatModel.
Fallback: regex-based extraction for when the LLM fails.
"""

from __future__ import annotations

import json
import logging
import re
from typing import TYPE_CHECKING

from app.pipeline.prompts import CLAIM_EXTRACTION_PROMPT
from app.verification.models import Claim

if TYPE_CHECKING:
    from langchain_core.language_models.chat_models import BaseChatModel

logger = logging.getLogger(__name__)

# Regex for extracting evidence refs like [E1], [E2]
_EVIDENCE_REF_RE = re.compile(r"\[E(\d+)\]")


class ClaimExtractor:
    """Extracts atomic claims from an LLM-generated answer.

    Uses structured output when available, falls back to regex parsing.
    """

    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def extract(
        self,
        answer_text: str,
        evidence_ids: list[str] | None = None,
    ) -> list[Claim]:
        """Extract claims from an answer.

        Tries LLM structured output first; falls back to regex on failure.
        """
        try:
            claims = await self._extract_with_llm(answer_text)
            if claims:
                return claims
            logger.warning("LLM returned no claims, falling back to regex")
        except Exception:
            logger.warning(
                "LLM claim extraction failed, falling back to regex", exc_info=True
            )

        return self._extract_with_regex(answer_text, evidence_ids or [])

    async def _extract_with_llm(self, answer_text: str) -> list[Claim]:
        """Use LangChain structured output to extract claims."""
        prompt = CLAIM_EXTRACTION_PROMPT.format(answer_text=answer_text)

        response = await self._llm.ainvoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)

        # Try to parse the JSON from the response
        claims_data = self._parse_json_response(content)
        if not claims_data:
            return []

        return [
            Claim.model_validate(c)
            for c in claims_data
            if "subject" in c and "predicate" in c and "object" in c
        ]

    @staticmethod
    def _parse_json_response(text: str) -> list[dict]:
        """Extract a JSON claims array from LLM text response."""
        # Try parsing the whole thing as JSON
        try:
            data = json.loads(text)
            if isinstance(data, dict) and "claims" in data:
                return data["claims"]
            if isinstance(data, list):
                return data
        except json.JSONDecodeError:
            pass

        # Try extracting JSON block from markdown fences
        json_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text)
        if json_match:
            try:
                data = json.loads(json_match.group(1))
                if isinstance(data, dict) and "claims" in data:
                    return data["claims"]
            except json.JSONDecodeError:
                pass

        # Try finding a JSON array
        arr_match = re.search(r"\[[\s\S]*\]", text)
        if arr_match:
            try:
                data = json.loads(arr_match.group(0))
                if isinstance(data, list):
                    return data
            except json.JSONDecodeError:
                pass

        return []

    @staticmethod
    def _extract_with_regex(
        answer_text: str,
        evidence_ids: list[str],
    ) -> list[Claim]:
        """Regex fallback: split into sentences, extract evidence refs."""
        sentences = re.split(r"(?<=[.!?])\s+", answer_text.strip())
        claims: list[Claim] = []

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence or len(sentence) < 10:
                continue

            refs = [f"E{m}" for m in _EVIDENCE_REF_RE.findall(sentence)]
            clean = _EVIDENCE_REF_RE.sub("", sentence).strip()

            claims.append(
                Claim(
                    subject=clean[:50] if len(clean) > 50 else clean,
                    predicate="states",
                    object=clean,
                    evidence_refs=refs,
                    source_statement=sentence,
                )
            )

        return claims
