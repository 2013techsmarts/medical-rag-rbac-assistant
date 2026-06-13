from langchain_community.utilities import SQLDatabase
from pydantic import BaseModel, Field

from medibot.config.settings import settings
from medibot.llm.provider import get_llm
from medibot.rag.prompts.sql_prompt import TEXT_TO_SQL_PROMPT


class SqlGeneration(BaseModel):
    """Schema for validating and parsing the generated SQLite query."""
    sql_query: str = Field(
        description="A syntactically correct SQLite SELECT query based on the table schemas."
    )


# Singleton SQLDatabase instance
_db: SQLDatabase | None = None


def get_schema_info() -> str:
    """Connect to the SQLite database and extract table DDL schemas and sample rows."""
    global _db
    if _db is None:
        # Construct absolute path URI for the sqlite database
        _db = SQLDatabase.from_uri(f"sqlite:///{settings.database_path}")
    return _db.get_table_info()


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
    
    # Fetch dynamic table structures and sample values
    schema_info = get_schema_info()
    
    # Format and invoke with dynamic schema info
    prompt = TEXT_TO_SQL_PROMPT.format_prompt(
        schema_info=schema_info,
        question=question
    )
    result = structured_llm.invoke(prompt)
    
    # Extract query and strip extra whitespace
    return result.sql_query.strip()
