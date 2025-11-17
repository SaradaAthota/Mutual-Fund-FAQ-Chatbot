"""Entry point to scrape, process, and upload Groww scheme data."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import CONFIG
from .doc_processing import build_chunks, export_sources
from .embedding import embed_chunks
from .pinecone_loader import PineconeLoader
from .scraper import save_raw_documents, scrape_all
from .storage import MongoStore

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


def run_pipeline(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Scrape
    LOGGER.info("Scraping Groww scheme pages")
    documents = scrape_all()
    save_raw_documents(documents, output_dir / "raw_documents.json")
    export_sources(documents, Path("docs/sources.csv"))

    # Step 2: Process + chunk
    LOGGER.info("Building chunks with Docling")
    all_chunks = []
    for doc in documents:
        chunks = build_chunks(doc)
        all_chunks.extend(chunks)

    # Step 3: Store in Mongo
    mongo_store = MongoStore()
    mongo_store.upsert_documents(documents)
    mongo_store.upsert_chunks(all_chunks)

    # Step 4: Embeddings + Pinecone
    LOGGER.info("Embedding %s chunks", len(all_chunks))
    embeddings = embed_chunks(all_chunks)
    loader = PineconeLoader()
    loader.upsert(embeddings)
    mongo_store.close()

    LOGGER.info("Pipeline completed successfully")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Groww data pipeline")
    parser.add_argument(
        "--output",
        default=CONFIG.paths.output_dir,
        type=Path,
        help="Directory to store raw scrape outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_pipeline(Path(args.output))


if __name__ == "__main__":
    main()
