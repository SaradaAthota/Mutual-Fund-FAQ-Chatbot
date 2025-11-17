"""Backend configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: Optional[str] = None) -> str:
    import os

    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' is required")
    return value


@dataclass(frozen=True)
class MongoSettings:
    uri: str = _env("MONGODB_URI", "mongodb://localhost:27017")
    db_name: str = _env("MONGODB_DB", "mutual_fund_faq")
    chunks_collection: str = _env("MONGODB_COLLECTION_CHUNKS", "chunks")


@dataclass(frozen=True)
class PineconeSettings:
    api_key: str = _env("PINECONE_API_KEY", "")
    index_name: str = _env("PINECONE_INDEX", "groww-hdfc-faq")


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str = _env("OPENAI_API_KEY", "")
    chat_model: str = _env("OPENAI_CHAT_MODEL", "gpt-4o")
    embed_model: str = _env("OPENAI_EMBED_MODEL", "text-embedding-3-small")


@dataclass(frozen=True)
class AdviceSettings:
    refusal_link: str = _env(
        "ADVICE_REFUSAL_LINK",
        "https://www.sebi.gov.in/sebiweb/investors/InvestorProtection.jsp",
    )


@dataclass(frozen=True)
class AppSettings:
    mongo: MongoSettings = MongoSettings()
    pinecone: PineconeSettings = PineconeSettings()
    openai: OpenAISettings = OpenAISettings()
    advice: AdviceSettings = AdviceSettings()
    disclaimer: str = _env("DISCLAIMER_TEXT", "Facts-only. No investment advice.")


@lru_cache
def get_settings() -> AppSettings:
    return AppSettings()
