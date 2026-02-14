import re
import logging

logger = logging.getLogger(__name__)


class TextHighlighter:
    """
    Aligns structured claims with the natural language answer text.
    Uses Jaccard similarity to find the best matching sentence for each claim.
    """

    def align_claims(self, text: str, claims: list[dict]) -> list[dict]:
        """
        Augments claims with 'highlight_start' and 'highlight_end' indices.

        Args:
            text: The full answer text.
            claims: List of claim dictionaries (must have subject, predicate, object).

        Returns:
            The list of claims with added highlight indices.
        """
        sentences = self._split_sentences(text)

        for claim in claims:
            # Construct a query representation of the claim
            claim_text = f"{claim.get('subject', '')} {claim.get('predicate', '')} {claim.get('object', '')}"
            claim_tokens = self._tokenize(claim_text)

            best_score = 0.0
            best_span = None

            for start, end, sent_text in sentences:
                sent_tokens = self._tokenize(sent_text)
                score = self._jaccard_similarity(claim_tokens, sent_tokens)

                if score > best_score:
                    best_score = score
                    best_span = (start, end)

            # Threshold to avoid garbage formatting if no match found
            # 0.1 is very improved permissive, ensuring we catch partial matches
            if best_score > 0.1 and best_span:
                claim["highlight_start"] = best_span[0]
                claim["highlight_end"] = best_span[1]
                logger.debug(
                    f"Aligned claim {claim.get('claim_id')} to sentence with score {best_score:.2f}"
                )
            else:
                claim["highlight_start"] = None
                claim["highlight_end"] = None
                logger.warning(
                    f"Could not align claim {claim.get('claim_id')} (best score: {best_score:.2f})"
                )

        return claims

    def _split_sentences(self, text: str) -> list[tuple[int, int, str]]:
        """
        Splits text into sentences, returning (start, end, text) tuples.
        Adjusts indices to exclude leading/trailing whitespace.
        """
        # Matches punctuation followed by space or end of string
        matches = list(re.finditer(r"[^.!?]+[.!?]+", text))

        results = []
        if matches:
            for m in matches:
                raw_text = m.group()
                stripped = raw_text.strip()
                if not stripped:
                    continue

                # Calculate offsets for stripped text
                leading_spaces = raw_text.find(stripped)
                start = m.start() + leading_spaces
                end = start + len(stripped)

                results.append((start, end, stripped))

            last_match_end = matches[-1].end()
        else:
            last_match_end = 0

        # Handle trailing text without punctuation
        if last_match_end < len(text):
            remainder_raw = text[last_match_end:]
            remainder_stripped = remainder_raw.strip()
            if remainder_stripped:
                leading_spaces = remainder_raw.find(remainder_stripped)
                start = last_match_end + leading_spaces
                end = start + len(remainder_stripped)
                results.append((start, end, remainder_stripped))

        # If no results found (e.g. empty or whitespace), return whole text as fallback if not empty
        if not results and text.strip():
            vals = text.strip()
            start = text.find(vals)
            return [(start, start + len(vals), vals)]

        return results

    def _tokenize(self, text: str) -> set[str]:
        """Simple word tokenizer."""
        # Remove punctuation and lowercase
        clean = re.sub(r"[^\w\s]", "", text.lower())
        return set(clean.split())

    def _jaccard_similarity(self, set1: set[str], set2: set[str]) -> float:
        """Calculates Jaccard similarity between two sets of tokens."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union
