import pytest
from fastapi.testclient import TestClient
from app.services.ai_evaluation.evaluation_service import AiEvaluationService
from app.core.security import create_access_token


@pytest.fixture
def admin_headers():
    token = create_access_token({"sub": "admin@safetyintelligence.internal", "role": "ADMIN"})
    return {"Authorization": f"Bearer {token}"}


def test_ai_evaluation_metrics_calculation(db_session):
    service = AiEvaluationService()
    eval_response = service.evaluate(db_session)

    assert eval_response is not None
    assert eval_response.evaluated_records_count >= 0
    assert eval_response.pipeline_version is not None
    
    # Check overall SIF metrics
    sif_metrics = eval_response.sif_classification
    assert 0.0 <= sif_metrics.accuracy <= 100.0
    assert 0.0 <= sif_metrics.precision <= 100.0
    assert 0.0 <= sif_metrics.recall <= 100.0
    assert 0.0 <= sif_metrics.f1_score <= 100.0

    # Check SIF counts consistency
    assert sif_metrics.true_positives + sif_metrics.false_positives + sif_metrics.true_negatives + sif_metrics.false_negatives >= 0

    # Check LSR macro metrics
    lsr_metrics = eval_response.life_saving_rules
    assert 0.0 <= lsr_metrics.macro_precision <= 100.0
    assert 0.0 <= lsr_metrics.macro_recall <= 100.0
    assert 0.0 <= lsr_metrics.macro_f1 <= 100.0

    # Check rule breakdown
    assert isinstance(lsr_metrics.rule_performance, list)
    assert lsr_metrics.confusion_matrix is not None
    assert len(lsr_metrics.confusion_matrix.labels) > 0


def test_ai_evaluation_api_endpoint(client, admin_headers):
    response = client.get("/api/analytics/ai-evaluation", headers=admin_headers)
    assert response.status_code == 200
    data = response.json()
    assert "evaluated_records_count" in data
    assert "sif_classification" in data
    assert "life_saving_rules" in data
    assert "pipeline_version" in data
