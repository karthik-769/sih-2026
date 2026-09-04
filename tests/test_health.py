def test_root_health_endpoint(client):
    """
    Test GET /health returns 200 and {"status": "ok"}.
    """
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}


def test_api_health_endpoint(client):
    """
    Test GET /api/health returns 200 and {"status": "ok"}.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok"}



def test_api_v1_health_endpoint(client):
    """
    Test GET /api/v1/health returns 200 and {"status": "ok"}.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_api_v1_health_details(client):
    """
    Test GET /api/v1/health/details returns 200 and structured diagnostics.
    """
    response = client.get("/api/v1/health/details")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "environment" in data
    assert "version" in data
    assert "database_connected" in data


def test_root_endpoint(client):
    """
    Test GET / returns 200 and basic API info.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["health"] == "/api/health"


def test_not_found_structured_error(client):
    """
    Test 404 responses are formatted properly according to exception handler.
    """
    response = client.get("/api/non-existent-endpoint-xyz")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == 404
