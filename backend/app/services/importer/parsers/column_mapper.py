import re
from typing import Dict, Any, Optional, List, Tuple


class ColumnMapper:
    """
    Intelligent, case-insensitive, fuzzy column name resolver for Excel & CSV safety reports.
    Maps arbitrary user header variations to standardized system fields:
    - case_id
    - job_role
    - department
    - location
    - task
    - incident_type
    - date_time
    - description
    """

    COLUMN_ALIASES: Dict[str, List[str]] = {
        "case_id": [
            "case id", "case_id", "caseid", "report id", "report_id", "reportid",
            "incident id", "incident_id", "incidentid", "id", "reference", "ref no",
            "case no", "caseno", "ticket id", "tracking id"
        ],
        "job_role": [
            "job role", "job_role", "jobrole", "role", "designation", "worker role",
            "reporter role", "trade", "occupation", "position", "reported by role", "job title"
        ],
        "department": [
            "department", "dept", "department name", "dept name", "discipline",
            "division", "section", "business unit", "functional area"
        ],
        "location": [
            "location", "plant location", "unit", "site", "area", "zone",
            "plant unit", "workplace", "facility", "building", "floor"
        ],
        "task": [
            "task", "task description", "activity", "work task", "job task",
            "operation", "maintenance activity", "work being performed", "job description"
        ],
        "incident_type": [
            "incident type", "incident_type", "type", "category", "incident category",
            "observation type", "classification", "event type", "hazard type"
        ],
        "date_time": [
            "date/time", "date time", "datetime", "date", "reported at", "reported_at",
            "reported date", "incident date", "event date", "time", "timestamp", "log date"
        ],
        "description": [
            "description", "incident description", "event description", "details",
            "narrative", "observation", "what happened", "findings", "verbatim description",
            "hazard details", "incident details", "summary", "notes", "remarks"
        ],
    }

    INCIDENT_TYPE_MAP: Dict[str, str] = {
        "near miss": "NEAR_MISS",
        "near_miss": "NEAR_MISS",
        "nearmiss": "NEAR_MISS",
        "unsafe act": "UNSAFE_ACT",
        "unsafe_act": "UNSAFE_ACT",
        "unsafe condition": "UNSAFE_CONDITION",
        "unsafe_condition": "UNSAFE_CONDITION",
        "safety observation": "SAFETY_OBSERVATION",
        "safety_observation": "SAFETY_OBSERVATION",
        "safe observation": "SAFETY_OBSERVATION",
        "safe practice": "SAFETY_OBSERVATION",
        "positive observation": "SAFETY_OBSERVATION",
        "observation": "SAFETY_OBSERVATION",
    }

    @classmethod
    def clean_header(cls, header: str) -> str:
        """Normalizes header string by lowercasing, stripping punctuation, and compressing spaces."""
        if not header:
            return ""
        cleaned = re.sub(r'[^a-zA-Z0-9\s_/-]', '', str(header).strip().lower())
        cleaned = re.sub(r'[\s_-]+', ' ', cleaned).strip()
        return cleaned

    @classmethod
    def map_columns(cls, raw_headers: List[str]) -> Dict[int, str]:
        """
        Maps column index -> canonical field name based on matching aliases.
        """
        mapping: Dict[int, str] = {}
        assigned_fields = set()

        for idx, header in enumerate(raw_headers):
            if not header:
                continue
            cleaned = cls.clean_header(header)
            
            # Exact alias check
            matched_field = None
            for field, aliases in cls.COLUMN_ALIASES.items():
                if field in assigned_fields:
                    continue
                if cleaned in aliases or any(alias == cleaned for alias in aliases):
                    matched_field = field
                    break

            # Partial substring check fallback
            if not matched_field:
                for field, aliases in cls.COLUMN_ALIASES.items():
                    if field in assigned_fields:
                        continue
                    if any(alias in cleaned or cleaned in alias for alias in aliases if len(alias) >= 4):
                        matched_field = field
                        break

            if matched_field:
                mapping[idx] = matched_field
                assigned_fields.add(matched_field)

        return mapping

    @classmethod
    def normalize_incident_type(cls, raw_type: Optional[str]) -> str:
        """Normalizes user provided incident type string into canonical Enum value."""
        if not raw_type or not str(raw_type).strip():
            return "UNSAFE_ACT"
        clean = re.sub(r'[^a-zA-Z0-9\s_]', '', str(raw_type).strip().lower())
        clean = re.sub(r'[\s_-]+', ' ', clean).strip()

        for key, val in cls.INCIDENT_TYPE_MAP.items():
            if key in clean or clean in key:
                return val

        # Direct enum uppercase check
        upper = str(raw_type).strip().upper().replace(" ", "_")
        if upper in ["UNSAFE_ACT", "UNSAFE_CONDITION", "NEAR_MISS", "SAFETY_OBSERVATION"]:
            return upper

        return "UNSAFE_ACT"
