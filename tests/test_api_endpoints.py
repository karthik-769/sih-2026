def test_get_departments_endpoint(client):
    """
    Test GET /api/departments returns 200 and list of departments.
    """
    response = client.get("/api/departments")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    names = [d["name"] for d in data]
    assert "Mechanical" in names
    assert "Electrical" in names
    assert "Operations" in names


def test_get_locations_endpoint(client):
    """
    Test GET /api/locations returns 200 and list of locations.
    """
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    names = [loc["name"] for loc in data]
    assert "Unit A" in names
    assert "Unit B" in names
    assert "Unit C" in names


def test_v1_departments_and_locations(client):
    """
    Test GET /api/v1/departments and /api/v1/locations endpoints.
    """
    res_dept = client.get("/api/v1/departments")
    assert res_dept.status_code == 200
    assert len(res_dept.json()) >= 3

    res_loc = client.get("/api/v1/locations")
    assert res_loc.status_code == 200
    assert len(res_loc.json()) >= 3


def test_root_endpoint_metadata(client):
    """
    Test GET / root metadata includes departments and locations.
    """
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "/api/departments" in data["endpoints"]
    assert "/api/locations" in data["endpoints"]
