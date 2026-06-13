from langchain_groq import ChatGroq

from medibot.config.settings import settings

_llm: ChatGroq | None = None


def get_llm() -> ChatGroq:
    """
    Get the singleton ChatGroq LLM client.
    Initialises it on the first call with configured settings.
    
    Returns:
        ChatGroq client.
    """
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model,
            temperature=0.0,  # 0.0 temperature for deterministic outputs (SQL, RAG)
        )
    return _llm
