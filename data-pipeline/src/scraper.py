"""Scraper utilities for collecting Groww scheme content."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, List, Tuple
import re

import requests
from bs4 import BeautifulSoup

from .config import CONFIG
from .constants import LAST_VERIFIED, SCHEME_URLS
from .models import SchemePage, ScrapedDocument

LOGGER = logging.getLogger(__name__)


def _headers() -> dict:
    user_agent = CONFIG.paths.output_dir.name or "MutualFundFAQBot/0.1"
    return {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml",
    }


def _scheme_entries() -> Iterable[SchemePage]:
    for entry in SCHEME_URLS:
        yield SchemePage(**entry)


def fetch_html(url: str, *, retries: int = 3, backoff: float = 1.5) -> str:
    """Fetch HTML with retries and Groww-friendly headers."""

    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(url, headers=_headers(), timeout=30)
            if resp.status_code != 200:
                raise RuntimeError(f"{url} returned {resp.status_code}")
            return resp.text
        except Exception as exc:  # noqa: BLE001
            LOGGER.warning("Attempt %s for %s failed: %s", attempt, url, exc)
            if attempt == retries:
                raise
            time.sleep(backoff * attempt)
    raise RuntimeError(f"Failed to fetch {url}")


def extract_text_and_links(html: str) -> Tuple[str, List[str]]:
    """Extract visible text and Groww hyperlinks from HTML."""

    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = "\n".join(
        [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
    )

    links: List[str] = []
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.startswith("https://groww.in/") and href not in links:
            links.append(href)
    return text, links


def scrape_scheme(page: SchemePage) -> ScrapedDocument:
    html = fetch_html(page.url)
    text, links = extract_text_and_links(html)
    text = _augment_with_dynamic_sections(page, html, text)
    return ScrapedDocument(
        scheme=page.scheme,
        category=page.category,
        url=page.url,
        html=html,
        text=text,
        last_verified=LAST_VERIFIED,
        extra_links=links,
    )


def scrape_all() -> List[ScrapedDocument]:
    documents: List[ScrapedDocument] = []
    for entry in _scheme_entries():
        LOGGER.info("Scraping %s", entry.scheme)
        documents.append(scrape_scheme(entry))
    return documents


def _augment_with_dynamic_sections(page: SchemePage, html: str, base_text: str) -> str:
    if page.scheme != "HDFC Flexi Cap Fund Direct Plan Growth":
        return base_text
    snippet = _extract_fund_management_section(html)
    if not snippet:
        return base_text
    if "Fund management" in base_text:
        return base_text
    return base_text + "\n\n" + snippet


def _extract_fund_management_section(html: str) -> str:
    pattern = re.compile(r"Fund management.*?(?:Fund house|Investment objective)", re.IGNORECASE | re.DOTALL)
    match = pattern.search(html)
    if not match:
        return ""
    soup = BeautifulSoup(match.group(0), "html.parser")
    text = " ".join(soup.get_text(separator=" ").split())
    return text


def save_raw_documents(docs: Iterable[ScrapedDocument], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fp:
        json.dump([asdict(doc) for doc in docs], fp, ensure_ascii=False, indent=2)
