import unittest
from app.services.text_highlighter import TextHighlighter


class TestTextHighlighter(unittest.TestCase):
    def setUp(self):
        self.highlighter = TextHighlighter()

    def test_exact_match(self):
        """Test exact mapping of a claim to a sentence."""
        text = "Alice owns a cat. Bob owns a dog."
        claims = [
            {
                "claim_id": "1",
                "subject": "Alice",
                "predicate": "owns",
                "object": "a cat",
            }
        ]

        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        self.assertIsNotNone(c["highlight_start"])
        # "Alice owns a cat." is index 0 to 17
        self.assertEqual(
            text[c["highlight_start"] : c["highlight_end"]], "Alice owns a cat."
        )

    def test_partial_match_with_noise(self):
        """Test matching when sentence has extra words (noise)."""
        text = "Alice actually owns a very cute cat. Bob owns a dog."
        # Claim omits "actually" and "very cute"
        claims = [
            {"claim_id": "1", "subject": "Alice", "predicate": "owns", "object": "cat"}
        ]

        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        matched_text = text[c["highlight_start"] : c["highlight_end"]]
        self.assertEqual(matched_text, "Alice actually owns a very cute cat.")

    def test_passive_voice_match(self):
        """Test matching passive voice sentence against active claim."""
        text = "The cat is owned by Alice."
        claims = [
            {"claim_id": "1", "subject": "Alice", "predicate": "owns", "object": "cat"}
        ]

        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        # Overlap: {alice, owns, cat} vs {the, cat, is, owned, by, alice}
        # Tokens: {alice, owns, cat} vs {cat, owned, alice} -> 2 matches (alice, cat) if stemming not used,
        # but my tokenizer splits simple. "owns" != "owned" without stemming.
        # Let's ensure Jaccard is permissive enough or adjust test expectation.
        # Current implementation: "owns" and "owned" are different.
        # Overlap: "alice", "cat".
        # Claim tokens: 3. Sentence tokens: 5.
        # Intersection: 2. Union: 6. Score: 0.33. Threshold is 0.1. Should match.

        self.assertIsNotNone(c["highlight_start"])
        self.assertEqual(
            text[c["highlight_start"] : c["highlight_end"]],
            "The cat is owned by Alice.",
        )

    def test_no_match_garbage(self):
        """Test that garbage claims do not return a highlight."""
        text = "Alice owns a cat."
        claims = [
            {
                "claim_id": "1",
                "subject": "Zorg",
                "predicate": "destroys",
                "object": "planet",
            }
        ]

        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        self.assertIsNone(c["highlight_start"])

    def test_multiple_sentences_best_match(self):
        """Test picking the best sentence among similar ones."""
        text = "Alice has a dog. Alice has a cat. Alice has a parrot."
        claims = [
            {"claim_id": "1", "subject": "Alice", "predicate": "has", "object": "cat"}
        ]

        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        matched = text[c["highlight_start"] : c["highlight_end"]]
        self.assertEqual(matched, "Alice has a cat.")

    def test_complex_punctuation_handling(self):
        """Test robust splitting with complex punctuation."""
        text = "Dr. Smith is here... or is he? No, he's not! Wait; maybe."
        # Splitter regex: r'[^.!?]+[.!?]+'
        # 1. "Dr. Smith is here..."
        # 2. " or is he?"
        # 3. " No, he's not!"
        # 4. " Wait;" -> regex requires [.!?]. ";" is not split by default regex unless handled.
        # My regex `r'[^.!?]+[.!?]+'` might fail on "Wait;" if it expects .!?
        # Let's see behavior.

        claims = [
            {"claim_id": "1", "subject": "Smith", "predicate": "is", "object": "here"}
        ]
        result = self.highlighter.align_claims(text, claims)

        c = result[0]
        self.assertIn("Smith is here", text[c["highlight_start"] : c["highlight_end"]])

    def test_empty_inputs(self):
        """Test empty text and claims."""
        self.assertEqual(self.highlighter.align_claims("", []), [])
        self.assertEqual(self.highlighter.align_claims("Text", []), [])
        result = self.highlighter.align_claims("", [{"subject": "A"}])
        self.assertIsNone(result[0]["highlight_start"])


if __name__ == "__main__":
    unittest.main()
