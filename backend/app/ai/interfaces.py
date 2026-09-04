from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class PreprocessedText:
    raw_text: str
    cleaned_text: str
    tokens: List[str] = field(default_factory=list)
    phrases: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HazardDetectionResult:
    hazards: List[Dict[str, Any]] = field(default_factory=list)
    is_prototype: bool = False


@dataclass
class ControlFailureResult:
    control_failures: List[Dict[str, Any]] = field(default_factory=list)
    is_prototype: bool = False


@dataclass
class ExposureDetectionResult:
    worker_exposure: Dict[str, Any] = field(default_factory=dict)
    is_prototype: bool = False


@dataclass
class SifDetectionResult:
    sif_precursor: bool = False
    sif_categories: List[str] = field(default_factory=list)
    sif_level: str = "NONE"  # NONE, LOW, MEDIUM, HIGH, CRITICAL
    sif_precursors: List[Dict[str, Any]] = field(default_factory=list)
    confidence: float = 0.85
    fatality_potential: bool = False
    sif_detected: bool = False
    is_prototype: bool = False


@dataclass
class RiskEngineResult:
    risk_score: float = 0.0  # 0 to 100
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH, CRITICAL
    scoring_breakdown: Dict[str, Any] = field(default_factory=dict)
    is_prototype: bool = False


@dataclass
class ExplanationResult:
    explanation: str = ""
    highlighted_evidence: List[str] = field(default_factory=list)
    is_prototype: bool = False


@dataclass
class RecommendationResult:
    recommendations: List[Dict[str, Any]] = field(default_factory=list)
    is_prototype: bool = False


@dataclass
class SimilarityResult:
    feature_vector: List[float] = field(default_factory=list)
    similarity_tags: List[str] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)
    is_prototype: bool = False


@dataclass
class PipelineExecutionResult:
    analysis_version: str
    model_name: str
    hazards: List[Dict[str, Any]]
    control_failures: List[Dict[str, Any]]
    worker_exposure: Dict[str, Any]
    sif_precursor: bool
    sif_categories: List[str]
    sif_level: str
    sif_precursors: List[Dict[str, Any]]
    sif_detected: bool
    risk_score: float
    risk_level: str
    explanation: str
    highlighted_evidence: List[str]
    recommendations: List[Dict[str, Any]]
    feature_vector: List[float]
    model_metadata: Dict[str, Any]


class BasePreprocessor(ABC):
    @abstractmethod
    def preprocess(self, text: str, context: Optional[Dict[str, Any]] = None) -> PreprocessedText:
        pass


class BaseHazardDetector(ABC):
    @abstractmethod
    def detect_hazards(self, preprocessed: PreprocessedText, context: Optional[Dict[str, Any]] = None) -> HazardDetectionResult:
        pass


class BaseControlFailureDetector(ABC):
    @abstractmethod
    def detect_failures(self, preprocessed: PreprocessedText, hazards: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> ControlFailureResult:
        pass


class BaseExposureDetector(ABC):
    @abstractmethod
    def detect_exposure(self, preprocessed: PreprocessedText, hazards: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> ExposureDetectionResult:
        pass


class BaseSifDetector(ABC):
    @abstractmethod
    def detect_sif(self, preprocessed: PreprocessedText, hazards: List[Dict[str, Any]], control_failures: List[Dict[str, Any]], exposure: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> SifDetectionResult:
        pass


class BaseRiskEngine(ABC):
    @abstractmethod
    def calculate_risk(self, hazards: List[Dict[str, Any]], control_failures: List[Dict[str, Any]], exposure: Dict[str, Any], sif_result: SifDetectionResult, context: Optional[Dict[str, Any]] = None) -> RiskEngineResult:
        pass


class BaseExplanationGenerator(ABC):
    @abstractmethod
    def generate_explanation(self, preprocessed: PreprocessedText, hazards: List[Dict[str, Any]], control_failures: List[Dict[str, Any]], sif_result: SifDetectionResult, risk_result: RiskEngineResult) -> ExplanationResult:
        pass


class BaseRecommendationEngine(ABC):
    @abstractmethod
    def generate_recommendations(self, hazards: List[Dict[str, Any]], control_failures: List[Dict[str, Any]], sif_result: SifDetectionResult, risk_result: RiskEngineResult) -> RecommendationResult:
        pass


class BaseSimilarityEngine(ABC):
    @abstractmethod
    def extract_features(self, preprocessed: PreprocessedText, hazards: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> SimilarityResult:
        pass
