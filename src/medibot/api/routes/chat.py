from fastapi import APIRouter, Depends
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field

from medibot.api.dependencies import get_current_role
from medibot.llm.provider import get_llm
from medibot.models.requests import ChatRequest
from medibot.models.responses import ChatResponse, Source
from medibot.rag.prompts.rag_prompt import RAG_PROMPT
from medibot.rag.retrieval import hybrid_search, rerank
from medibot.rag.sql import sql_rag_chain

router = APIRouter()


class RouteDecision(BaseModel):
    """Schema for parsing the query routing decision."""
    route: str = Field(
        description="The target pipeline for the query, either 'sql_rag' or 'hybrid_rag'."
    )


def classify_query_route(question: str) -> str:
    """
    Classify the user question intent semantically using ChatGroq.
    
    Args:
        question: User query string.
        
    Returns:
        'sql_rag' or 'hybrid_rag'.
    """
    llm = get_llm()
    router_llm = llm.with_structured_output(RouteDecision)
    
    prompt = PromptTemplate.from_template(
        "Classify the question route.\n"
        "Available Routes:\n"
        "- sql_rag: Choose this for questions needing database counts, lists, averages, sums, statistics, ticket reports, or claim records.\n"
        "- hybrid_rag: Choose this for questions asking about policies, standards, leave protocols, faqs, instructions, or procedures.\n\n"
        "Question: {question}\n\n"
        "Route:"
    )
    
    try:
        formatted = prompt.format_prompt(question=question)
        result = router_llm.invoke(formatted)
        return result.route.strip().lower()
    except Exception:
        # Secure fallback to document hybrid search in case of classification issues
        return "hybrid_rag"


@router.post("/chat", response_model=ChatResponse, tags=["chat"])
def chat(request: ChatRequest, current_role: str = Depends(get_current_role)):
    """
    RAG Chat Endpoint.
    
    If the question has analytical intent (resolved semantically) AND the user's role is
    'billing_executive' or 'admin', it routes to SQL RAG (Component 4).
    Otherwise, it routes to Hybrid RAG search and Cross-Encoder reranking.
    """
    question = request.question

    # 1. Routing Decision (Only query LLM router if user has database privileges)
    route = "hybrid_rag"
    if current_role in ["billing_executive", "admin"]:
        route = classify_query_route(question)

    if route == "sql_rag":
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
