"""
Document parser using Docling.
Converts PDF and Markdown files into DoclingDocument objects
with structural awareness (headings, tables, code blocks).
"""
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption


def _build_converter() -> DocumentConverter:
    """Build a DocumentConverter with standard PDF pipeline options."""
    pdf_opts = PdfPipelineOptions()
    pdf_opts.do_ocr = False          # disable OCR — documents are digital
    pdf_opts.do_table_structure = True  # preserve table structure

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pdf_opts),
        }
    )


# Singleton converter (initialised once per process)
_converter: DocumentConverter | None = None


def get_converter() -> DocumentConverter:
    global _converter
    if _converter is None:
        _converter = _build_converter()
    return _converter


def parse_document(path: Path):
    """
    Parse a single PDF or Markdown file into a DoclingDocument.

    Args:
        path: Absolute path to the document.

    Returns:
        DoclingDocument object with structural metadata.
    """
    converter = get_converter()
    result = converter.convert(str(path))
    return result.document
