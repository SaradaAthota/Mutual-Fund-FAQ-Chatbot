"""End-to-end tests for the QueryService pipeline."""

from __future__ import annotations

import os

import pytest

from backend.src.models import QueryRequest, QueryType
from backend.src.services.query_service import QueryService


class DummyGemini:
    def embed(self, text: str):  # noqa: ANN001, D401
        """Return a deterministic fake embedding."""

        return [0.1, 0.2, 0.3]

    def answer(self, question: str, contexts):  # noqa: ANN001
        return "Stub answer [CITATION]"


class DummyRetriever:
    def __init__(self, matches):  # noqa: ANN001
        self._matches = matches
        self.received_embedding = None

    def query(self, embedding, top_k: int = 5):  # noqa: ANN001
        self.received_embedding = embedding
        return self._matches

    def close(self):  # noqa: D401
        """No-op for tests."""


def test_advice_guard_refuses_advisory_question():
    service = QueryService(llm=DummyGemini(), retriever=DummyRetriever([]))
    response = service.handle(QueryRequest(question="Should I invest in this fund?"))

    assert response.query_type == QueryType.ADVISORY
    assert "provide investment" in response.answer


def test_no_result_returns_fallback_message():
    service = QueryService(llm=DummyGemini(), retriever=DummyRetriever([]))
    response = service.handle(QueryRequest(question="What is the exit load for foo?"))

    assert "couldn’t find" in response.answer or "couldn't find" in response.answer
    assert response.citation.url.startswith("https://groww.in/")


@pytest.mark.integration
def test_openai_generates_answer_with_real_model():
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not configured for integration test")

    matches = [
        {
            "chunk_id": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth#section-1",
            "scheme": "HDFC ELSS Tax Saver Fund Direct Plan Growth",
            "category": "ELSS",
            "url": "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
            "section": "Exit Load",
            "content": "Exit load is Nil for HDFC ELSS Tax Saver Fund Direct Plan Growth.",
            "last_verified": "2025-11-15",
        }
    ]

    class PassthroughRetriever(DummyRetriever):
        def __init__(self):
            super().__init__(matches)

    service = QueryService(retriever=PassthroughRetriever())

    response = service.handle(
        QueryRequest(question="What is the exit load for HDFC ELSS Tax Saver Fund?")
    )

    assert response.query_type == QueryType.FACTUAL
    answer_lower = response.answer.lower()
    assert "exit" in answer_lower or "nil" in answer_lower
    assert response.citation.url == matches[0]["url"]
    assert matches[0]["url"] in response.answer
