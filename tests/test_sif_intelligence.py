import pytest
from app.ai.pipeline import AiAnalysisPipeline
from app.ai.interfaces import PreprocessedText
from app.ai.activity_extraction.service import ActivityExtractionService
from app.ai.life_saving_rules.service import LifeSavingRuleMappingService
from app.ai.consequence_detection.service import ConsequenceDetectionService
from app.services.analytics.analytics_service import analytics_service
from app.services.analysis import analysis_service


@pytest.fixture
def pipeline():
    return AiAnalysisPipeline()


def test_sif_detection_confined_space_without_gas_testing(pipeline):
    """
    Test Confined space without gas testing -> SIF Precursor (HIGH/CRITICAL)
    """
    text = "Worker entered the vessel for cleaning without atmospheric testing. No standby person was present at the entry point."
    result = pipeline.process(text)

    assert result.sif_precursor is True
    assert result.sif_level in ["HIGH", "CRITICAL"]
    assert result.fatality_potential is True
    assert result.life_saving_rule == "Confined Space"
    assert any("Atmospheric Testing" in b.get("barrier_name", "") for b in result.failed_barriers)
    assert any("Standby Person" in b.get("barrier_name", "") for b in result.failed_barriers)
    assert "asphyxiation" in result.potential_consequence.lower() or "toxic" in result.potential_consequence.lower()


def test_sif_detection_electrical_without_loto(pipeline):
    """
    Test Electrical without LOTO -> SIF Precursor (HIGH/CRITICAL) + Energy Isolation Rule
    """
    text = "During pump maintenance, technician opened the electrical panel without applying LOTO. The equipment remained energized."
    result = pipeline.process(text)

    assert result.sif_precursor is True
    assert result.sif_level in ["HIGH", "CRITICAL"]
    assert result.life_saving_rule in ["Energy Isolation", "Electrical Safety"]
    assert any("LOTO" in b.get("barrier_name", "") for b in result.failed_barriers)
    assert result.actual_consequence in ["No injury", "No injury (Near-miss)"]
    assert "electrocution" in result.potential_consequence.lower() or "arc-flash" in result.potential_consequence.lower()


def test_sif_detection_working_at_height(pipeline):
    """
    Test Work at height without fall arrest -> SIF Precursor + Work at Height Rule
    """
    text = "Technician accessed the elevated platform without connecting the fall arrest lanyard. The worker was exposed to an unprotected edge."
    result = pipeline.process(text)

    assert result.sif_precursor is True
    assert result.life_saving_rule == "Work at Height"
    assert any("Fall Protection" in b.get("barrier_name", "") for b in result.failed_barriers)


def test_safe_controlled_work_is_not_sif(pipeline):
    """
    Test Safe controlled work is NOT automatically SIF even in high-hazard environment.
    """
    text = "Worker entered confined space after gas testing and standby person verification was completed successfully."
    result = pipeline.process(text)

    assert result.sif_precursor is False
    assert result.sif_level == "NONE"
    assert result.risk_level == "LOW"


def test_activity_extraction(pipeline):
    """
    Test Operational Activity & Category Extraction.
    """
    text = "Carried out pump maintenance on crude oil feed pump #2 and replaced mechanical seal."
    result = pipeline.process(text)

    assert result.activity == "Pump Maintenance"
    assert result.activity_category == "Maintenance & Integrity"


def test_consequence_actual_vs_potential(pipeline):
    """
    Test Actual outcome vs Potential worst-case outcome divergence.
    """
    text = "Worker stood within the swing radius of a suspended load during lifting operations. No injury occurred."
    result = pipeline.process(text)

    assert result.actual_consequence in ["No injury (Near-miss)", "No injury"]
    assert "fatal" in result.potential_consequence.lower() or "trauma" in result.potential_consequence.lower() or "crush" in result.potential_consequence.lower()
    assert result.fatality_potential is True


def test_sif_density_analytics(db_session):
    """
    Verifies SIF Precursor Density formula = (SIF reports / total reports) * 100.
    """
    density_data = analytics_service.get_sif_density(db_session)
    
    assert density_data.total_reports >= 0
    assert 0.0 <= density_data.overall_density <= 100.0
    if density_data.total_reports > 0:
        expected_density = round((density_data.total_sif_precursors / density_data.total_reports) * 100.0, 1)
        assert density_data.overall_density == expected_density


def test_hse_review_and_override_workflow(client, db_session):
    """
    Test Human-in-the-loop HSE review (Confirm & Override) endpoint.
    """
    admin_login = client.post("/api/auth/login", json={"email": "admin@safetyintelligence.internal", "password": "Admin@2026"})
    token = admin_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Submit a report
    report_res = client.post("/api/reports", json={
        "job_role": "Operator",
        "department_id": 1,
        "location_id": 1,
        "task": "Pump Servicing",
        "incident_type": "UNSAFE_ACT",
        "description": "Technician opened electrical panel without applying LOTO. Equipment remained energized.",
    }, headers=headers)
    assert report_res.status_code == 201
    rep_id = report_res.json()["id"]

    # 2. Confirm AI Assessment
    confirm_res = client.post(f"/api/reports/{rep_id}/review", json={
        "action": "CONFIRM",
        "comment": "Confirmed by Lead HSE Auditor",
    }, headers=headers)
    assert confirm_res.status_code == 200
    c_data = confirm_res.json()
    assert c_data["success"] is True
    assert c_data["review_status"] == "CONFIRMED"

    # 3. Override AI Assessment
    override_res = client.post(f"/api/reports/{rep_id}/review", json={
        "action": "OVERRIDE",
        "sif_level": "CRITICAL",
        "risk_score": 95.0,
        "comment": "Escalated to Critical due to 6.6kV line proximity",
    }, headers=headers)
    assert override_res.status_code == 200
    o_data = override_res.json()
    assert o_data["success"] is True
    assert o_data["review_status"] == "OVERRIDDEN"
    assert o_data["final_decision"]["sif_level"] == "CRITICAL"
    assert o_data["final_decision"]["risk_score"] == 95.0
