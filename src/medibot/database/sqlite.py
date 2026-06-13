import sqlite3
from pathlib import Path

from medibot.config.settings import settings


def execute_query(sql: str) -> tuple[list[str], list[tuple]]:
    """
    Execute an SQL query against the SQLite database in read-only mode.
    
    Args:
        sql: The SQL query string.
        
    Returns:
        A tuple of (column_names, rows).
    """
    # Resolve the absolute path to make URI connection robust
    db_path = Path(settings.database_path).resolve()
    
    # Establish connection with read-only URI parameter
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        # Extract column names from description
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        rows = cursor.fetchall()
        return columns, rows
    finally:
        conn.close()
