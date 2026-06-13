"""
Metadata builder for document chunks.
Maps each chunk to the full ChunkMetadata schema, including
access_roles derived by inverting the ROLE_ACCESS permission map.
"""
from pathlib import Path

from medibot.auth.roles import ROLE_ACCESS
from medibot.models.document import ChunkMetadata
from medibot.rag.ingestion.chunker import Chunk

# Invert ROLE_ACCESS: collection → list of roles that can access it
# e.g. "billing" → ["billing_executive", "admin"]
_COLLECTION_TO_ROLES: dict[str, list[str]] = {}
for role, collections in ROLE_ACCESS.items():
    for collection in collections:
        _COLLECTION_TO_ROLES.setdefault(collection, []).append(role)


def build_metadata(chunk: Chunk, doc_path: Path) -> ChunkMetadata:
    """
    Build a ChunkMetadata object for a given chunk and its source document.

    The collection is inferred from the document's parent directory name
    (e.g. data/billing/billing_codes.pdf → collection="billing").

    Access roles are all roles that have access to that collection,
    derived by inverting ROLE_ACCESS.

    Args:
        chunk:    Chunk object from chunker.chunk_document().
        doc_path: Absolute path to the source document file.

    Returns:
        ChunkMetadata with all fields populated.
    """
    # Collection = immediate parent folder name (billing, clinical, nursing, etc.)
    collection = doc_path.parent.name

    # Roles that can access this collection
    access_roles = _COLLECTION_TO_ROLES.get(collection, [])

    return ChunkMetadata(
        source_document=doc_path.name,
        collection=collection,
        access_roles=access_roles,
        section_title=chunk.section_title or doc_path.stem,
        chunk_type=chunk.chunk_type,
    )


def get_collection_to_roles() -> dict[str, list[str]]:
    """Return the inverted role map for inspection."""
    return dict(_COLLECTION_TO_ROLES)
