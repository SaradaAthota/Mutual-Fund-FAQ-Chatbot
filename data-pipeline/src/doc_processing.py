"""Docling-powered preprocessing utilities."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

from bs4 import BeautifulSoup

try:  # Best-effort Docling import
    from docling.pipeline.standard import StandardPipeline
    from docling_common.utils import docling_logger

    docling_logger.setLevel(logging.WARNING)
    _DOC_PIPELINE = StandardPipeline()
except Exception:  # noqa: BLE001
    _DOC_PIPELINE = None

from .models import Chunk, ScrapedDocument

LOGGER = logging.getLogger(__name__)


def _fallback_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return "\n".join(
        [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    )


def normalize_text(html: str) -> str:
    if _DOC_PIPELINE is None:
        return _fallback_clean_text(html)
    try:
        artifact = _DOC_PIPELINE.run(html, mime_type="text/html")
        text_blocks = []
        for section in artifact.sections:
            section_title = section.title or ""
            section_text = section.export_text()
            text_blocks.append(f"{section_title}\n{section_text}".strip())
        return "\n\n".join([block for block in text_blocks if block])
    except Exception as exc:  # noqa: BLE001
        LOGGER.warning("Docling pipeline failed, falling back: %s", exc)
        return _fallback_clean_text(html)


def chunk_text(text: str, *, chunk_size: int = 700, overlap: int = 100) -> List[str]:
    tokens = text.split()
    chunks: List[str] = []
    start = 0
    while start < len(tokens):
        end = min(len(tokens), start + chunk_size)
        chunks.append(" ".join(tokens[start:end]))
        if end == len(tokens):
            break
        start = max(0, end - overlap)
    return chunks


def build_chunks(doc: ScrapedDocument, *, chunk_size: int = 700) -> List[Chunk]:
    normalized_text = normalize_text(doc.html)
    if not normalized_text.strip():
        normalized_text = doc.text
    segments = chunk_text(normalized_text, chunk_size=chunk_size)
    chunks: List[Chunk] = []
    for idx, segment in enumerate(segments, start=1):
        chunk_id = f"{doc.url}#section-{idx}"
        chunks.append(
            Chunk(
                scheme=doc.scheme,
                category=doc.category,
                url=doc.url,
                section=f"Section {idx}",
                content=segment.strip(),
                last_verified=doc.last_verified,
                metadata={"position": str(idx)},
                chunk_id=chunk_id,
            )
        )
    return chunks


def export_sources(documents: Iterable[ScrapedDocument], output_csv: Path) -> None:
    import csv

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["scheme", "category", "url", "last_verified"]
    with output_csv.open("w", encoding="utf-8", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for doc in documents:
            writer.writerow(
                {
                    "scheme": doc.scheme,
                    "category": doc.category,
                    "url": doc.url,
                    "last_verified": doc.last_verified,
                }
            )
