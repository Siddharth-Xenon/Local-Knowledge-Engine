"""Finance-specific text perturbations for semantic stability testing."""

import random


class FinancePerturbator:
    """Generates semantic variations of finance texts."""

    BOUNDARIES = {
        "greater than": ["exceeds", "more than", "above"],
        "less than": ["below", "under", "not exceeding"],
        "equal to": ["exactly", "same as"],
        "between": ["in the range of", "from ... to"],
        "max": ["maximum", "upper limit"],
        "min": ["minimum", "lower limit"],
    }

    NUMERIC_MAP = {
        "1M": "one million",
        "10k": "ten thousand",
        "1000": "1,000",
        "1%": "one percent",
    }

    @staticmethod
    def perturb(text: str) -> str:
        """Apply a random set of perturbations to the text."""
        p_text = text

        # 1. Case shuffling (lightweight)
        if random.random() < 0.5:
            p_text = p_text.lower()

        # 2. Boundary replacement
        for key, synonyms in FinancePerturbator.BOUNDARIES.items():
            if key in p_text and random.random() < 0.6:
                replacement = random.choice(synonyms)
                p_text = p_text.replace(key, replacement)

        # 3. Numeric expansion (Regex based or simple replace)
        # Simple replace for now
        for key, val in FinancePerturbator.NUMERIC_MAP.items():
            if key in p_text and random.random() < 0.6:
                p_text = p_text.replace(key, val)

        # 4. Typos (simulate Fat Finger)
        if random.random() < 0.3:
            p_text = FinancePerturbator._inject_typo(p_text)

        return p_text

    @staticmethod
    def _inject_typo(text: str) -> str:
        """Swap two adjacent characters once."""
        if len(text) < 4:
            return text
        idx = random.randint(1, len(text) - 2)
        chars = list(text)
        chars[idx], chars[idx + 1] = chars[idx + 1], chars[idx]
        return "".join(chars)
