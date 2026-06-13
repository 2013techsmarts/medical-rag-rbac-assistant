import re

from medibot.llm.provider import get_llm
from medibot.rag.prompts.sql_prompt import TEXT_TO_SQL_PROMPT


def clean_sql(raw_sql: str) -> str:
    """
    Clean the SQL string returned by the LLM.
    Strips markdown code fences (```sql ... ```) and leading/trailing whitespace.
    
    Args:
        raw_sql: The raw string response from LLM.
        
    Returns:
        A clean SQL query string.
    """
    # Regex to match ```sql ... ``` or ``` ... ``` code blocks
    match = re.search(r"```(?:sql)?\s*(.*?)\s*```", raw_sql, re.DOTALL | re.IGNORECASE)
    if match:
        cleaned = match.group(1)
    else:
        cleaned = raw_sql

    cleaned = cleaned.strip()

    # Strip wrapping quotes if the model wrapped the query in single/double quotes or backticks
    if (
        (cleaned.startswith("'") and cleaned.endswith("'"))
        or (cleaned.startswith('"') and cleaned.endswith('"'))
        or (cleaned.startswith("`") and cleaned.endswith("`"))
    ):
        cleaned = cleaned[1:-1].strip()

    # Remove trailing semicolon if present
    if cleaned.endswith(";"):
        cleaned = cleaned[:-1].strip()

    return cleaned


def generate_sql(question: str) -> str:
    """
    Generate an SQL query using ChatGroq for a given question.
    
    Args:
        question: User's natural language question.
        
    Returns:
        A cleaned SQLite query string.
    """
    llm = get_llm()
    prompt = TEXT_TO_SQL_PROMPT.format_prompt(question=question)
    response = llm.invoke(prompt)
    raw_sql = str(response.content)
    return clean_sql(raw_sql)
