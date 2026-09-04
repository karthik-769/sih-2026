import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.models import (
    User,
    Department,
    Location,
    SafetyReport,
    UserRole,
    IncidentType,
    ProcessingStatus,
)
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


def seed_database(db: Session) -> dict:
    """
    Seeds the database with foundational development data.
    Clearly labeled as synthetic/demo data.
    """
    logger.info("Starting database seeding with synthetic demonstration data...")

    # 1. Seed Departments
    departments_data = [
        {
            "name": "Mechanical",
            "description": "Mechanical maintenance, rotating equipment, conveyors, and fabrication units.",
        },
        {
            "name": "Electrical",
            "description": "High voltage substations, motor control centers, transformers, and instrumentation.",
        },
        {
            "name": "Operations",
            "description": "Control room operations, process units, boiler plants, and material handling.",
        },
    ]

    dept_map = {}
    for d_data in departments_data:
        dept = db.query(Department).filter(Department.name == d_data["name"]).first()
        if not dept:
            dept = Department(**d_data)
            db.add(dept)
            db.flush()
        dept_map[dept.name] = dept

    # 2. Seed Locations
    locations_data = [
        {
            "name": "Unit A",
            "description": "Primary Processing & Crushing Plant (Heavy Machinery Zone)",
            "latitude": 28.6139,
            "longitude": 77.2090,
        },
        {
            "name": "Unit B",
            "description": "Substation 3 & Main Power Distribution Complex",
            "latitude": 28.6145,
            "longitude": 77.2105,
        },
        {
            "name": "Unit C",
            "description": "Bulk Chemical Storage & Tank Loading Terminal",
            "latitude": 28.6152,
            "longitude": 77.2120,
        },
    ]

    loc_map = {}
    for l_data in locations_data:
        loc = db.query(Location).filter(Location.name == l_data["name"]).first()
        if not loc:
            loc = Location(**l_data)
            db.add(loc)
            db.flush()
        loc_map[loc.name] = loc

    # 3. Seed Users
    users_data = [
        {
            "name": "John Worker",
            "email": "worker@safetyintelligence.internal",
            "password_hash": get_password_hash("Worker@2026"),
            "role": UserRole.WORKER,
            "is_active": True,
        },
        {
            "name": "David Admin",
            "email": "admin@safetyintelligence.internal",
            "password_hash": get_password_hash("Admin@2026"),
            "role": UserRole.ADMIN,
            "is_active": True,
        },
    ]

    user_map = {}
    for u_data in users_data:
        user = db.query(User).filter(User.email == u_data["email"]).first()
        if not user:
            user = User(**u_data)
            db.add(user)
            db.flush()
        user_map[user.role] = user

    # 4. Seed Realistic Synthetic Safety Reports (clearly labeled)
    now = datetime.now(timezone.utc)

    synthetic_reports = [
        {
            "case_id": "SYN-2026-001",
            "job_role": "Fitter / Millwright",
            "department_id": dept_map["Mechanical"].id,
            "location_id": loc_map["Unit A"].id,
            "task": "Conveyor Belt Idler Roller Replacement",
            "incident_type": IncidentType.NEAR_MISS,
            "description": "[SYNTHETIC DEMO DATA] While replacing idler roller on Conveyor #4, an overhead 10kg metal bracket broke loose and fell 4 meters, landing 30 cm from the technician. LOTO was active but overhead drop-zone barrier was not installed.",
            "reported_at": now - timedelta(days=5, hours=3),
            "created_by": user_map[UserRole.WORKER].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-002",
            "job_role": "High Voltage Electrician",
            "department_id": dept_map["Electrical"].id,
            "location_id": loc_map["Unit B"].id,
            "task": "Transformer Bay Busbar Inspection",
            "incident_type": IncidentType.UNSAFE_CONDITION,
            "description": "[SYNTHETIC DEMO DATA] Discovered missing safety interlock panel cover on 6.6kV Switchgear Cabinet 2B. Exposed energized copper terminal busbars without warning barrier.",
            "reported_at": now - timedelta(days=4, hours=6),
            "created_by": user_map[UserRole.ADMIN].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-003",
            "job_role": "Plant Process Operator",
            "department_id": dept_map["Operations"].id,
            "location_id": loc_map["Unit C"].id,
            "task": "Caustic Soda Tank Offloading",
            "incident_type": IncidentType.UNSAFE_ACT,
            "description": "[SYNTHETIC DEMO DATA] Contractor driver observed offloading liquid caustic soda without wearing chemical splash face shield and PVC apron. Driver was only wearing standard safety glasses.",
            "reported_at": now - timedelta(days=3, hours=1),
            "created_by": user_map[UserRole.WORKER].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-004",
            "job_role": "Scaffolding Inspector",
            "department_id": dept_map["Mechanical"].id,
            "location_id": loc_map["Unit A"].id,
            "task": "Erection of Working Platform at 12m Height",
            "incident_type": IncidentType.UNSAFE_CONDITION,
            "description": "[SYNTHETIC DEMO DATA] Third-party scaffold found with missing middle guardrails and unfastened toe-boards on platform level 3 (approx 9m elevation). Green safe-to-use tag was immediately removed.",
            "reported_at": now - timedelta(days=2, hours=8),
            "created_by": user_map[UserRole.ADMIN].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-005",
            "job_role": "Control Room Engineer",
            "department_id": dept_map["Operations"].id,
            "location_id": loc_map["Unit C"].id,
            "task": "Pressure Relief Valve Routine Shift Check",
            "incident_type": IncidentType.SAFETY_OBSERVATION,
            "description": "[SYNTHETIC DEMO DATA] Good catch: Shift technician identified weeping flange on nitrogen purge header before startup and initiated preventative seal torque procedure.",
            "reported_at": now - timedelta(days=1, hours=4),
            "created_by": user_map[UserRole.WORKER].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-006",
            "job_role": "Electrical Technician",
            "department_id": dept_map["Electrical"].id,
            "location_id": loc_map["Unit B"].id,
            "task": "UPS Battery Bank Impedance Testing",
            "incident_type": IncidentType.UNSAFE_ACT,
            "description": "[SYNTHETIC DEMO DATA] Technician attempted battery cell voltage check without insulated tool kit and without removing metal wristwatch.",
            "reported_at": now - timedelta(hours=14),
            "created_by": user_map[UserRole.ADMIN].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
        {
            "case_id": "SYN-2026-007",
            "job_role": "Rigging Specialist",
            "department_id": dept_map["Mechanical"].id,
            "location_id": loc_map["Unit A"].id,
            "task": "Overhead Crane 20-Ton Gearbox Lift",
            "incident_type": IncidentType.NEAR_MISS,
            "description": "[SYNTHETIC DEMO DATA] Wire rope sling slipped 10 cm along lifting lug during initial test tensioning due to missing shackle safety pin. Load lowered immediately and sling replaced.",
            "reported_at": now - timedelta(hours=5),
            "created_by": user_map[UserRole.WORKER].id,
            "processing_status": ProcessingStatus.SUBMITTED,
        },
    ]

    created_reports = 0
    for r_data in synthetic_reports:
        rep = db.query(SafetyReport).filter(SafetyReport.case_id == r_data["case_id"]).first()
        if not rep:
            rep = SafetyReport(**r_data)
            db.add(rep)
            created_reports += 1

    db.commit()

    logger.info(f"Seeding completed successfully: {len(dept_map)} depts, {len(loc_map)} locs, {len(user_map)} users, {created_reports} reports seeded.")

    return {
        "departments_count": len(dept_map),
        "locations_count": len(loc_map),
        "users_count": len(user_map),
        "reports_seeded": created_reports,
    }
