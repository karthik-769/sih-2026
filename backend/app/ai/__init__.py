"""
AI Processing Infrastructure Package
Exposes pipeline interfaces, orchestration pipeline, and modular processing services.
"""

from app.ai.interfaces import (
    PreprocessedText,
    HazardDetectionResult,
    ControlFailureResult,
    ExposureDetectionResult,
    SifDetectionResult,
    RiskEngineResult,
    ExplanationResult,
    RecommendationResult,
    SimilarityResult,
    PipelineExecutionResult,
    BasePreprocessor,
    BaseHazardDetector,
    BaseControlFailureDetector,
    BaseExposureDetector,
    BaseSifDetector,
    BaseRiskEngine,
    BaseExplanationGenerator,
    BaseRecommendationEngine,
    BaseSimilarityEngine,
)
from app.ai.pipeline import AiAnalysisPipeline

__all__ = [
    "AiAnalysisPipeline",
    "PreprocessedText",
    "HazardDetectionResult",
    "ControlFailureResult",
    "ExposureDetectionResult",
    "SifDetectionResult",
    "RiskEngineResult",
    "ExplanationResult",
    "RecommendationResult",
    "SimilarityResult",
    "PipelineExecutionResult",
    "BasePreprocessor",
    "BaseHazardDetector",
    "BaseControlFailureDetector",
    "BaseExposureDetector",
    "BaseSifDetector",
    "BaseRiskEngine",
    "BaseExplanationGenerator",
    "BaseRecommendationEngine",
    "BaseSimilarityEngine",
]
