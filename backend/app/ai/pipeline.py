import time
import logging
from typing import Dict, Any, Optional

from app.ai.interfaces import (
    BasePreprocessor,
    BaseActivityExtractor,
    BaseHazardDetector,
    BaseControlFailureDetector,
    BaseExposureDetector,
    BaseConsequenceDetector,
    BaseSifDetector,
    BaseLifeSavingRuleMapper,
    BaseRiskEngine,
    BaseExplanationGenerator,
    BaseRecommendationEngine,
    BaseSimilarityEngine,
    PipelineExecutionResult,
)
from app.ai.preprocessing.service import PreprocessingService
from app.ai.activity_extraction.service import ActivityExtractionService
from app.ai.hazard_detection.service import HazardDetectionService
from app.ai.control_failure_detection.service import ControlFailureDetectionService
from app.ai.exposure_detection.service import ExposureDetectionService
from app.ai.consequence_detection.service import ConsequenceDetectionService
from app.ai.sif_detection.service import SifDetectionService
from app.ai.life_saving_rules.service import LifeSavingRuleMappingService
from app.ai.risk_engine.service import RiskEngineService
from app.ai.explanation.service import ExplanationService
from app.ai.recommendation.service import RecommendationService
from app.ai.similarity.service import SimilarityService

logger = logging.getLogger(__name__)


