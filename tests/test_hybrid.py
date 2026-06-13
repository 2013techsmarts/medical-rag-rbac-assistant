import pytest

from medibot.rag.retrieval import hybrid_search, rerank


def test_rbac_filtering_doctor():
    """Doctor should access general, clinical, and nursing, but NOT billing or equipment."""
    query = "treatment"
    results = hybrid_search(query, role="doctor", top_k=5)
    
    # We should have some results from the ingested documents
    assert len(results) > 0
    
    for point in results:
        collection = point.payload["collection"]
        assert collection in ["general", "clinical", "nursing"]
        assert collection not in ["billing", "equipment"]


def test_rbac_filtering_nurse():
    """Nurse should access general and nursing, but NOT clinical, billing, or equipment."""
    query = "patient"
    results = hybrid_search(query, role="nurse", top_k=5)
    
    # Verify collections
    for point in results:
        collection = point.payload["collection"]
        assert collection in ["general", "nursing"]
        assert collection not in ["clinical", "billing", "equipment"]


def test_rbac_filtering_billing_executive():
    """Billing executive should access general and billing, but NOT clinical, nursing, or equipment."""
    query = "claim"
    results = hybrid_search(query, role="billing_executive", top_k=5)
    
    # Verify collections
    for point in results:
        collection = point.payload["collection"]
        assert collection in ["general", "billing"]
        assert collection not in ["clinical", "nursing", "equipment"]


def test_hybrid_search_and_reranking():
    """Reranking should sort candidate points based on joint attention relevancy score."""
    query = "infection control policy"
    candidates = hybrid_search(query, role="nurse", top_k=10)
    
    assert len(candidates) > 0
    
    # Rerank the candidates
    reranked = rerank(query, candidates, top_n=3)
    
    assert len(reranked) <= 3
    assert len(reranked) > 0
    
    # The scores should be sorted in descending order
    scores = [p.score for p in reranked]
    assert scores == sorted(scores, reverse=True)
