"""Helper to format citation payloads consistently."""

from __future__ import annotations

from datetime import datetime

from ..config import get_settings
from ..models import Citation


def build_citation(metadata: dict) -> Citation:
    url = metadata.get("url")
    if not url:
        raise ValueError("Chunk metadata missing URL")
    last_verified = metadata.get("last_verified") or datetime.utcnow().strftime("%Y-%m-%d")
    return Citation(
        text=metadata.get("scheme", "HDFC Mutual Fund"),
        url=url,
        last_verified=f"Last updated from sources: {last_verified}",
    )
