from fastapi.testclient import TestClient

from medibot.main import app

client = TestClient(app)


def test_health_endpoint():
    """Verify health status endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_login_success():
    """Verify successful login returns valid JWT token and correct role."""
    response = client.post(
        "/auth/login",
        json={"username": "dr.mehta", "password": "doctor"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["role"] == "doctor"


def test_auth_login_invalid():
    """Verify login fails with incorrect credentials."""
    response = client.post(
        "/auth/login",
        json={"username": "dr.mehta", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"


def test_collections_authenticated():
    """Verify authenticated user can retrieve their role-based collections."""
    # Login
    login_response = client.post(
        "/auth/login",
        json={"username": "nurse.priya", "password": "nurse"},
    )
    token = login_response.json()["access_token"]

    # Fetch collections
    response = client.get(
        "/collections",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "nurse"
    assert "general" in data["collections"]
    assert "nursing" in data["collections"]
    assert "clinical" not in data["collections"]


def test_collections_unauthorized():
    """Verify collections request is blocked without valid auth token."""
    response = client.get("/collections")
    assert response.status_code == 401


def test_chat_hybrid_rag_flow():
    """Verify chat route works for Hybrid RAG queries and applies RBAC."""
    # Login as nurse
    login_response = client.post(
        "/auth/login",
        json={"username": "nurse.priya", "password": "nurse"},
    )
    token = login_response.json()["access_token"]

    # Ask about ICU standard precautions (nursing collection)
    response = client.post(
        "/chat",
        json={"question": "What is the ICU nursing hand hygiene requirement?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["retrieval_type"] == "hybrid_rag"
    assert len(data["answer"]) > 0
    # There should be sources matching general or nursing collections
    assert len(data["sources"]) > 0
    for src in data["sources"]:
        assert src["collection"] in ["general", "nursing"]


def test_chat_sql_rag_flow_admin():
    """Verify chat route performs SQL RAG routing for analytical questions if admin."""
    # Login as admin
    login_response = client.post(
        "/auth/login",
        json={"username": "admin.sys", "password": "admin"},
    )
    token = login_response.json()["access_token"]

    # Ask an analytical question
    response = client.post(
        "/chat",
        json={"question": "How many total claims have resolved status?"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["retrieval_type"] == "sql_rag"
    assert "sql_query" in data
    assert data["sql_query"] is not None
    assert "SELECT" in data["sql_query"].upper()
    assert len(data["answer"]) > 0
