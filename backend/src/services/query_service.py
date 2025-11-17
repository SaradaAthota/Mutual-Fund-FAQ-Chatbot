"""High-level orchestrator for the FAQ query pipeline."""

from __future__ import annotations

from datetime import datetime, timezone
import re

from typing import Optional

from ..config import get_settings
from ..models import Citation, QueryAnswer, QueryRequest, QueryType
from .advice_guard import AdviceGuard
from .citation import build_citation
from .llm import OpenAIClient
from .retriever import RetrieverService


GENERIC_SCHEME_TERMS = {"direct", "plan", "growth", "regular", "scheme"}


class QueryService:
    def __init__(
        self,
        *,
        guard: Optional[AdviceGuard] = None,
        llm: Optional[OpenAIClient] = None,
        retriever: Optional[RetrieverService] = None,
    ) -> None:
        self._settings = get_settings()
        self._guard = guard or AdviceGuard.default()
        self._llm = llm or OpenAIClient()
        self._retriever = retriever or RetrieverService()

    def _advice_response(self) -> QueryAnswer:
        return QueryAnswer(
            answer=(
                "I’m sorry, but I can’t provide investment or portfolio advice. Please consult a "
                "SEBI-registered financial adviser for personalised guidance."
            ),
            citations=[self._settings.advice.refusal_link],
            is_factual=False,
            method="advice_guard",
        )

    def _no_result_response(self) -> QueryAnswer:
        fallback_url = "https://groww.in/mutual-funds"
        answer = "I couldn’t find that fact in the official Groww documents I have."
        return QueryAnswer(
            answer=f"{answer} [{fallback_url}]",
            citations=[fallback_url],
            method="no_result",
        )

    def handle(self, payload: QueryRequest) -> QueryAnswer:
        question = payload.query.strip()
        if self._guard.classify(question):
            return self._advice_response()

        embedding = self._llm.embed(question)
        matches = self._retriever.query(embedding)
        if not matches:
            return self._no_result_response()

        contexts = []
        for match in matches[:3]:
            prefix = match.get("section") or "Section"
            contexts.append(f"{prefix}: {match.get('content', '')}")

        answer = self._llm.answer(question, contexts)
        ordered_citations = [build_citation(match) for match in matches]
        best_citation = self._select_best_citation(matches, ordered_citations, question)
        primary_url = best_citation.url
        clean_answer = answer.replace("[CITATION]", "").strip()
        last_updated = best_citation.last_verified

        return QueryAnswer(
            answer=clean_answer,
            citations=[primary_url],
            method="rag",
            last_updated=last_updated,
        )

    def close(self) -> None:
        self._retriever.close()

    @staticmethod
    def _select_best_citation(matches, citations, question: str) -> Citation:
        normalized_question = QueryService._normalize_text(question)
        question_tokens = set(normalized_question.split())

        best_citation = citations[0]
        best_score = 0

        for match, citation in zip(matches, citations):
            scheme_tokens = QueryService._scheme_tokens(match.get("scheme") or "")
            if not scheme_tokens:
                continue
            overlap = len(question_tokens.intersection(scheme_tokens))
            if overlap > best_score:
                best_score = overlap
                best_citation = citation

        if best_score:
            return best_citation

        for match, citation in zip(matches, citations):
            scheme = QueryService._normalize_text(match.get("scheme") or "")
            if scheme and scheme in normalized_question:
                return citation

        for match, citation in zip(matches, citations):
            section = QueryService._normalize_text(match.get("section") or "")
            if section and section in normalized_question:
                return citation

        return citations[0]

    @staticmethod
    def _normalize_text(text: str) -> str:
        if not text:
            return ""
        cleaned = re.sub(r"[^a-z0-9\s]", " ", text.lower())
        return re.sub(r"\s+", " ", cleaned).strip()

    @staticmethod
    def _scheme_tokens(text: str) -> set[str]:
        normalized = QueryService._normalize_text(text)
        tokens = [token for token in normalized.split() if token and token not in GENERIC_SCHEME_TERMS]
        return set(tokens)
