"""Core dataclasses used throughout the data pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class SchemePage:
    """Represents the seed metadata for a scheme page on Groww."""

    scheme: str
    category: str
    url: str


@dataclass
class ScrapedDocument:
    """Raw HTML/text pulled from Groww along with canonical metadata."""

    scheme: str
    category: str
    url: str
    html: str
    text: str
    last_verified: str
    extra_links: List[str] = field(default_factory=list)


@dataclass
class Chunk:
    """A Docling-processed chunk ready for storage + embedding."""

    scheme: str
    category: str
    url: str
    section: str
    content: str
    last_verified: str
    metadata: Dict[str, str] = field(default_factory=dict)
    chunk_id: Optional[str] = None


@dataclass
class EmbeddingRecord:
    """Chunk content plus numerical embedding vector."""

    chunk: Chunk
    vector: List[float]
