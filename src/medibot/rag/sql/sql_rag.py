from medibot.llm.provider import get_llm
from medibot.rag.prompts.sql_prompt import SQL_RESULT_TO_ANSWER_PROMPT
from medibot.rag.sql.sql_executor import run_sql
from medibot.rag.sql.sql_generator import generate_sql


def synthesise_answer(
    question: str, sql: str, columns: list[str], rows: list[tuple]
) -> str:
    """
    Synthesise a natural language answer from SQL execution result rows.
    
    Args:
        question: User's original question.
        sql: Cleaned SQL query string.
        columns: Column headers list.
        rows: List of tuple query results.
        
    Returns:
        A natural language response string.
    """
    llm = get_llm()
    prompt = SQL_RESULT_TO_ANSWER_PROMPT.format_prompt(
        question=question, sql=sql, columns=columns, rows=rows
    )
    response = llm.invoke(prompt)
    return str(response.content)


def sql_rag_chain(question: str) -> dict:
    """
    Orchestrate the entire Text-to-SQL-to-Answer pipeline.
    
    Args:
        question: Natural language query.
        
    Returns:
        Dictionary containing 'answer' and 'sql'.
    """
    # Step 1 & 2: Generate and clean SQL
    sql = generate_sql(question)

    # Step 3: Run the SQL query safely
    try:
        columns, rows = run_sql(sql)
    except Exception as e:
        err_msg = f"Generated query '{sql}' but failed to execute: {e}"
        return {"answer": err_msg, "sql": sql}

    # Step 4: Synthesise answer from data rows
    answer = synthesise_answer(question, sql, columns, rows)
    return {"answer": answer, "sql": sql}
