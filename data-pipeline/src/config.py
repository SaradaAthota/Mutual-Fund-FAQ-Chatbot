"""Configuration helpers for the data pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


def _env(key: str, default: Optional[str] = None) -> str:
    """Fetch environment variables with optional defaults."""

    import os

    value = os.getenv(key, default)
    if value is None:
        raise ValueError(f"Environment variable '{key}' is required")
    return value


@dataclass(frozen=True)
class MongoSettings:
    uri: str = _env("MONGODB_URI", "mongodb://localhost:27017")
    db_name: str = _env("MONGODB_DB", "mutual_fund_faq")
    documents_collection: str = _env("MONGODB_COLLECTION_DOCUMENTS", "documents")
    chunks_collection: str = _env("MONGODB_COLLECTION_CHUNKS", "chunks")


@dataclass(frozen=True)
class PineconeSettings:
    api_key: str = _env("PINECONE_API_KEY", "")
    environment: str = _env("PINECONE_ENV", "")
    index_name: str = _env("PINECONE_INDEX", "groww-hdfc-faq")


@dataclass(frozen=True)
class OpenAISettings:
    api_key: str = _env("OPENAI_API_KEY", "")
    embed_model: str = _env("OPENAI_EMBED_MODEL", "text-embedding-3-small")
    chat_model: str = _env("OPENAI_CHAT_MODEL", "gpt-4o")


@dataclass(frozen=True)
class PipelinePaths:
    output_dir: Path = Path(_env("DATA_OUTPUT_DIR", "./data-pipeline/output")).resolve()


@dataclass(frozen=True)
class PipelineConfig:
    mongo: MongoSettings = MongoSettings()
    pinecone: PineconeSettings = PineconeSettings()
    openai: OpenAISettings = OpenAISettings()
    paths: PipelinePaths = PipelinePaths()


CONFIG = PipelineConfig()
