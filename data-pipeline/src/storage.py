"""MongoDB storage helpers for scraped documents and chunks."""

from __future__ import annotations

import logging
from typing import Iterable, List

from pymongo import MongoClient

from .config import CONFIG
from .models import Chunk, ScrapedDocument

LOGGER = logging.getLogger(__name__)


class MongoStore:
    """Thin wrapper around MongoDB collections used by the pipeline."""

    def __init__(self) -> None:
        self._client = MongoClient(CONFIG.mongo.uri)
        self._db = self._client[CONFIG.mongo.db_name]
        self._documents = self._db[CONFIG.mongo.documents_collection]
        self._chunks = self._db[CONFIG.mongo.chunks_collection]

    def upsert_documents(self, documents: Iterable[ScrapedDocument]) -> None:
        for doc in documents:
            LOGGER.info("Upserting raw document for %s", doc.scheme)
            self._documents.update_one(
                {"url": doc.url},
                {
                    "$set": {
                        "scheme": doc.scheme,
                        "category": doc.category,
                        "url": doc.url,
                        "html": doc.html,
                        "text": doc.text,
                        "last_verified": doc.last_verified,
                        "extra_links": doc.extra_links,
                    }
                },
                upsert=True,
            )

    def upsert_chunks(self, chunks: Iterable[Chunk]) -> List[str]:
        inserted_ids: List[str] = []
        for chunk in chunks:
            payload = {
                "chunk_id": chunk.chunk_id,
                "scheme": chunk.scheme,
                "category": chunk.category,
                "url": chunk.url,
                "section": chunk.section,
                "content": chunk.content,
                "last_verified": chunk.last_verified,
                "metadata": chunk.metadata,
            }
            filter_query = {"chunk_id": chunk.chunk_id} if chunk.chunk_id else {
                "url": chunk.url,
                "section": chunk.section,
            }
            result = self._chunks.update_one(
                filter_query,
                {"$set": payload},
                upsert=True,
            )
            if chunk.chunk_id:
                inserted_ids.append(chunk.chunk_id)
            elif result.upserted_id:
                inserted_ids.append(str(result.upserted_id))
        return inserted_ids

    def close(self) -> None:
        self._client.close()
