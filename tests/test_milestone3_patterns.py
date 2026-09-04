import os
import io
import time
from datetime import datetime, timezone, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
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


def test_rbac_worker_forbidden_milestone3_endpoints(client, worker_headers):
    """Verifies that Worker role is denied access to admin patterns, alerts, analytics, and admin reporting."""
    assert client.get("/api/patterns", headers=worker_headers).status_code == 403
    assert client.get("/api/alerts", headers=worker_headers).status_code == 403
    assert client.post("/api/corrective-actions", json={"title": "test"}, headers=worker_headers).status_code == 403
    assert client.get("/api/analytics/kpis", headers=worker_headers).status_code == 403
    assert client.get("/api/analytics/risk-map", headers=worker_headers).status_code == 403
    assert client.get("/api/reporting/summary", headers=worker_headers).status_code == 403


def test_pattern_detection_and_early_warning_evaluation(client, admin_headers):
    """
    Test 1: Confined Space Pattern & Alert Generation
    Verifies pattern detection across historical confined space incidents and data-backed alert generation.
    """
    # 1. Trigger pattern recompute
    res = client.post("/api/patterns/recompute", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data["patterns_detected"] >= 1

    # 2. List patterns
    p_res = client.get("/api/patterns", headers=admin_headers)
    assert p_res.status_code == 200
    p_data = p_res.json()
    assert p_data["total"] >= 1

    # Check for Confined Space pattern or Hazard pattern
    patterns = p_data["items"]
    pattern_keys = [p["pattern_key"] for p in patterns]
    assert any("HAZ" in pk or "LOC" in pk or "DEPT" in pk for pk in pattern_keys)

    # Check detail of top pattern
    top_p = patterns[0]
    detail_res = client.get(f"/api/patterns/{top_p['id']}", headers=admin_headers)
    assert detail_res.status_code == 200
    d_data = detail_res.json()
    assert "scoring_factors" in d_data
    assert "recommendations" in d_data
    assert "contributing_reports" in d_data


def test_alert_generation_and_deduplication(client, admin_headers):
    """
    Test 2: Alert Generation & Deduplication
    Verifies alert generation, evidence explanations, and that recomputing does NOT create duplicate active alerts.
    """
    # First check
    res1 = client.get("/api/alerts", headers=admin_headers)
    assert res1.status_code == 200
    total1 = res1.json()["total"]

    # Trigger recompute
    client.post("/api/patterns/recompute", headers=admin_headers)

    # Second check - should deduplicate and not inflate count
    res2 = client.get("/api/alerts", headers=admin_headers)
    assert res2.status_code == 200
    total2 = res2.json()["total"]
    assert total2 == total1

    if total2 > 0:
        alert = res2.json()["items"][0]
        assert alert["severity"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
        assert len(alert["explanation_evidence"]) >= 1

        # Check alert detail
        a_detail = client.get(f"/api/alerts/{alert['id']}", headers=admin_headers)
        assert a_detail.status_code == 200
        ad_data = a_detail.json()
        assert "explanation_evidence" in ad_data
        assert "contributing_reports" in ad_data

        # Update alert status to ACKNOWLEDGED
        patch_res = client.patch(
            f"/api/alerts/{alert['id']}",
            json={"status": "ACKNOWLEDGED", "notes": "Safety team notified."},
            headers=admin_headers,
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "ACKNOWLEDGED"


def test_corrective_action_lifecycle_and_overdue_detection(client, admin_headers):
    """
    Test 3: Corrective Action Workflow
    Verifies action creation, assignment, overdue auto-flagging, and resolution.
    """
    # 1. Create action with past due date (overdue)
    past_due = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    action_payload = {
        "title": "Mandate Atmospheric Gas Testing in Unit C",
        "description": "Continuous gas monitoring equipment must be calibrated and staged at Unit C vessel manhole.",
        "recommended_action": "Install 4-gas multi-sensor monitor and assign dedicated standby personnel.",
        "priority": "CRITICAL",
        "due_date": past_due,
    }

    create_res = client.post("/api/corrective-actions", json=action_payload, headers=admin_headers)
    assert create_res.status_code == 201
    act_data = create_res.json()
    action_id = act_data["id"]
    assert act_data["status"] == "OVERDUE"
    assert act_data["is_overdue"] is True

    # 2. List actions and verify overdue filter
    list_res = client.get("/api/corrective-actions?status=OVERDUE", headers=admin_headers)
    assert list_res.status_code == 200
    assert any(a["id"] == action_id for a in list_res.json()["items"])

    # 3. Update action progress (Admin updates to IN_PROGRESS)
    future_due = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    update_res = client.patch(
        f"/api/corrective-actions/{action_id}",
        json={"status": "IN_PROGRESS", "due_date": future_due, "resolution_notes": "Calibrated monitors staged."},
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "IN_PROGRESS"
    assert update_res.json()["is_overdue"] is False

    # 4. Mark action as RESOLVED
    res_res = client.patch(
        f"/api/corrective-actions/{action_id}",
        json={"status": "RESOLVED", "resolution_notes": "Permit process verified and operational."},
        headers=admin_headers,
    )
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "RESOLVED"
    assert res_res.json()["completed_at"] is not None


def test_advanced_safety_analytics_endpoints(client, admin_headers):
    """
    Test 4: Advanced Safety Analytics APIs
    Verifies KPIs, risk trends, hazard distributions, SIF trends, and top risk areas.
    """
    # 1. KPIs
    kpi_res = client.get("/api/analytics/kpis", headers=admin_headers)
    assert kpi_res.status_code == 200
    kpis = kpi_res.json()
    assert "total_reports" in kpis
    assert "critical_risk_count" in kpis
    assert "active_alerts_count" in kpis
    assert "open_actions_count" in kpis

    # 2. Risk Trend
    trend_res = client.get("/api/analytics/risk-trend?weeks=4", headers=admin_headers)
    assert trend_res.status_code == 200
    trends = trend_res.json()
    assert len(trends) == 4

    # 3. Hazard Trend
    haz_res = client.get("/api/analytics/hazard-trend", headers=admin_headers)
    assert haz_res.status_code == 200
    assert isinstance(haz_res.json(), list)

    # 4. SIF Trend
    sif_res = client.get("/api/analytics/sif-trend", headers=admin_headers)
    assert sif_res.status_code == 200
    sif_data = sif_res.json()
    assert "sif_count" in sif_data
    assert "sif_percentage" in sif_data

    # 5. Top Risk Areas
    top_res = client.get("/api/analytics/top-risk-areas", headers=admin_headers)
    assert top_res.status_code == 200
    top_areas = top_res.json()
    assert isinstance(top_areas, list)

    # 6. Risk Map Markers
    map_res = client.get("/api/analytics/risk-map", headers=admin_headers)
    assert map_res.status_code == 200
    markers = map_res.json()
    assert len(markers) >= 1
    assert "latitude" in markers[0]
    assert "longitude" in markers[0]
    assert "risk_level" in markers[0]


def test_reporting_summary_and_exports(client, admin_headers):
    """
    Test 5: Executive Reporting & Multi-Format Exports
    Verifies summary generation and CSV, Excel (.xlsx), and PDF (.pdf) file exports.
    """
    # 1. Summary
    sum_res = client.get("/api/reporting/summary?report_type=WEEKLY", headers=admin_headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert "report_title" in summary
    assert "risk_distribution" in summary
    assert "key_recommendations" in summary

    # 2. Export CSV
    csv_res = client.get("/api/reporting/export?report_type=WEEKLY&export_format=csv", headers=admin_headers)
    assert csv_res.status_code == 200
    assert "text/csv" in csv_res.headers.get("content-type", "")
    assert len(csv_res.content) > 50

    # 3. Export Excel (.xlsx)
    xlsx_res = client.get("/api/reporting/export?report_type=WEEKLY&export_format=xlsx", headers=admin_headers)
    assert xlsx_res.status_code == 200
    assert len(xlsx_res.content) > 100

    # 4. Export PDF (.pdf)
    pdf_res = client.get("/api/reporting/export?report_type=WEEKLY&export_format=pdf", headers=admin_headers)
    assert pdf_res.status_code == 200
    assert "application/pdf" in pdf_res.headers.get("content-type", "")
    assert len(pdf_res.content) > 100
