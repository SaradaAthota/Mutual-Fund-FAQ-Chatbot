"""Retriever service combining Pinecone vector search with Mongo metadata."""

from __future__ import annotations

import logging
from typing import List, Sequence

from pinecone import Pinecone
from pymongo import MongoClient

from ..config import get_settings

LOGGER = logging.getLogger(__name__)


class RetrieverService:
    def __init__(self) -> None:
        settings = get_settings()
        if not settings.pinecone.api_key:
            raise ValueError("PINECONE_API_KEY is required")
        self._pinecone = Pinecone(api_key=settings.pinecone.api_key)
        self._index = self._pinecone.Index(settings.pinecone.index_name)
        self._mongo = MongoClient(settings.mongo.uri)
        self._chunks = self._mongo[settings.mongo.db_name][settings.mongo.chunks_collection]

    def close(self) -> None:
        self._mongo.close()

    def fetch_chunks(self, ids: Sequence[str]) -> List[dict]:
        if not ids:
            return []
        docs = list(self._chunks.find({"chunk_id": {"$in": list(ids)}}))
        return docs

    def query(self, embedding: List[float], top_k: int = 5) -> List[dict]:
        if not embedding:
            return []
        response = self._index.query(vector=embedding, top_k=top_k, include_metadata=True)
        matches = response.get("matches", [])
        chunk_ids = [match["id"] for match in matches if match.get("score", 0) > 0]
        documents = self.fetch_chunks(chunk_ids)
        chunk_map = {doc.get("chunk_id"): doc for doc in documents}
        ordered = []
        for match in matches:
            chunk_id = match.get("id")
            if chunk_id in chunk_map:
                doc = chunk_map[chunk_id]
                doc["score"] = match.get("score")
                ordered.append(doc)
        LOGGER.info("Retriever returned %s chunks", len(ordered))
        return ordered
