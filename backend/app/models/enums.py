import enum


class UserRole(str, enum.Enum):
    WORKER = "WORKER"
    ADMIN = "ADMIN"


class IncidentType(str, enum.Enum):
    UNSAFE_ACT = "UNSAFE_ACT"
    UNSAFE_CONDITION = "UNSAFE_CONDITION"
    NEAR_MISS = "NEAR_MISS"
    SAFETY_OBSERVATION = "SAFETY_OBSERVATION"


class ProcessingStatus(str, enum.Enum):
    SUBMITTED = "SUBMITTED"
    ANALYZING = "ANALYZING"
    ANALYZED = "ANALYZED"
    FAILED = "FAILED"
