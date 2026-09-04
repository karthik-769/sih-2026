import os
import io
import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.database.session import get_db, SessionLocal
from app.models.safety_report import SafetyReport
from app.models.import_batch import ImportBatch
from app.models.ai_analysis import AiAnalysis
from app.core.security import create_access_token


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_headers():
    token = create_access_token({"sub": "admin@safetyintelligence.internal", "role": "ADMIN"})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def worker_headers():
    token = create_access_token({"sub": "worker@safetyintelligence.internal", "role": "WORKER"})
    return {"Authorization": f"Bearer {token}"}


def test_rbac_worker_denied_import(client, worker_headers):
    """Verifies that Worker role is forbidden from accessing import endpoints."""
    # Test file upload
    dummy_csv = io.BytesIO(b"Case ID,Description\nTEST01,Worker entered confined space.")
    res = client.post(
        "/api/imports/upload",
        files={"file": ("test.csv", dummy_csv, "text/csv")},
        headers=worker_headers,
    )
    assert res.status_code == 403

    # Test list imports
    res = client.get("/api/imports", headers=worker_headers)
    assert res.status_code == 403


def test_excel_import_and_ai_analysis(client, admin_headers):
    """
    Test 1 — Excel:
    Uploads sample_safety_reports.xlsx containing 5 reports.
    Verifies 5 reports extracted, preview generated, reports imported, and AI analyses triggered.
    """
    xlsx_path = os.path.join(os.path.dirname(__file__), "..", "backend", "samples", "sample_safety_reports.xlsx")
    assert os.path.exists(xlsx_path), f"Sample file not found at {xlsx_path}"

    with open(xlsx_path, "rb") as f:
        file_bytes = f.read()

    # 1. Upload & Preview
    res = client.post(
        "/api/imports/upload",
        files={"file": ("sample_safety_reports.xlsx", io.BytesIO(file_bytes), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["file_type"] == "EXCEL"
    assert data["total_records"] == 5
    assert len(data["rows"]) == 5
    batch_id = data["batch_id"]

    # Verify extracted Case IDs
    case_ids = [r["case_id"] for r in data["rows"]]
    assert "SIF001" in case_ids
    assert "SIF002" in case_ids
    assert "SIF003" in case_ids
    assert "SIF004" in case_ids
    assert "SAFE001" in case_ids

    # 2. Confirm Import with REPLACE (in case pre-existing) or SKIP
    confirm_res = client.post(
        f"/api/imports/{batch_id}/confirm",
        json={"duplicate_strategy": "REPLACE"},
        headers=admin_headers,
    )
    assert confirm_res.status_code == 200
    c_data = confirm_res.json()
    assert c_data["imported_count"] >= 5

    # 3. Verify reports via API and DB session
    time.sleep(1.0)  # Wait for background thread
    db = SessionLocal()
    try:
        for cid in ["SIF001", "SIF002", "SIF003", "SIF004", "SAFE001"]:
            report = db.query(SafetyReport).filter(SafetyReport.case_id == cid).first()
            assert report is not None
            assert report.source_type == "EXCEL"
            assert report.source_file == "sample_safety_reports.xlsx"

            # Check AI analysis created
            ai = db.query(AiAnalysis).filter(AiAnalysis.report_id == report.id).first()
            assert ai is not None
            assert ai.risk_score >= 0.0
    finally:
        db.close()


def test_csv_import_workflow(client, admin_headers):
    """
    Test 2 — CSV:
    Uploads structured CSV dataset with custom Case IDs.
    """
    csv_content = """Case ID,Job Role,Department,Location,Task,Incident Type,Date/Time,Description
CSV-TEST-001,Electrician,Electrical,Unit A,Breaker Rack Out,Near Miss,2026-09-02 10:00,Worker racked out 11kV circuit breaker while still under load without PPE.
CSV-TEST-002,Fitter,Mechanical,Unit B,Valve Overhaul,Unsafe Act,2026-09-02 11:30,Fitter used cheater pipe on wrench causing wrench to slip and strike hand.
"""
    # 1. Upload & Preview
    res = client.post(
        "/api/imports/upload",
        files={"file": ("test_data.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["file_type"] == "CSV"
    assert data["total_records"] == 2
    batch_id = data["batch_id"]

    # 2. Confirm
    confirm_res = client.post(
        f"/api/imports/{batch_id}/confirm",
        json={"duplicate_strategy": "SKIP"},
        headers=admin_headers,
    )
    assert confirm_res.status_code == 200

    # 3. Verify
    time.sleep(0.5)
    db = SessionLocal()
    try:
        r1 = db.query(SafetyReport).filter(SafetyReport.case_id == "CSV-TEST-001").first()
        assert r1 is not None
        assert "11kV" in r1.description
    finally:
        db.close()


def test_duplicate_case_id_handling(client, admin_headers):
    """
    Test 3 — Duplicate:
    Uploads CSV with an existing Case ID. Verifies duplicate warning and SKIP policy behavior.
    """
    csv_content = """Case ID,Job Role,Department,Location,Task,Incident Type,Description
DUP-CASE-001,Technician,Mechanical,Unit A,Pump Inspection,Unsafe Condition,Initial report for duplicate testing.
"""
    # First upload
    res1 = client.post(
        "/api/imports/upload",
        files={"file": ("dup1.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    batch_id1 = res1.json()["batch_id"]
    client.post(f"/api/imports/{batch_id1}/confirm", json={"duplicate_strategy": "SKIP"}, headers=admin_headers)

    # Second upload with same Case ID
    res2 = client.post(
        "/api/imports/upload",
        files={"file": ("dup2.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["duplicate_records"] == 1
    assert data2["rows"][0]["is_duplicate"] is True

    # Confirm with SKIP -> duplicate not inserted again
    batch_id2 = data2["batch_id"]
    conf2 = client.post(
        f"/api/imports/{batch_id2}/confirm",
        json={"duplicate_strategy": "SKIP"},
        headers=admin_headers,
    )
    assert conf2.status_code == 200
    assert conf2.json()["skipped_duplicates_count"] == 1


def test_invalid_row_handling(client, admin_headers):
    """
    Test 4 — Invalid row:
    Uploads a file where one row has an empty description.
    Verifies that the invalid row is marked ERROR and not silently imported.
    """
    csv_content = """Case ID,Job Role,Department,Location,Task,Description
VALID-ROW-01,Operator,Mechanical,Unit A,Filter Clean,Valid observation with adequate length description.
EMPTY-DESC-02,Operator,Mechanical,Unit A,Filter Clean,
"""
    res = client.post(
        "/api/imports/upload",
        files={"file": ("invalid_test.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_records"] == 2
    assert data["error_records"] == 1

    # Check that row 2 has status ERROR
    row2 = [r for r in data["rows"] if r["row_number"] == 3 or r.get("case_id") == "EMPTY-DESC-02"][0]
    assert row2["validation_status"] == "ERROR"
    assert any("Description is missing" in m for m in row2["validation_messages"])


def test_pdf_multi_report_extraction(client, admin_headers):
    """
    Test 5 — PDF:
    Uploads structured multi-report PDF (sample_safety_reports.pdf).
    Verifies extraction of multiple reports and preview generation.
    """
    pdf_path = os.path.join(os.path.dirname(__file__), "..", "backend", "samples", "sample_safety_reports.pdf")
    assert os.path.exists(pdf_path)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    res = client.post(
        "/api/imports/upload",
        files={"file": ("sample_safety_reports.pdf", io.BytesIO(file_bytes), "application/pdf")},
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["file_type"] == "PDF"
    assert data["total_records"] >= 3
    assert len(data["rows"]) >= 3

    batch_id = data["batch_id"]
    confirm_res = client.post(
        f"/api/imports/{batch_id}/confirm",
        json={"duplicate_strategy": "REPLACE"},
        headers=admin_headers,
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["imported_count"] >= 3


def test_import_history_and_progress(client, admin_headers):
    """
    Verifies Import History listing and real-time progress polling endpoint.
    """
    # List batches
    res = client.get("/api/imports", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert data["total"] >= 1

    batch_id = data["items"][0]["batch_id"]

    # Poll progress
    prog_res = client.get(f"/api/imports/{batch_id}/progress", headers=admin_headers)
    assert prog_res.status_code == 200
    prog_data = prog_res.json()
    assert "progress_percentage" in prog_data
    assert "status" in prog_data


