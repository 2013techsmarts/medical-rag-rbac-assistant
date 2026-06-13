from pydantic import BaseModel


class Source(BaseModel):
    source_document: str
    section_title: str
    collection: str


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieval_type: str  # "hybrid_rag" or "sql_rag"
    role: str
    sql_query: str | None = None  # Optional field showing executed SQL query if SQL RAG was triggered


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
