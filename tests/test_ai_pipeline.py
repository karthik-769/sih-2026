import pytest
from app.ai.pipeline import AiAnalysisPipeline
from app.ai.hazard_detector import HazardDetectionService
from app.ai.control_failure_detector import ControlFailureDetectionService
from app.ai.exposure_detector import ExposureDetectionService
from app.ai.sif_detector import SifDetectionService
from app.ai.risk_engine import RiskEngineService
from app.ai.explanation_engine import ExplanationService
from app.ai.recommendation_engine import RecommendationService
from app.ai.similarity_engine import SimilarityService


def _get_auth_headers(client, email, password):
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def pipeline():
    return AiAnalysisPipeline()


def test_1_normal_low_risk_observation(pipeline):
    """
    Test 1 — Normal low-risk observation
    Input: "A worker noticed a small amount of water near the entrance and cleaned the area."
    Expected: Low/Medium risk, No SIF precursor.
    """
    text = "A worker noticed a small amount of water near the entrance and cleaned the area."
    result = pipeline.process(text)

    assert result.sif_precursor is False
    assert result.risk_level in ["LOW", "MEDIUM"]
    assert result.risk_score <= 40.0
    assert "cleaned the area" in " ".join(result.highlighted_evidence).lower() or len(result.highlighted_evidence) > 0


def test_2_confined_space_critical_case(pipeline):
    """
    Test 2 — Confined-space critical case
    Input: "During maintenance, a worker entered a confined space without atmospheric testing. No standby person was present."
    Expected:
    - Confined Space hazard
    - Control failures detected (no atmospheric testing, no standby person)
    - Worker exposure detected
    - SIF precursor = YES
    - High/Critical risk
    - Relevant explanation and recommendations
    """
    text = "During maintenance, a worker entered a confined space without atmospheric testing. No standby person was present."
    result = pipeline.process(text)

    hazard_types = [h["hazard_type"] for h in result.hazards]
    hazard_categories = [h["category"] for h in result.hazards]
    assert "CONFINED_SPACE" in hazard_categories or any("Confined" in ht for ht in hazard_types)

    failed_controls = [cf["failed_control"] for cf in result.control_failures]
    assert any("atmospheric testing" in fc.lower() or "gas test" in fc.lower() for fc in failed_controls)
    assert any("standby" in fc.lower() for fc in failed_controls)

    assert result.sif_precursor is True
    assert result.sif_detected is True
    assert "Confined Space" in result.sif_categories or any("Confined" in c for c in result.sif_categories)
    assert result.risk_level in ["HIGH", "CRITICAL"]
    assert result.risk_score >= 70.0

    # Explanation and recommendations
    assert len(result.explanation) > 20
    assert "confined space" in result.explanation.lower()
    assert len(result.recommendations) >= 2
    rec_titles = [r["action_title"].lower() for r in result.recommendations]
    assert any("atmospheric" in t or "standby" in t or "permit" in t for t in rec_titles)


def test_3_working_at_height_critical_case(pipeline):
    """
    Test 3 — Working at height
    Input: "A worker was performing maintenance at height without proper fall protection."
    Expected:
    - Working at Height hazard
    - Missing Fall Protection
    - SIF precursor = YES
    - High/Critical risk
    """
    text = "A worker was performing maintenance at height without proper fall protection."
    result = pipeline.process(text)

    hazard_categories = [h["category"] for h in result.hazards]
    assert "WORKING_AT_HEIGHT" in hazard_categories

    failed_controls = [cf["failed_control"] for cf in result.control_failures]
    assert any("fall protection" in fc.lower() for fc in failed_controls)

    assert result.sif_precursor is True
    assert "Working at Height" in result.sif_categories
    assert result.risk_level in ["HIGH", "CRITICAL"]
    assert result.risk_score >= 70.0


