from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class HazardItem(BaseModel):
    category: str = Field(..., description="Hazard category e.g. CONFINED_SPACE, ELECTRICAL, WORKING_AT_HEIGHT, CHEMICAL")
    hazard_type: str = Field(..., description="Specific hazard designation")
    description: str = Field(..., description="Details of observed hazard")
    confidence: float = Field(default=0.90, ge=0.0, le=1.0, description="Detection confidence score")
    keywords_matched: List[str] = Field(default_factory=list)


class ControlFailureItem(BaseModel):
    hierarchy_level: str = Field(..., description="Hierarchy level: ELIMINATION, SUBSTITUTION, ENGINEERING, ADMINISTRATIVE, PPE")
    failed_control: str = Field(..., description="Name of the failed or missing control safeguard")
    description: str = Field(..., description="Analysis of failure mechanism")
    severity: str = Field(default="HIGH", description="Failure criticality: LOW, MEDIUM, HIGH, CRITICAL")


class WorkerExposureData(BaseModel):
    exposure_rating: str = Field(default="MODERATE", description="Exposure rating: LOW, MODERATE, HIGH, EXTREME")
    proximity_level: str = Field(default="DIRECT", description="DIRECT, IMMEDIATE_VICINITY, PERIPHERAL")
    duration_estimate: str = Field(default="SHORT_TERM", description="TRANSIENT, SHORT_TERM, EXTENDED, CONTINUOUS")
    exposed_hazard: Optional[str] = None
    line_of_fire_detected: bool = False
    notes: Optional[str] = None


class SifPrecursorItem(BaseModel):
    precursor_type: str = Field(..., description="Precursor classification e.g. CONFINED_SPACE, HIGH_VOLTAGE, WORKING_AT_HEIGHT")
    energy_source: str = Field(..., description="Energy source involved e.g. ATMOSPHERIC, ELECTRICAL, GRAVITY, CHEMICAL")
    description: str = Field(..., description="Explanation of why this constitutes a SIF precursor")
    fatality_potential: bool = Field(default=False)


class RecommendationItem(BaseModel):
    priority: int = Field(default=1, ge=1, le=5, description="Priority rank (1 highest)")
    hierarchy_level: str = Field(default="ENGINEERING", description="Hierarchy of controls category")
    action_title: str = Field(..., description="Concise action item title")
    action_description: str = Field(..., description="Actionable safety safeguard instructions")


class ModelMetadata(BaseModel):
    pipeline_version: str = Field(default="1.0.0")
    model_name: str = Field(default="safety-intelligence-nlp-v1")
    execution_time_ms: float = Field(default=0.0)
    components_executed: List[str] = Field(default_factory=list)
    similarity_tags: List[str] = Field(default_factory=list)
    feature_vector_dim: int = Field(default=16)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class SimilarIncidentItem(BaseModel):
    report_id: int
    case_id: str
    similarity_score: float
    task: str
    description: str
    incident_type: str
    risk_level: str
    risk_score: float
    sif_precursor: bool
    department: Optional[str] = None
    location: Optional[str] = None
    reported_at: Optional[Union[datetime, str]] = None


class SimilarIncidentsResponse(BaseModel):
    source_report_id: int
    similar_reports_count: int
    high_risk_count: int
    critical_risk_count: int
    sif_count: int
    summary_text: str
    similar_reports: List[SimilarIncidentItem] = Field(default_factory=list)


class AiAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    report_id: int
    status: str = "COMPLETED"
    analysis_version: str = "1.0.0"
    model_name: str = "safety-intelligence-nlp-v1"
    
    # Intelligence attributes
    hazards: List[Dict[str, Any]] = Field(default_factory=list)
    control_failures: List[Dict[str, Any]] = Field(default_factory=list)
    failed_barriers: List[Dict[str, Any]] = Field(default_factory=list)
    worker_exposure: Dict[str, Any] = Field(default_factory=dict)
    
    # Activity & Task
    activity: Optional[str] = None
    activity_category: Optional[str] = None
    activity_confidence: float = 0.85

    # IOGP Life-Saving Rules
    life_saving_rule: Optional[str] = None
    life_saving_rule_confidence: float = 0.85
    life_saving_rule_evidence: List[str] = Field(default_factory=list)

    # Actual vs Potential Consequence
    actual_consequence: str = "No injury"
    potential_consequence: str = ""
    potential_consequence_severity: str = "NONE"
    fatality_potential: bool = False

    # SIF Precursor
    sif_precursor: bool = False
    sif_categories: List[str] = Field(default_factory=list)
    sif_level: str = "NONE"
    sif_precursors: List[Dict[str, Any]] = Field(default_factory=list)
    sif_detected: bool = False
    sif_reasoning: str = ""

    risk_score: float = 0.0
    risk_level: str = "LOW"
    explanation: str = ""
    highlighted_evidence: List[str] = Field(default_factory=list)
    evidence_snippets: List[str] = Field(default_factory=list)
    recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    similar_incidents: Dict[str, Any] = Field(default_factory=dict)
    model_metadata: Dict[str, Any] = Field(default_factory=dict)

    # HSE Review & Human-in-the-loop
    review_status: str = "PENDING"
    reviewed_by: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    original_ai_decision: Optional[Dict[str, Any]] = None
    final_hse_decision: Optional[Dict[str, Any]] = None
    review_comment: Optional[str] = None

    created_at: datetime
    updated_at: datetime


class AiAnalysisTriggerResponse(BaseModel):
    message: str
    report_id: int
    processing_status: str
    analysis: Optional[AiAnalysisResponse] = None


class HseReviewRequest(BaseModel):
    action: str = Field(..., description="Action: 'CONFIRM' or 'OVERRIDE'")
    sif_level: Optional[str] = Field(default=None, description="Updated SIF level if overriding: NONE, LOW, MEDIUM, HIGH, CRITICAL")
    life_saving_rule: Optional[str] = Field(default=None, description="Updated IOGP Life-Saving Rule if overriding")
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Updated risk score if overriding")
    comment: Optional[str] = Field(default=None, description="HSE officer review reasoning/notes")


class HseReviewResponse(BaseModel):
    success: bool
    message: str
    report_id: int
    review_status: str
    reviewed_at: datetime
    final_decision: Dict[str, Any]
