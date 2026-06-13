import pytest

from medibot.rag.sql import sql_rag_chain


def test_sql_rag_claims_count():
    """Verify text-to-SQL-to-answer on claims table count questions."""
    question = "How many total claims are in the database?"
    res = sql_rag_chain(question)
    
    assert "answer" in res
    assert "sql" in res
    
    sql = res["sql"].upper()
    assert "SELECT" in sql
    assert "CLAIMS" in sql
    assert "COUNT" in sql
    
    # Answer should be a string containing a number or text representation of the total count (e.g. 85)
    assert len(res["answer"]) > 0


def test_sql_rag_claims_aggregate():
    """Verify sum/average calculation query generation on claims."""
    question = "What is the total claimed amount across all claims?"
    res = sql_rag_chain(question)
    
    assert "answer" in res
    assert "sql" in res
    
    sql = res["sql"].upper()
    assert "SELECT" in sql
    assert "CLAIMS" in sql
    assert "SUM" in sql or "CLAIMED_AMOUNT" in sql
    
    assert len(res["answer"]) > 0


def test_sql_rag_maintenance_tickets():
    """Verify querying maintenance tickets table."""
    question = "How many open maintenance tickets are raised from campus or overall?"
    res = sql_rag_chain(question)
    
    assert "answer" in res
    assert "sql" in res
    
    sql = res["sql"].upper()
    assert "SELECT" in sql
    assert "MAINTENANCE_TICKS" in sql or "MAINTENANCE_TICKETS" in sql
    assert "STATUS" in sql
    
    assert len(res["answer"]) > 0


def test_sql_rag_safety_block():
    """Verify SQL executor raises ValueError on non-SELECT commands."""
    from medibot.rag.sql.sql_executor import run_sql
    
    with pytest.raises(ValueError, match="Security block"):
        run_sql("DELETE FROM claims WHERE claim_id = '123'")
        
    with pytest.raises(ValueError, match="Security block"):
        run_sql("DROP TABLE maintenance_tickets")
        
    with pytest.raises(ValueError, match="Security block"):
        run_sql("INSERT INTO claims (claim_id) VALUES ('123')")
