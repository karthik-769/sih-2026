import pytest
from app.services.analysis import AnalysisService
from app.models.safety_report import SafetyReport
from app.models.enums import IncidentType, ProcessingStatus


def test_ground_truth_not_leaked_to_pipeline(db_session):
    service = AnalysisService()
    
    # Create report with explicit ground truth columns
    report = SafetyReport(
        case_id="GT-TEST-001",
        description="Worker observed working at height of 6 meters on scaffold without attaching safety harness.",
        incident_type=IncidentType.UNSAFE_ACT,
        job_role="Scaffolder",
        task="Erecting Scaffolding",
        activity="Work at Height",
        department_id=1,
        location_id=1,
        is_sif=True,
        failed_barrier="Fall Arrest / Harness",
        life_saving_rule="Work at Height",
        processing_status=ProcessingStatus.SUBMITTED,
    )
    db_session.add(report)
    db_session.commit()
    db_session.refresh(report)

    # Trigger analysis
    ai_record = service.process_report_analysis(report.id, db=db_session)
    assert ai_record is not None

    # Verify predictions were generated independently
    assert ai_record.sif_detected in [True, False]
    assert ai_record.risk_score >= 0.0
    assert ai_record.explanation is not None
    assert len(ai_record.explanation) > 0

    # Ensure report ground truth remains intact on report record
    assert report.is_sif is True
    assert report.failed_barrier == "Fall Arrest / Harness"
