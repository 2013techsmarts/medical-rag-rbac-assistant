"""
Hierarchical chunker using Docling's HybridChunker.
Splits along natural document structure (section → subsection → paragraph/table),
then applies token-aware size limits as a second pass.
Each chunk's embedded text carries its parent section heading as context prefix.
"""
from dataclasses import dataclass

from docling.chunking import HybridChunker
from docling.datamodel.document import DoclingDocument

# Token budget per chunk (roughly 512 tokens ≈ 350-400 words)
MAX_TOKENS = 512

# Singleton chunker
_chunker: HybridChunker | None = None


def get_chunker() -> HybridChunker:
    global _chunker
    if _chunker is None:
        _chunker = HybridChunker(max_tokens=MAX_TOKENS)
    return _chunker


@dataclass
class Chunk:
    """A single chunk with its text and heading context."""
    text: str           # The raw chunk text
    context_text: str   # "[section_heading]\n\n[chunk text]" — used for embedding
    section_title: str  # Closest parent heading
    chunk_type: str     # "text", "table", "code", etc.


def chunk_document(doc: DoclingDocument) -> list[Chunk]:
    """
    Chunk a DoclingDocument into Chunk objects using HybridChunker.

    The HybridChunker respects the document hierarchy and produces
    semantically coherent chunks. Each chunk's embedding input
    prepends its parent section heading for richer context.

    Args:
        doc: A parsed DoclingDocument from parser.parse_document().

    Returns:
        List of Chunk dataclass objects.
    """
    chunker = get_chunker()
    chunks: list[Chunk] = []

    for docling_chunk in chunker.chunk(doc):
        raw_text = docling_chunk.text.strip()
        if not raw_text:
            continue

        # Extract section heading from chunk metadata
        section_title = _extract_heading(docling_chunk)

        # Determine chunk type
        chunk_type = _detect_chunk_type(docling_chunk)

        # Build context-enriched text for embedding
        if section_title:
            context_text = f"{section_title}\n\n{raw_text}"
        else:
            context_text = raw_text

        chunks.append(
            Chunk(
                text=raw_text,
                context_text=context_text,
                section_title=section_title,
                chunk_type=chunk_type,
            )
        )

    return chunks


def _extract_heading(chunk) -> str:
    """Extract the closest parent heading from a Docling chunk."""
    # Docling chunks carry headings in their metadata
    try:
        meta = chunk.meta
        if meta and hasattr(meta, "headings") and meta.headings:
            return meta.headings[-1]  # innermost heading
    except (AttributeError, TypeError):
        pass
    return ""


def _detect_chunk_type(chunk) -> str:
    """Detect chunk type from Docling chunk metadata."""
    try:
        # Docling labels items with their document element type
        if hasattr(chunk, "meta") and chunk.meta:
            doc_items = getattr(chunk.meta, "doc_items", [])
            if doc_items:
                label = str(doc_items[0].label).lower()
                if "table" in label:
                    return "table"
                if "code" in label:
                    return "code"
                if "title" in label or "heading" in label:
                    return "heading"
    except (AttributeError, TypeError):
        pass
    return "text"
