"""
SQL RAG package.
Provides translation of natural language questions into SQLite queries,
safe execution, and natural language answer generation.
"""

from .sql_rag import sql_rag_chain

__all__ = ["sql_rag_chain"]
