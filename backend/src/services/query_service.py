"""High-level orchestrator for the FAQ query pipeline."""

from __future__ import annotations

from datetime import datetime, timezone

from typing import Optional

from ..config import get_settings
from ..models import Citation, QueryAnswer, QueryRequest, QueryType
from .advice_guard import AdviceGuard
from .citation import build_citation
from .llm import OpenAIClient
from .retriever import RetrieverService


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
    @staticmethod
    def _select_best_citation(matches, citations, question: str) -> Citation:
        normalized_question = question.lower()

        for match, citation in zip(matches, citations):
            scheme = (match.get("scheme") or "").lower()
            if scheme and scheme in normalized_question:
                return citation

        for match, citation in zip(matches, citations):
            section = (match.get("section") or "").lower()
            if section and section in normalized_question:
                return citation

        return citations[0]
