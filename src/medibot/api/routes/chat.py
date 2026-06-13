from fastapi import APIRouter, Depends

from medibot.api.dependencies import get_current_role
from medibot.llm.provider import get_llm
from medibot.models.requests import ChatRequest
from medibot.models.responses import ChatResponse, Source
from medibot.rag.prompts.rag_prompt import RAG_PROMPT
from medibot.rag.retrieval import hybrid_search, rerank
from medibot.rag.sql import sql_rag_chain

router = APIRouter()

# Simple keyword classifier list to direct analytical questions to SQL RAG
ANALYTIC_KEYWORDS = [
    "how many",
    "count",
    "total",
    "average",
    "list all",
    "escalated",
    "approved",
    "rejected",
    "last month",
    "fault code",
    "ticket",
    "claim",
    "equipment",
    "campus",
    "sum of",
]


def is_analytical_question(question: str) -> bool:
    """Check if the user question has database/analytical intent."""
    q = question.lower()
    return any(keyword in q for keyword in ANALYTIC_KEYWORDS)


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest, current_role: str = Depends(get_current_role)):
    """
    RAG Chat Endpoint.
    
    If the question is analytical (count, average, lists) AND the user's role is
    'billing_executive' or 'admin', it routes to SQL RAG (Component 4).
    Otherwise, it routes to Hybrid RAG search and Cross-Encoder reranking.
    """
    question = request.question

    # 1. Routing Decision
    if (current_role in ["billing_executive", "admin"]) and is_analytical_question(question):
        # Route to SQL RAG
        result = sql_rag_chain(question)
        return ChatResponse(
            answer=result["answer"],
            sources=[],
            retrieval_type="sql_rag",
            role=current_role,
            sql_query=result["sql"],
        )

    # 2. Route to Hybrid RAG (Dense + BM25)
    candidates = hybrid_search(question, role=current_role, top_k=10)
    if not candidates:
        return ChatResponse(
            answer="I do not have sufficient information in your authorized documents to answer this question.",
            sources=[],
            retrieval_type="hybrid_rag",
            role=current_role,
        )

    # Rerank retrieved candidate chunks
    top_candidates = rerank(question, candidates, top_n=3)

    # Format context for LLM and build sources payload
    context_str = ""
    sources_payload = []
    seen_sources = set()

    for idx, cand in enumerate(top_candidates, 1):
        doc = cand.payload.get("source_document", "Unknown Document")
        section = cand.payload.get("section_title", "General")
        coll = cand.payload.get("collection", "general")
        text = cand.payload.get("text", "")

        context_str += f"[{idx}] Source: {doc} ({section})\nContext:\n{text}\n\n"

        source_key = (doc, section, coll)
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            sources_payload.append(
                Source(
                    source_document=doc,
                    section_title=section,
                    collection=coll,
                )
            )

    # Ask the LLM using context chunks
    llm = get_llm()
    prompt = RAG_PROMPT.format_prompt(context=context_str, question=question)
    response = llm.invoke(prompt)
    answer = str(response.content)

    return ChatResponse(
        answer=answer,
        sources=sources_payload,
        retrieval_type="hybrid_rag",
        role=current_role,
    )
