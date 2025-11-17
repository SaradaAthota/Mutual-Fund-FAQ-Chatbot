"""Pydantic models shared across the API."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class QueryType(str, Enum):
    FACTUAL = "factual"
    ADVISORY = "advisory"


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)


class Citation(BaseModel):
    text: str
    url: str
    last_verified: str


class QueryAnswer(BaseModel):
    answer: str
    citations: List[str]
    is_factual: bool = True
    confidence: float = 1.0
    method: str = Field("rag", description="How the answer was generated")
    last_updated: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
    citation: Optional[Citation] = None
