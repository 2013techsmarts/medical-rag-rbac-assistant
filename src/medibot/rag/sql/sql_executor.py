from medibot.database.sqlite import execute_query


def run_sql(sql: str) -> tuple[list[str], list[tuple]]:
    """
    Safely executes an SQL query on the database.
    Only allows read-only SELECT statements.
    
    Args:
        sql: Cleaned SQL query string.
        
    Returns:
        A tuple of (columns_list, rows_list).
        
    Raises:
        ValueError: If the query is not a SELECT statement.
    """
    # Standardise whitespace and check if it starts with SELECT
    sql_upper = sql.strip().upper()
    
    # Block writing, schema modifications or administrative commands
    if not sql_upper.startswith("SELECT"):
        raise ValueError(
            "Security block: Only SELECT (read-only) operations are allowed."
        )

    # Secondary keywords check just in case of nested write operations
    restricted_keywords = ["INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "REPLACE"]
    for keyword in restricted_keywords:
        if f" {keyword} " in f" {sql_upper} ":
            raise ValueError(
                f"Security block: Found restricted keyword '{keyword}'."
            )

    return execute_query(sql)