def test_4_electrical_exposure_case(pipeline):
    """
    Test 4 — Electrical exposure
    Input: "An electrician began maintenance without isolating the electrical supply."
    Expected:
    - Electrical Exposure hazard
    - Energy Isolation Failure
    - SIF precursor = YES
    - High/Critical risk
    """
    text = "An electrician began maintenance without isolating the electrical supply."
    result = pipeline.process(text)

    hazard_categories = [h["category"] for h in result.hazards]
    assert "ELECTRICAL" in hazard_categories or "ENERGY_ISOLATION" in hazard_categories

    failed_controls = [cf["failed_control"] for cf in result.control_failures]
    assert any("isolation" in fc.lower() or "loto" in fc.lower() for fc in failed_controls)

    assert result.sif_precursor is True
    assert result.risk_level in ["HIGH", "CRITICAL"]
    assert result.risk_score >= 70.0


def test_5_safe_observation(pipeline):
    """
    Test 5 — Safe observation
    Input: "Workers were wearing required PPE and following the approved procedure during routine maintenance."
    Expected:
    - No major SIF precursor
    - Low risk
    """
    text = "Workers were wearing required PPE and following the approved procedure during routine maintenance."
    result = pipeline.process(text)

    assert result.sif_precursor is False
    assert result.risk_level == "LOW"
    assert result.risk_score <= 24.0
    assert len(result.control_failures) == 0


def test_pipeline_evidence_and_similarity_features(pipeline):
    """
    Tests highlighted evidence extraction and feature vector generation.
    """
    text = "Technician entered a confined space without atmospheric testing."
    result = pipeline.process(text)

    assert len(result.highlighted_evidence) > 0
    assert any("confined space" in e.lower() for e in result.highlighted_evidence)
    assert len(result.feature_vector) > 0
    assert len(result.recommendations) > 0


def test_api_analysis_endpoints(client):
    """
    Tests POST /api/reports/{id}/analyze, GET /api/reports/{id}/analysis, and GET /api/reports/{id}/similar.
    """
    worker_headers = _get_auth_headers(client, "worker@safetyintelligence.internal", "Worker@2026")
    admin_headers = _get_auth_headers(client, "admin@safetyintelligence.internal", "Admin@2026")

    # 1. Create a new report
    create_payload = {
        "job_role": "Process Tech",
        "department_id": 1,
        "location_id": 1,
        "task": "Valve Testing",
        "incident_type": "UNSAFE_ACT",
        "description": "During maintenance, a worker entered a confined space without atmospheric testing.",
    }
    create_res = client.post("/api/reports", json=create_payload, headers=worker_headers)
    assert create_res.status_code == 201
    rep_data = create_res.json()
    report_id = rep_data["id"]

    # 2. Trigger analysis via POST /api/reports/{id}/analyze
    reanalyze_res = client.post(f"/api/reports/{report_id}/analyze", headers=worker_headers)
    assert reanalyze_res.status_code == 200
    reanalyze_data = reanalyze_res.json()
    assert reanalyze_data["processing_status"] == "ANALYZED"
    assert reanalyze_data["analysis"] is not None

    # 3. GET /api/reports/{id}/analysis
    analysis_res = client.get(f"/api/reports/{report_id}/analysis", headers=worker_headers)
    assert analysis_res.status_code == 200
    analysis_data = analysis_res.json()
    assert analysis_data["report_id"] == report_id
    assert analysis_data["sif_precursor"] is True
    assert "Confined Space" in analysis_data["sif_categories"] or any("Confined" in c for c in analysis_data["sif_categories"])
    assert analysis_data["risk_level"] in ["HIGH", "CRITICAL"]

    # 4. GET /api/reports/{id}/similar
    similar_res = client.get(f"/api/reports/{report_id}/similar", headers=admin_headers)
    assert similar_res.status_code == 200
    similar_data = similar_res.json()
    assert "similar_reports_count" in similar_data
    assert "similar_reports" in similar_data
