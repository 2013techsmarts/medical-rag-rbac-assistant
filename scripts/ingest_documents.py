#!/usr/bin/env python3
"""
Orchestration script to ingest PDF and Markdown files from the data/ directory.
Steps:
1. Walk data/ directory recursively.
2. For each document, check if it's already ingested in Qdrant (by source_document payload).
3. If not ingested, parse with Docling (parser.py) to get DoclingDocument.
4. Chunk with HybridChunker (chunker.py) to get context-aware chunks.
5. For each chunk, compute dense and sparse embeddings (embeddings.py).
6. Build metadata with access_roles permission mapping (metadata.py).
7. Upsert chunks as PointStruct to Qdrant.
"""

import sys
import uuid
from pathlib import Path

from qdrant_client.models import FieldCondition, Filter, MatchValue, PointStruct

from medibot.config.settings import settings
from medibot.rag.ingestion import (
    build_metadata,
    chunk_document,
    get_embeddings,
    parse_document,
)
from medibot.vectorstore.qdrant import get_qdrant_client


def is_document_ingested(client, collection_name: str, doc_name: str) -> bool:
    """Check if any chunks from this document are already present in the collection."""
    res = client.count(
        collection_name=collection_name,
        count_filter=Filter(
            must=[
                FieldCondition(
                    key="source_document",
                    match=MatchValue(value=doc_name),
                )
            ]
        ),
    )
    return res.count > 0


def main():
    # Base directory of the project
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"

    if not data_dir.exists():
        print(f"Error: Data directory not found at {data_dir}")
        sys.exit(1)

    # Find all supported files
    supported_extensions = {".pdf", ".md"}
    files = sorted(
        [p for p in data_dir.rglob("*") if p.suffix.lower() in supported_extensions]
    )

    if not files:
        print(f"No PDF or Markdown documents found in {data_dir}")
        sys.exit(0)

    print(f"Found {len(files)} documents to check for ingestion.")

    # Initialize Qdrant Client
    client = get_qdrant_client()
    collection_name = settings.collection_name

    # Verify collection exists
    if not client.collection_exists(collection_name):
        print(f"Error: Collection '{collection_name}' does not exist in Qdrant.")
        print("Please run `python scripts/create_collection.py` first.")
        sys.exit(1)

    total_chunks_added = 0

    for idx, file_path in enumerate(files, 1):
        doc_name = file_path.name
        print(f"\n[{idx}/{len(files)}] Processing '{doc_name}'...")

        # Skip if already ingested
        if is_document_ingested(client, collection_name, doc_name):
            print(f"  -> Already ingested. Skipping.")
            continue

        print(f"  -> Parsing with Docling...")
        try:
            doc = parse_document(file_path)
        except Exception as e:
            print(f"  -> Error parsing document {doc_name}: {e}")
            continue

        print(f"  -> Chunking...")
        try:
            chunks = chunk_document(doc)
        except Exception as e:
            print(f"  -> Error chunking document {doc_name}: {e}")
            continue

        if not chunks:
            print(f"  -> No chunks generated for {doc_name}.")
            continue

        print(f"  -> Generating embeddings & metadata for {len(chunks)} chunks...")
        points = []
        for c_idx, chunk in enumerate(chunks):
            # Get dense and sparse embeddings (runs lazy loading on first call)
            dense_vec, sparse_vec = get_embeddings(chunk.context_text)

            # Build metadata payload
            meta = build_metadata(chunk, file_path)
            payload = meta.model_dump()
            payload["text"] = chunk.text  # Embed text in payload for prompt retrieval

            # Deterministic point ID to avoid duplicates
            point_id = str(
                uuid.uuid5(uuid.NAMESPACE_DNS, f"{doc_name}_{c_idx}_{chunk.text[:50]}")
            )

            points.append(
                PointStruct(
                    id=point_id,
                    vector={"dense": dense_vec, "sparse": sparse_vec},
                    payload=payload,
                )
            )

        print(f"  -> Upserting to Qdrant...")
        try:
            client.upsert(collection_name=collection_name, points=points)
            print(f"  -> Successfully ingested {len(points)} chunks.")
            total_chunks_added += len(points)
        except Exception as e:
            print(f"  -> Error upserting to Qdrant for {doc_name}: {e}")

    print(f"\nIngestion finished. Added a total of {total_chunks_added} chunks.")


if __name__ == "__main__":
    main()
