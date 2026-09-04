import time
import logging
from typing import Dict, Any, Optional

from app.ai.interfaces import (
    BasePreprocessor,
    BaseHazardDetector,
    BaseControlFailureDetector,
    BaseExposureDetector,
    BaseSifDetector,
    BaseRiskEngine,
    BaseExplanationGenerator,
    BaseRecommendationEngine,
    BaseSimilarityEngine,
    PipelineExecutionResult,
)
from app.ai.preprocessing.service import PreprocessingService
from app.ai.hazard_detection.service import HazardDetectionService
from app.ai.control_failure_detection.service import ControlFailureDetectionService
from app.ai.exposure_detection.service import ExposureDetectionService
from app.ai.sif_detection.service import SifDetectionService
from app.ai.risk_engine.service import RiskEngineService
from app.ai.explanation.service import ExplanationService
from app.ai.recommendation.service import RecommendationService
from app.ai.similarity.service import SimilarityService

logger = logging.getLogger(__name__)


class AiAnalysisPipeline:
    """
    Orchestrates the end-to-end AI Safety Intelligence Processing Pipeline:
    Safety Report -> Preprocessing -> Hazard Detection -> Control Failure ->
    Worker Exposure -> SIF Precursor Detection -> Risk Scoring ->
    Explanation & Evidence -> Preventive Recommendations -> Semantic Embedding
    """

    VERSION = "1.0.0"
    MODEL_NAME = "safety-intelligence-nlp-v1"

    def __init__(
        self,
        preprocessor: Optional[BasePreprocessor] = None,
        hazard_detector: Optional[BaseHazardDetector] = None,
        control_failure_detector: Optional[BaseControlFailureDetector] = None,
        exposure_detector: Optional[BaseExposureDetector] = None,
        sif_detector: Optional[BaseSifDetector] = None,
        risk_engine: Optional[BaseRiskEngine] = None,
        explanation_generator: Optional[BaseExplanationGenerator] = None,
        recommendation_engine: Optional[BaseRecommendationEngine] = None,
        similarity_engine: Optional[BaseSimilarityEngine] = None,
    ):
        self.preprocessor = preprocessor or PreprocessingService()
        self.hazard_detector = hazard_detector or HazardDetectionService()
        self.control_failure_detector = control_failure_detector or ControlFailureDetectionService()
        self.exposure_detector = exposure_detector or ExposureDetectionService()
        self.sif_detector = sif_detector or SifDetectionService()
        self.risk_engine = risk_engine or RiskEngineService()
        self.explanation_generator = explanation_generator or ExplanationService()
        self.recommendation_engine = recommendation_engine or RecommendationService()
        self.similarity_engine = similarity_engine or SimilarityService()

    def process(self, text: str, context: Optional[Dict[str, Any]] = None) -> PipelineExecutionResult:
        """
        Executes pipeline synchronously across all modular safety intelligence engines.
        """
        start_time = time.perf_counter()
        components_executed = []

        # 1. Preprocessing & Linguistic Analysis
        preprocessed = self.preprocessor.preprocess(text, context=context)
        components_executed.append("preprocessing")

        # 2. Domain & Ontology Hazard Detection
        hazard_result = self.hazard_detector.detect_hazards(preprocessed, context=context)
        components_executed.append("hazard_detection")

        # 3. Control Failure & Safeguard Integrity Detection
        control_result = self.control_failure_detector.detect_failures(
            preprocessed, hazards=hazard_result.hazards, context=context
        )
        components_executed.append("control_failure_detection")

        # 4. Worker Exposure & Proximity Detection
        exposure_result = self.exposure_detector.detect_exposure(
            preprocessed, hazards=hazard_result.hazards, context=context
        )
        components_executed.append("exposure_detection")

        # 5. SIF (Serious Injury and Fatality) Precursor Detection
        sif_result = self.sif_detector.detect_sif(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            context=context,
        )
        components_executed.append("sif_detection")

        # 6. Quantitative Explainable Risk Engine
        risk_result = self.risk_engine.calculate_risk(
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            sif_result=sif_result,
            context=context,
        )
        components_executed.append("risk_engine")

        # 7. Natural Language Explanation & Highlighted Evidence Extraction
        explanation_result = self.explanation_generator.generate_explanation(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            sif_result=sif_result,
            risk_result=risk_result,
        )
        components_executed.append("explanation")

        # 8. Actionable Hierarchy-of-Controls Recommendations
        recommendation_result = self.recommendation_engine.generate_recommendations(
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            sif_result=sif_result,
            risk_result=risk_result,
        )
        components_executed.append("recommendation")

        # 9. Semantic Feature Vector & Dense Embedding Extraction
        similarity_result = self.similarity_engine.extract_features(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            context=context,
        )
        components_executed.append("similarity")

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        model_metadata = {
            "pipeline_version": self.VERSION,
            "model_name": self.MODEL_NAME,
            "execution_time_ms": elapsed_ms,
            "components_executed": components_executed,
            "similarity_tags": similarity_result.similarity_tags,
            "feature_vector_dim": len(similarity_result.feature_vector),
            "scoring_breakdown": risk_result.scoring_breakdown,
            "sif_confidence": sif_result.confidence,
            "fatality_potential": sif_result.fatality_potential,
        }

        return PipelineExecutionResult(
            analysis_version=self.VERSION,
            model_name=self.MODEL_NAME,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            worker_exposure=exposure_result.worker_exposure,
            sif_precursor=sif_result.sif_precursor,
            sif_categories=sif_result.sif_categories,
            sif_level=sif_result.sif_level,
            sif_precursors=sif_result.sif_precursors,
            sif_detected=sif_result.sif_detected,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            explanation=explanation_result.explanation,
            highlighted_evidence=explanation_result.highlighted_evidence,
            recommendations=recommendation_result.recommendations,
            feature_vector=similarity_result.feature_vector,
            model_metadata=model_metadata,
        )
