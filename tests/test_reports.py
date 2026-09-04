import pytest
from app.models.enums import IncidentType, ProcessingStatus


def _get_auth_headers(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_report_valid_auto_case_id(client):
    """
    Test submitting a valid report with auto-generated Case ID.
    """
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")

    # Get department and location IDs
    dept_id = client.get("/api/departments").json()[0]["id"]
    loc_id = client.get("/api/locations").json()[0]["id"]

    raw_description = "Observed oil leakage on primary gearbox casing creating slip hazard near walkway."

    payload = {
        "job_role": "Maintenance Fitter",
        "department_id": dept_id,
        "location_id": loc_id,
        "task": "Daily Gearbox Inspection",
        "incident_type": "UNSAFE_CONDITION",
        "description": raw_description,
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["case_id"].startswith("CASE-")
    assert data["processing_status"] in ["SUBMITTED", "ANALYZED"]
    assert data["description"] == raw_description
    assert data["task"] == "Daily Gearbox Inspection"
    assert data["department"]["id"] == dept_id
    assert data["location"]["id"] == loc_id
    assert data["reporter"]["email"] == "worker@safetyintelligence.internal"


def test_create_report_valid_custom_case_id(client):
    """
    Test submitting a report with custom user-provided Case ID.
    """
    headers = _get_auth_headers(client, "admin@safetyintelligence.internal", "Admin@2026")
    dept_id = client.get("/api/departments").json()[0]["id"]
    loc_id = client.get("/api/locations").json()[0]["id"]

    custom_id = "CUSTOM-CASE-2026-999"
    payload = {
        "case_id": custom_id,
        "job_role": "Area Supervisor",
        "department_id": dept_id,
        "location_id": loc_id,
        "task": "Emergency Lighting Test",
        "incident_type": "SAFETY_OBSERVATION",
        "description": "All emergency backup fixtures in Substation 3 responded within 1.2 seconds of simulated power cut.",
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["case_id"] == custom_id


def test_create_report_duplicate_case_id(client):
    """
    Test submitting duplicate Case ID returns 400 Bad Request.
    """
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")
    dept_id = client.get("/api/departments").json()[0]["id"]
    loc_id = client.get("/api/locations").json()[0]["id"]

    # Use existing seeded case_id
    payload = {
        "case_id": "SYN-2026-001",
        "job_role": "Fitter",
        "department_id": dept_id,
        "location_id": loc_id,
        "task": "Duplicate test task",
        "incident_type": "UNSAFE_ACT",
        "description": "Attempting to create report with already existing case_id.",
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["error"]["message"].lower() or "already exists" in str(response.json()).lower()


def test_create_report_description_too_short(client):
    """
    Test submitting description < 10 characters fails validation with 422.
    """
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")
    dept_id = client.get("/api/departments").json()[0]["id"]
    loc_id = client.get("/api/locations").json()[0]["id"]

    payload = {
        "job_role": "Fitter",
        "department_id": dept_id,
        "location_id": loc_id,
        "task": "Inspection",
        "incident_type": "UNSAFE_ACT",
        "description": "Too short",  # 9 chars
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 422


def test_create_report_missing_fields(client):
    """
    Test submitting payload with missing required fields returns 422.
    """
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")

    payload = {
        "job_role": "Fitter",
        # missing department_id, location_id, task, description
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 422


def test_create_report_invalid_department(client):
    """
    Test submitting non-existent department_id returns 400.
    """
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")
    loc_id = client.get("/api/locations").json()[0]["id"]

    payload = {
        "job_role": "Fitter",
        "department_id": 99999,  # non-existent
        "location_id": loc_id,
        "task": "Testing Task",
        "incident_type": "UNSAFE_ACT",
        "description": "Valid description text for invalid department testing.",
    }

    response = client.post("/api/reports", json=payload, headers=headers)
    assert response.status_code == 400


def test_create_report_unauthenticated(client):
    """
    Test unauthenticated POST /api/reports returns 401.
    """
    response = client.post("/api/reports", json={})
    assert response.status_code == 401


def test_worker_report_scoping(client):
    """
    Test Worker only sees reports authored by their user account.
    """
    headers_worker = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")

    response = client.get("/api/reports", headers=headers_worker)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    # Verify all returned reports belong to this worker
    for item in data["items"]:
        assert item["reporter"]["email"] == "worker@safetyintelligence.internal"


def test_admin_report_scoping(client):
    """
    Test Admin sees all reports across all users and departments.
    """
    headers_admin = _get_auth_headers(client, "admin@safetyintelligence.internal", "Admin@2026")

    response = client.get("/api/reports", headers=headers_admin)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 5
    # Should include reports from worker and admin
    reporters = {item["reporter"]["email"] for item in data["items"] if item.get("reporter")}
    assert "worker@safetyintelligence.internal" in reporters or "admin@safetyintelligence.internal" in reporters


def test_list_reports_filters_and_pagination(client):
    """
    Test filtering by incident_type, department_id, and search query.
    """
    headers_admin = _get_auth_headers(client, "admin@safetyintelligence.internal", "Admin@2026")

    # Filter by incident type NEAR_MISS
    res_type = client.get("/api/reports?incident_type=NEAR_MISS", headers=headers_admin)
    assert res_type.status_code == 200
    for item in res_type.json()["items"]:
        assert item["incident_type"] == "NEAR_MISS"

    # Search keyword
    res_search = client.get("/api/reports?search=SYN-2026-001", headers=headers_admin)
    assert res_search.status_code == 200
    assert len(res_search.json()["items"]) >= 1
    assert res_search.json()["items"][0]["case_id"] == "SYN-2026-001"

    # Pagination
    res_page = client.get("/api/reports?page=1&page_size=2", headers=headers_admin)
    assert res_page.status_code == 200
    assert len(res_page.json()["items"]) <= 2
    assert res_page.json()["page"] == 1
    assert res_page.json()["page_size"] == 2


def test_get_report_by_id_and_forbidden_worker(client):
    """
    Test single report retrieval and 403 for unauthorized worker.
    """
    headers_worker = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")
    headers_admin = _get_auth_headers(client, "admin@safetyintelligence.internal", "Admin@2026")

    # Find a report created by admin (not worker)
    res_all = client.get("/api/reports", headers=headers_admin)
    admin_report = next(r for r in res_all.json()["items"] if r["reporter"]["email"] == "admin@safetyintelligence.internal")

    # 1. Worker tries to view admin's report -> 403 Forbidden
    res_forbidden = client.get(f"/api/reports/{admin_report['id']}", headers=headers_worker)
    assert res_forbidden.status_code == 403

    # 2. Admin views admin's report -> 200 OK
    res_allowed = client.get(f"/api/reports/{admin_report['id']}", headers=headers_admin)
    assert res_allowed.status_code == 200
    assert res_allowed.json()["case_id"] == admin_report["case_id"]


def test_end_to_end_submission_and_retrieval(client):
    """
    Complete flow:
    Login -> Submit Report -> Database Persist -> Query in List -> Open Detail View.
    """
    # 1. Login
    headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")

    # 2. Get master data
    dept = client.get("/api/departments").json()[0]
    loc = client.get("/api/locations").json()[0]

    # 3. Submit Report
    submit_payload = {
        "job_role": "High Pressure Welder",
        "department_id": dept["id"],
        "location_id": loc["id"],
        "task": "Boiler Steam Pipe Welding",
        "incident_type": "UNSAFE_ACT",
        "description": "Welder initiated hot work torch cutting without spark containment blanket or fire watcher on duty.",
    }
    submit_res = client.post("/api/reports", json=submit_payload, headers=headers)
    assert submit_res.status_code == 201
    created_report = submit_res.json()
    report_id = created_report["id"]
    case_id = created_report["case_id"]

    # 4. Query in list
    list_res = client.get(f"/api/reports?search={case_id}", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1
    assert list_res.json()["items"][0]["id"] == report_id

    # 5. Open report detail view
    detail_res = client.get(f"/api/reports/{report_id}", headers=headers)
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["case_id"] == case_id
    assert detail_data["task"] == "Boiler Steam Pipe Welding"
    assert detail_data["processing_status"] in ["SUBMITTED", "ANALYZED"]
    assert detail_data["description"] == submit_payload["description"]
