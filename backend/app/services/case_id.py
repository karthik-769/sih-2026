import random
import string
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models.safety_report import SafetyReport


def generate_unique_case_id(db: Session, prefix: str = "CASE") -> str:
    """
    Generates a unique, non-colliding Case ID.
    Format: CASE-YYYY-XXXX (e.g., CASE-2026-0142)
    """
    year = datetime.now(timezone.utc).year
    max_attempts = 100

    for _ in range(max_attempts):
        # Generate 4-character random alphanumeric or number suffix
        num = random.randint(1001, 9999)
        case_id = f"{prefix}-{year}-{num}"
        
        # Check if already exists in DB
        exists = db.query(SafetyReport).filter(SafetyReport.case_id == case_id).first()
        if not exists:
            return case_id

    # Fallback to high-entropy hex suffix if loop exhausts
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{year}-{random_str}"
