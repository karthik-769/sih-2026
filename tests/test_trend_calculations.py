import pytest
from app.services.analytics.analytics_service import AnalyticsService, _calculate_trend


def test_calculate_trend_normal():
    # cur=15, prev=10 -> ((15-10)/10)*100 = +50.0%
    assert _calculate_trend(15, 10) == 50.0
    # cur=5, prev=10 -> ((5-10)/10)*100 = -50.0%
    assert _calculate_trend(5, 10) == -50.0
    # cur=10, prev=10 -> 0.0%
    assert _calculate_trend(10, 10) == 0.0


def test_calculate_trend_zero_division():
    # cur=0, prev=0 -> 0.0%
    assert _calculate_trend(0, 0) == 0.0
    # cur=5, prev=0 -> +100.0%
    assert _calculate_trend(5, 0) == 100.0


def test_analytics_endpoints_trend_integrity(db_session):
    service = AnalyticsService()
    
    # Test activity risk
    activity_risk = service.get_activity_risk(db=db_session, window_days=30)
    assert isinstance(activity_risk, list)
    for item in activity_risk:
        assert isinstance(item.trend_percentage, float)

    # Test location risk
    location_risk = service.get_location_risk(db=db_session, window_days=30)
    assert isinstance(location_risk, list)
    for item in location_risk:
        assert isinstance(item.trend_percentage, float)

    # Test life saving rules risk
    lsr_risk = service.get_life_saving_rules_risk(db=db_session, window_days=30)
    assert isinstance(lsr_risk, list)
    for item in lsr_risk:
        assert isinstance(item.trend_percentage, float)

    # Test barrier recurrence
    barrier_risk = service.get_barrier_failures_recurrence(db=db_session, window_days=30)
    assert isinstance(barrier_risk, list)
    for item in barrier_risk:
        assert isinstance(item.trend_percentage, float)

    # Test department risk
    dept_risk = service.get_department_risk(db=db_session, window_days=30)
    assert isinstance(dept_risk, list)
    for item in dept_risk:
        assert isinstance(item.trend_percentage, float)
