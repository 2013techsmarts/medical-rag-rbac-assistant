from pydantic import BaseModel, Field

from medibot.llm.provider import get_llm
from medibot.rag.prompts.sql_prompt import TEXT_TO_SQL_PROMPT


class SqlGeneration(BaseModel):
    """Schema for validating and parsing the generated SQLite query."""
    sql_query: str = Field(
        description="A syntactically correct SQLite SELECT query based on the table schemas."
    )


def generate_sql(question: str) -> str:
    """
    Generate an SQL query using ChatGroq for a given question.
    Uses LangChain's native structured output bindings to guarantee a clean SQL query.
    
    Args:
        question: User's natural language question.
        
    Returns:
        A validated SQLite query string.
    """
    llm = get_llm()
    
    # Bind Pydantic schema to ChatGroq
    structured_llm = llm.with_structured_output(SqlGeneration)
    
    # Format and invoke
    prompt = TEXT_TO_SQL_PROMPT.format_prompt(question=question)
    result = structured_llm.invoke(prompt)
    
    # Extract query and strip extra whitespace
    return result.sql_query.strip()
