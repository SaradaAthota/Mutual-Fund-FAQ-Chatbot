"""Embedding helpers using OpenAI embeddings API."""

from __future__ import annotations

import logging
from typing import Iterable, List

from openai import OpenAI

from .config import CONFIG
from .models import Chunk, EmbeddingRecord

LOGGER = logging.getLogger(__name__)

_openai_client: OpenAI | None = None


def _client() -> OpenAI:
    global _openai_client  # noqa: PLW0603
    if _openai_client is not None:
        return _openai_client
    if not CONFIG.openai.api_key:
        raise ValueError("OPENAI_API_KEY is required for embeddings")
    _openai_client = OpenAI(api_key=CONFIG.openai.api_key)
    return _openai_client


def embed_chunks(chunks: Iterable[Chunk], *, batch_size: int = 32) -> List[EmbeddingRecord]:
    client = _client()
    model_name = CONFIG.openai.embed_model
    embedding_records: List[EmbeddingRecord] = []
    batch: List[Chunk] = []

    def _flush_batch() -> None:
        nonlocal batch
        if not batch:
            return
        texts = [chunk.content for chunk in batch]
        response = client.embeddings.create(model=model_name, input=texts)
        for chunk, datum in zip(batch, response.data):
            embedding_records.append(EmbeddingRecord(chunk=chunk, vector=datum.embedding))
        batch = []

    for chunk in chunks:
        if not chunk.content.strip():
            continue
        batch.append(chunk)
        if len(batch) >= batch_size:
            _flush_batch()

    _flush_batch()
    LOGGER.info("Generated %s embeddings via OpenAI", len(embedding_records))
    return embedding_records
