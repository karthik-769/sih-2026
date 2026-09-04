import pytest
from sqlalchemy.exc import IntegrityError
from app.models import (
    User,
    Department,
    Location,
    SafetyReport,
    UserRole,
    IncidentType,
    ProcessingStatus,
)
from app.core.security import verify_password


def test_database_tables_exist(db_session):
    """
    Verify all required tables are present and can be queried.
    """
    assert db_session.query(User).count() >= 2
    assert db_session.query(Department).count() >= 3
    assert db_session.query(Location).count() >= 3
    assert db_session.query(SafetyReport).count() >= 5


def test_seed_users(db_session):
    """
    Verify worker and admin role-based users exist with properly hashed passwords.
    """
    worker = db_session.query(User).filter(User.role == UserRole.WORKER).first()
    assert worker is not None
    assert worker.email == "worker@safetyintelligence.internal"
    assert verify_password("Worker@2026", worker.password_hash)

    admin = db_session.query(User).filter(User.role == UserRole.ADMIN).first()
    assert admin is not None
    assert admin.email == "admin@safetyintelligence.internal"
    assert verify_password("Admin@2026", admin.password_hash)


def test_seed_departments(db_session):
    """
    Verify seeded departments match specifications: Mechanical, Electrical, Operations.
    """
    dept_names = {d.name for d in db_session.query(Department).all()}
    assert "Mechanical" in dept_names
    assert "Electrical" in dept_names
    assert "Operations" in dept_names


def test_seed_locations(db_session):
    """
    Verify seeded locations match specifications: Unit A, Unit B, Unit C with coordinates.
    """
    locations = {l.name: l for l in db_session.query(Location).all()}
    assert "Unit A" in locations
    assert "Unit B" in locations
    assert "Unit C" in locations

    assert locations["Unit A"].latitude is not None
    assert locations["Unit A"].longitude is not None


def test_model_relationships(db_session):
    """
    Verify relational integrity: SafetyReport -> Department, Location, Reporter.
    """
    report = db_session.query(SafetyReport).filter(SafetyReport.case_id == "SYN-2026-001").first()
    assert report is not None
    assert report.department is not None
    assert report.department.name == "Mechanical"
    assert report.location is not None
    assert report.location.name == "Unit A"
    assert report.reporter is not None
    assert report.reporter.role == UserRole.WORKER
    assert "[SYNTHETIC DEMO DATA]" in report.description


def test_unique_email_constraint(db_session):
    """
    Verify duplicate email raises IntegrityError.
    """
    duplicate_user = User(
        name="Duplicate User",
        email="worker@safetyintelligence.internal",
        password_hash="somehash",
        role=UserRole.WORKER,
    )
    db_session.add(duplicate_user)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_unique_department_name_constraint(db_session):
    """
    Verify duplicate department name raises IntegrityError.
    """
    duplicate_dept = Department(name="Mechanical", description="Duplicate")
    db_session.add(duplicate_dept)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_unique_case_id_constraint(db_session):
    """
    Verify duplicate case_id raises IntegrityError.
    """
    dept = db_session.query(Department).first()
    loc = db_session.query(Location).first()
    dup_report = SafetyReport(
        case_id="SYN-2026-001",
        job_role="Technician",
        department_id=dept.id,
        location_id=loc.id,
        task="Testing Task",
        incident_type=IncidentType.UNSAFE_ACT,
        description="Duplicate test",
    )
    db_session.add(dup_report)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
