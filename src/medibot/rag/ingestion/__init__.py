"""
Document ingestion pipeline.
Provides document parsing, hierarchical chunking, dense/sparse vector embedding,
and metadata generation.
"""

from .chunker import Chunk, chunk_document
from .embeddings import get_dense_embedding, get_embeddings, get_sparse_embedding
from .metadata import build_metadata
from .parser import parse_document

__all__ = [
    "parse_document",
    "chunk_document",
    "Chunk",
    "get_embeddings",
    "get_dense_embedding",
    "get_sparse_embedding",
    "build_metadata",
]
