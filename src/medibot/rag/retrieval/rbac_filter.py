from qdrant_client.models import FieldCondition, Filter, MatchValue


def build_rbac_filter(role: str) -> Filter:
    """
    Build a Qdrant Filter to restrict retrieval to chunks that the specified
    role is allowed to access.
    
    This applies the 'access_roles' metadata filter at the vector store query level.
    
    Args:
        role: The role of the user requesting retrieval (e.g. 'doctor', 'nurse').
        
    Returns:
        Qdrant Filter object.
    """
    return Filter(
        must=[
            FieldCondition(
                key="access_roles",
                match=MatchValue(value=role),
            )
        ]
    )
