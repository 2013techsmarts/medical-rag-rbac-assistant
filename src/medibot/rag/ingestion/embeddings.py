"""
Embedding module using fastembed.
Produces both dense (BAAI/bge-large-en-v1.5, 1024-dim) and
sparse (Qdrant/bm25) vectors for a given text.
Both models are lazy-loaded on first use as singletons.
"""
from fastembed import SparseTextEmbedding, TextEmbedding
from qdrant_client.models import SparseVector

from medibot.config.settings import settings

# Singletons — initialised once
_dense_model: TextEmbedding | None = None
_sparse_model: SparseTextEmbedding | None = None


def _get_dense_model() -> TextEmbedding:
    global _dense_model
    if _dense_model is None:
        _dense_model = TextEmbedding(model_name=settings.dense_model)
    return _dense_model


def _get_sparse_model() -> SparseTextEmbedding:
    global _sparse_model
    if _sparse_model is None:
        _sparse_model = SparseTextEmbedding(model_name=settings.sparse_model)
    return _sparse_model


def get_dense_embedding(text: str) -> list[float]:
    """
    Compute a dense embedding vector for the given text.

    Args:
        text: Input text (context-enriched chunk text or query).

    Returns:
        List of floats (1024 dimensions for bge-large-en-v1.5).
    """
    model = _get_dense_model()
    embeddings = list(model.embed([text]))
    return embeddings[0].tolist()


def get_sparse_embedding(text: str) -> SparseVector:
    """
    Compute a sparse BM25 vector for the given text.

    Args:
        text: Input text.

    Returns:
        SparseVector with indices and values for Qdrant upsert/query.
    """
    model = _get_sparse_model()
    results = list(model.embed([text]))
    sparse = results[0]
    return SparseVector(
        indices=sparse.indices.tolist(),
        values=sparse.values.tolist(),
    )


def get_embeddings(text: str) -> tuple[list[float], SparseVector]:
    """
    Compute both dense and sparse embeddings in one call.

    Args:
        text: Input text.

    Returns:
        (dense_vector, sparse_vector) tuple.
    """
    return get_dense_embedding(text), get_sparse_embedding(text)