class AiAnalysisPipeline:
    """
    Orchestrates the end-to-end AI Safety Intelligence Processing Pipeline for OIL:
    Safety Report -> Preprocessing -> Activity Extraction -> Hazard Detection ->
    Control Failure & Barrier Classification -> Worker Exposure ->
    Worst-case Potential Consequence -> SIF Precursor Assessment ->
    IOGP Life-Saving Rules Mapping -> Risk Scoring -> Explainable Reasoning & Evidence ->
    Hierarchy-of-Controls Recommendations -> Semantic Feature Embeddings.
    """

    VERSION = "2.0.0"
    MODEL_NAME = "oil-sif-intelligence-nlp-v2"

    def __init__(
        self,
        preprocessor: Optional[BasePreprocessor] = None,
        activity_extractor: Optional[BaseActivityExtractor] = None,
        hazard_detector: Optional[BaseHazardDetector] = None,
        control_failure_detector: Optional[BaseControlFailureDetector] = None,
        exposure_detector: Optional[BaseExposureDetector] = None,
        consequence_detector: Optional[BaseConsequenceDetector] = None,
        sif_detector: Optional[BaseSifDetector] = None,
        life_saving_rule_mapper: Optional[BaseLifeSavingRuleMapper] = None,
        risk_engine: Optional[BaseRiskEngine] = None,
        explanation_generator: Optional[BaseExplanationGenerator] = None,
        recommendation_engine: Optional[BaseRecommendationEngine] = None,
        similarity_engine: Optional[BaseSimilarityEngine] = None,
    ):
        self.preprocessor = preprocessor or PreprocessingService()
        self.activity_extractor = activity_extractor or ActivityExtractionService()
        self.hazard_detector = hazard_detector or HazardDetectionService()
        self.control_failure_detector = control_failure_detector or ControlFailureDetectionService()
        self.exposure_detector = exposure_detector or ExposureDetectionService()
        self.consequence_detector = consequence_detector or ConsequenceDetectionService()
        self.sif_detector = sif_detector or SifDetectionService()
        self.life_saving_rule_mapper = life_saving_rule_mapper or LifeSavingRuleMappingService()
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
        context = context or {}

        # 1. Preprocessing & Linguistic Analysis
        preprocessed = self.preprocessor.preprocess(text, context=context)
        components_executed.append("preprocessing")

        # 2. Activity / Task Extraction
        activity_result = self.activity_extractor.extract_activity(preprocessed, context=context)
        components_executed.append("activity_extraction")

        # 3. Domain & Ontology Hazard Detection
        hazard_result = self.hazard_detector.detect_hazards(preprocessed, context=context)
        components_executed.append("hazard_detection")

        # 4. Control Failure & Barrier Classification
        control_result = self.control_failure_detector.detect_failures(
            preprocessed, hazards=hazard_result.hazards, context=context
        )
        components_executed.append("control_failure_detection")

        # 5. Worker Exposure & Proximity Detection
        exposure_result = self.exposure_detector.detect_exposure(
            preprocessed, hazards=hazard_result.hazards, context=context
        )
        components_executed.append("exposure_detection")

        # 6. Actual vs Worst-Case Potential Consequence Detection
        consequence_result = self.consequence_detector.detect_consequence(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            context=context,
        )
        components_executed.append("consequence_detection")

        # 7. SIF (Serious Injury and Fatality) Precursor Detection
        sif_result = self.sif_detector.detect_sif(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            consequence=consequence_result,
            context=context,
        )
        components_executed.append("sif_detection")

        # 8. IOGP Life-Saving Rules Mapping
        lsr_result = self.life_saving_rule_mapper.map_life_saving_rule(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            activity=activity_result,
            sif_result=sif_result,
            context=context,
        )
        components_executed.append("life_saving_rule_mapping")

        # 9. Quantitative Explainable Risk Engine
        risk_result = self.risk_engine.calculate_risk(
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            exposure=exposure_result.worker_exposure,
            sif_result=sif_result,
            consequence=consequence_result,
            context=context,
        )
        components_executed.append("risk_engine")

        # 10. Natural Language Explanation & Highlighted Evidence Extraction
        explanation_result = self.explanation_generator.generate_explanation(
            preprocessed=preprocessed,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            sif_result=sif_result,
            risk_result=risk_result,
            life_saving_rule=lsr_result,
            consequence=consequence_result,
            activity=activity_result,
        )
        components_executed.append("explanation")

        # 11. Actionable Hierarchy-of-Controls Recommendations
        recommendation_result = self.recommendation_engine.generate_recommendations(
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            sif_result=sif_result,
            risk_result=risk_result,
            life_saving_rule=lsr_result,
        )
        components_executed.append("recommendation")

        # 12. Semantic Feature Vector & Dense Embedding Extraction
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
            "activity_confidence": activity_result.confidence,
            "life_saving_rule_confidence": lsr_result.confidence,
            "potential_consequence_severity": consequence_result.severity,
        }

        # Combine highlighted evidence snippets
        combined_evidence = list(set(explanation_result.highlighted_evidence + sif_result.evidence_snippets + lsr_result.evidence))

        return PipelineExecutionResult(
            analysis_version=self.VERSION,
            model_name=self.MODEL_NAME,
            hazards=hazard_result.hazards,
            control_failures=control_result.control_failures,
            failed_barriers=control_result.failed_barriers,
            worker_exposure=exposure_result.worker_exposure,
            activity=activity_result.activity,
            activity_category=activity_result.activity_category,
            activity_confidence=activity_result.confidence,
            actual_consequence=consequence_result.actual_consequence,
            potential_consequence=consequence_result.potential_consequence,
            potential_consequence_severity=consequence_result.severity,
            fatality_potential=sif_result.fatality_potential,
            sif_precursor=sif_result.sif_precursor,
            sif_categories=sif_result.sif_categories,
            sif_level=sif_result.sif_level,
            sif_precursors=sif_result.sif_precursors,
            sif_detected=sif_result.sif_detected,
            sif_reasoning=sif_result.sif_reasoning,
            life_saving_rule=lsr_result.life_saving_rule,
            life_saving_rule_confidence=lsr_result.confidence,
            life_saving_rule_evidence=lsr_result.evidence,
            risk_score=risk_result.risk_score,
            risk_level=risk_result.risk_level,
            explanation=explanation_result.explanation,
            highlighted_evidence=explanation_result.highlighted_evidence,
            evidence_snippets=combined_evidence,
            recommendations=recommendation_result.recommendations,
            feature_vector=similarity_result.feature_vector,
            model_metadata=model_metadata,
        )
