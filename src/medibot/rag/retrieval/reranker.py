from qdrant_client.models import ScoredPoint
from sentence_transformers import CrossEncoder

from medibot.config.settings import settings

# Lazy loaded singleton model
_model: CrossEncoder | None = None


def _get_model() -> CrossEncoder:
    global _model
    if _model is None:
        _model = CrossEncoder(settings.reranker_model)
    return _model


def rerank(
    query: str, candidates: list[ScoredPoint], top_n: int | None = None
) -> list[ScoredPoint]:
    """
    Rerank candidate chunks using the cross-encoder reranker.
    Computes joint attention query-context similarity scores and returns
    the top N chunks sorted by relevancy.
    
    Args:
        query: User search query.
        candidates: List of retrieve ScoredPoint chunks.
        top_n: Number of final chunks to return. Defaults to settings.rerank_top_n.
        
    Returns:
        List of ScoredPoint chunks with updated similarity scores.
    """
    if not candidates:
        return []

    if top_n is None:
        top_n = settings.rerank_top_n

    model = _get_model()

    # Create (query, context) text pairs
    pairs = [[query, p.payload.get("text", "")] for p in candidates]

    # Predict scores (higher = more relevant)
    scores = model.predict(pairs)

    # Sort candidates by rerank score descending
    ranked = sorted(zip(scores, candidates), key=lambda x: x[0], reverse=True)

    results = []
    for score, candidate in ranked[:top_n]:
        candidate.score = float(score)  # Update score with the cross-encoder score
        results.append(candidate)

    return results
