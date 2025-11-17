"""Rule-based detector for advisory/investment questions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

ADVISORY_PATTERNS = [
    r"should I (buy|sell)",
    r"is (this|it) a good time",
    r"will it go up",
    r"recommend",
    r"suggest .* fund",
    r"portfolio",
    r"better than",
    r"invest(ing)?",
    r"investment advice",
]


@dataclass
class AdviceGuard:
    patterns: Iterable[re.Pattern[str]]

    @classmethod
    def default(cls) -> "AdviceGuard":
        compiled = [re.compile(pat, re.IGNORECASE) for pat in ADVISORY_PATTERNS]
        return cls(patterns=compiled)

    def classify(self, question: str) -> bool:
        question = question.strip()
        for pattern in self.patterns:
            if pattern.search(question):
                return True
        return False
