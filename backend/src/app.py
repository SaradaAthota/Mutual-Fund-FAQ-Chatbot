"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import ErrorResponse, QueryAnswer, QueryRequest
from .services.query_service import QueryService


LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "backend.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
    force=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    service = QueryService()
    app.state.query_service = service
    yield
    service.close()


app = FastAPI(
    title="Mutual Fund FAQ Assistant",
    version="0.1.0",
    description="Facts-only HDFC Mutual Fund FAQ assistant (Groww corpus)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:3000",
        "http://localhost:3000",
        "https://mf-faq-backend-production.up.railway.app",
        "https://mutual-fund-faq-chatbot.vercel.app",
    ],
    allow_origin_regex=r"https://mutual-fund-faq-chatbot.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=QueryAnswer, responses={400: {"model": ErrorResponse}})
def handle_query(payload: QueryRequest) -> QueryAnswer:
    try:
        service: QueryService = app.state.query_service
        return service.handle(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


__all__ = ["app"]
