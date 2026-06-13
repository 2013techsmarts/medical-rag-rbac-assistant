from qdrant_client.models import Fusion, FusionQuery, Prefetch, ScoredPoint

from medibot.config.settings import settings
from medibot.rag.ingestion import get_dense_embedding, get_sparse_embedding
from medibot.rag.retrieval.rbac_filter import build_rbac_filter
from medibot.vectorstore.qdrant import get_qdrant_client


def hybrid_search(query: str, role: str, top_k: int | None = None) -> list[ScoredPoint]:
    """
    Perform a single-query hybrid search in Qdrant.
    Combines dense (bge-large-en-v1.5) and sparse (bm25) vectors using
    Reciprocal Rank Fusion (RRF), applying RBAC filters at the vector store level.
    
    Args:
        query: User search query string.
        role: Role of the user making the query (for RBAC filtering).
        top_k: Number of candidates to retrieve. Defaults to settings.retrieval_top_k.
        
    Returns:
        List of ScoredPoint objects from Qdrant.
    """
    if top_k is None:
        top_k = settings.retrieval_top_k

    client = get_qdrant_client()
    
    # Compute query embeddings
    dense_vec = get_dense_embedding(query)
    sparse_vec = get_sparse_embedding(query)
    
    # Build the payload filter checking 'access_roles'
    rbac_filter = build_rbac_filter(role)

    # Perform query with prefetch (dense + sparse) fused using RRF
    response = client.query_points(
        collection_name=settings.collection_name,
        prefetch=[
            Prefetch(
                query=dense_vec,
                using="dense",
                limit=top_k,
                filter=rbac_filter,
            ),
            Prefetch(
                query=sparse_vec,
                using="sparse",
                limit=top_k,
                filter=rbac_filter,
            ),
        ],
        query=FusionQuery(fusion=Fusion.RRF),
        limit=top_k,
    )
    return response.points
