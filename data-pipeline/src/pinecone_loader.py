"""Utilities to push embeddings into Pinecone."""

from __future__ import annotations

import logging
from typing import Iterable

from pinecone import Pinecone

from .config import CONFIG
from .models import EmbeddingRecord

LOGGER = logging.getLogger(__name__)


class PineconeLoader:
    def __init__(self) -> None:
        if not CONFIG.pinecone.api_key:
            raise ValueError("PINECONE_API_KEY is required")
        self._pc = Pinecone(api_key=CONFIG.pinecone.api_key)
        self._index = self._pc.Index(CONFIG.pinecone.index_name)

    def upsert(self, embeddings: Iterable[EmbeddingRecord]) -> None:
        vectors = []
        for record in embeddings:
            metadata = {
                "scheme": record.chunk.scheme,
                "category": record.chunk.category,
                "url": record.chunk.url,
                "section": record.chunk.section,
                "last_verified": record.chunk.last_verified,
            }
            metadata.update(record.chunk.metadata)
            vectors.append(
                {
                    "id": record.chunk.chunk_id or f"{record.chunk.url}#{record.chunk.section}",
                    "values": record.vector,
                    "metadata": metadata,
                }
            )
        if vectors:
            LOGGER.info("Upserting %s vectors into Pinecone", len(vectors))
            self._index.upsert(vectors=vectors)
