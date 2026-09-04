import math
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.enums import ProcessingStatus
from app.ai.pipeline import AiAnalysisPipeline
from app.ai.interfaces import PipelineExecutionResult

logger = logging.getLogger(__name__)


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Computes cosine similarity between two float vectors.
    """
    if not vec1 or not vec2:
        return 0.0
    min_len = min(len(vec1), len(vec2))
    dot = sum(vec1[i] * vec2[i] for i in range(min_len))
    norm1 = math.sqrt(sum(x * x for x in vec1[:min_len]))
    norm2 = math.sqrt(sum(y * y for y in vec2[:min_len]))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    sim = dot / (norm1 * norm2)
    return round(float(sim), 4)


class AnalysisProcessingError(Exception):
    """Raised when an unrecoverable failure happens during AI analysis."""
    pass


class AnalysisService:
    """
    Coordinates the execution of AI Processing Pipeline against safety reports,
    handles lifecycle state transitions (SUBMITTED/PENDING -> ANALYZING/PROCESSING -> ANALYZED/COMPLETED / FAILED),
    manages persistence in the ai_analyses table while keeping the original safety report intact,
    and runs semantic similarity search across historical incidents.
    """

    def __init__(self, pipeline: Optional[AiAnalysisPipeline] = None):
        self.pipeline = pipeline or AiAnalysisPipeline()

    def process_report_analysis(
        self,
        report_id: int,
        db: Session,
        raise_on_failure: bool = False,
    ) -> AiAnalysis:
        """
        Executes the AI analysis pipeline for a safety report.
        """
        report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
        if not report:
            raise ValueError(f"Safety report with ID {report_id} does not exist.")

        # 1. Update Processing Status to ANALYZING / PROCESSING
        report.processing_status = ProcessingStatus.ANALYZING
        db.add(report)
        db.commit()
        db.refresh(report)
        logger.info(f"Report {report.case_id} (ID: {report.id}) status set to ANALYZING")

        try:
            # Prepare contextual data for the pipeline
            context = {
                "report_id": report.id,
                "case_id": report.case_id,
                "job_role": report.job_role,
                "task": report.task,
                "incident_type": report.incident_type.value if hasattr(report.incident_type, "value") else str(report.incident_type),
                "department_id": report.department_id,
                "location_id": report.location_id,
            }

            # Combine task and description for rich NLP processing
            full_text = f"{report.task}. {report.description}"

            # 2. Execute AI analysis pipeline
            result: PipelineExecutionResult = self.pipeline.process(
                text=full_text,
                context=context,
            )

            # 3. Compute Semantic Similarity with historical reports
            similar_summary = self._compute_historical_similarity(
                current_report_id=report.id,
                current_vector=result.feature_vector,
                db=db,
            )

            # 4. Create or update AiAnalysis record
            analysis = db.query(AiAnalysis).filter(AiAnalysis.report_id == report.id).first()
            if not analysis:
                analysis = AiAnalysis(
                    report_id=report.id,
                    status="COMPLETED",
                    analysis_version=result.analysis_version,
                    model_name=result.model_name,
                    hazards=result.hazards,
                    control_failures=result.control_failures,
                    worker_exposure=result.worker_exposure,
                    sif_precursor=result.sif_precursor,
                    sif_categories=result.sif_categories,
                    sif_level=result.sif_level,
                    sif_precursors=result.sif_precursors,
                    sif_detected=result.sif_detected,
                    risk_score=result.risk_score,
                    risk_level=result.risk_level,
                    explanation=result.explanation,
                    highlighted_evidence=result.highlighted_evidence,
                    recommendations=result.recommendations,
                    similar_incidents=similar_summary,
                    embedding=result.feature_vector,
                    model_metadata=result.model_metadata,
                )
                db.add(analysis)
            else:
                analysis.status = "COMPLETED"
                analysis.analysis_version = result.analysis_version
                analysis.model_name = result.model_name
                analysis.hazards = result.hazards
                analysis.control_failures = result.control_failures
                analysis.worker_exposure = result.worker_exposure
                analysis.sif_precursor = result.sif_precursor
                analysis.sif_categories = result.sif_categories
                analysis.sif_level = result.sif_level
                analysis.sif_precursors = result.sif_precursors
                analysis.sif_detected = result.sif_detected
                analysis.risk_score = result.risk_score
                analysis.risk_level = result.risk_level
                analysis.explanation = result.explanation
                analysis.highlighted_evidence = result.highlighted_evidence
                analysis.recommendations = result.recommendations
                analysis.similar_incidents = similar_summary
                analysis.embedding = result.feature_vector
                analysis.model_metadata = result.model_metadata
                db.add(analysis)

            # 5. Transition report status to ANALYZED
            report.processing_status = ProcessingStatus.ANALYZED
            db.add(report)
            db.commit()
            db.refresh(analysis)
            db.refresh(report)

            logger.info(
                f"Report {report.case_id} (ID: {report.id}) successfully analyzed. "
                f"Risk: {result.risk_level} ({result.risk_score}), SIF Precursor: {result.sif_precursor}"
            )

            # 6. Trigger Pattern & Early Warning Engine evaluation
            try:
                from app.services.patterns.early_warning_engine import early_warning_engine
                early_warning_engine.evaluate_patterns_and_generate_alerts(db)
            except Exception as pe_err:
                logger.warning(f"Pattern & Early Warning evaluation note for Report {report.id}: {pe_err}")

            return analysis

        except Exception as exc:
            db.rollback()
            logger.error(f"Analysis pipeline execution failed for Report {report.id}: {exc}", exc_info=True)

            # Attempt recording FAILED state cleanly
            try:
                report.processing_status = ProcessingStatus.FAILED
                db.add(report)

                analysis = db.query(AiAnalysis).filter(AiAnalysis.report_id == report.id).first()
                if not analysis:
                    analysis = AiAnalysis(
                        report_id=report.id,
                        status="FAILED",
                        analysis_version=self.pipeline.VERSION,
                        model_name=self.pipeline.MODEL_NAME,
                        hazards=[],
                        control_failures=[],
                        worker_exposure={},
                        sif_precursor=False,
                        sif_categories=[],
                        sif_level="NONE",
                        sif_precursors=[],
                        sif_detected=False,
                        risk_score=0.0,
                        risk_level="LOW",
                        explanation=f"AI analysis failed during processing: {str(exc)}",
                        highlighted_evidence=[],
                        recommendations=[],
                        similar_incidents={},
                        embedding=[],
                        model_metadata={"error": str(exc)},
                    )
                    db.add(analysis)
                else:
                    analysis.status = "FAILED"
                    analysis.explanation = f"AI analysis failed during processing: {str(exc)}"
                    analysis.model_metadata = {"error": str(exc)}
                    db.add(analysis)

                db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to persist failure status for report {report.id}: {commit_err}")
                db.rollback()

            if raise_on_failure:
                raise AnalysisProcessingError(f"AI analysis failed for report {report_id}: {str(exc)}") from exc

            return analysis

    def _compute_historical_similarity(
        self,
        current_report_id: int,
        current_vector: List[float],
        db: Session,
    ) -> Dict[str, Any]:
        """
        Calculates cosine similarity with all previously analyzed reports and aggregates high-risk/SIF counts.
        """
        all_analyses = (
            db.query(AiAnalysis)
            .filter(AiAnalysis.report_id != current_report_id)
            .all()
        )

        similar_items = []
        high_risk_count = 0
        critical_risk_count = 0
        sif_count = 0

        for other_a in all_analyses:
            other_vec = other_a.embedding
            if not other_vec:
                continue

            sim_score = compute_cosine_similarity(current_vector, other_vec)
            # Threshold for semantic relevance (e.g. >= 0.50)
            if sim_score >= 0.40:
                rep: Optional[SafetyReport] = other_a.report
                if not rep:
                    continue

                if other_a.risk_level == "HIGH":
                    high_risk_count += 1
                elif other_a.risk_level == "CRITICAL":
                    critical_risk_count += 1

                if other_a.sif_precursor or other_a.sif_detected:
                    sif_count += 1

                similar_items.append({
                    "report_id": rep.id,
                    "case_id": rep.case_id,
                    "similarity_score": round(sim_score, 2),
                    "task": rep.task,
                    "description": rep.description[:160] + "..." if len(rep.description) > 160 else rep.description,
                    "incident_type": rep.incident_type.value if hasattr(rep.incident_type, "value") else str(rep.incident_type),
                    "risk_level": other_a.risk_level,
                    "risk_score": other_a.risk_score,
                    "sif_precursor": other_a.sif_precursor or other_a.sif_detected,
                    "department": rep.department.name if rep.department else "N/A",
                    "location": rep.location.name if rep.location else "N/A",
                    "reported_at": rep.reported_at.isoformat() if rep.reported_at else None,
                })

        # Sort by similarity score descending
        similar_items.sort(key=lambda x: x["similarity_score"], reverse=True)
        top_matches = similar_items[:8]

        total_count = len(similar_items)
        if total_count == 0:
            summary_text = "No semantically similar historical incidents found in registry."
        else:
            summary_parts = [f"{total_count} similar report{'s' if total_count > 1 else ''} found"]
            if high_risk_count > 0:
                summary_parts.append(f"{high_risk_count} HIGH risk")
            if critical_risk_count > 0:
                summary_parts.append(f"{critical_risk_count} CRITICAL")
            if sif_count > 0:
                summary_parts.append(f"{sif_count} SIF precursor{'s' if sif_count > 1 else ''}")
            summary_text = " (" + ", ".join(summary_parts[1:]) + ")" if len(summary_parts) > 1 else ""
            summary_text = f"{summary_parts[0]}{summary_text}"

        return {
            "similar_reports_count": total_count,
            "high_risk_count": high_risk_count,
            "critical_risk_count": critical_risk_count,
            "sif_count": sif_count,
            "summary_text": summary_text,
            "similar_reports": top_matches,
        }

    def get_similar_incidents(self, report_id: int, db: Session) -> Dict[str, Any]:
        """
        Retrieves detailed similar incidents for a report.
        """
        analysis = db.query(AiAnalysis).filter(AiAnalysis.report_id == report_id).first()
        if not analysis or not analysis.embedding:
            # Run quick feature extraction if no embedding
            report = db.query(SafetyReport).filter(SafetyReport.id == report_id).first()
            if not report:
                raise ValueError(f"Report {report_id} not found.")
            full_text = f"{report.task}. {report.description}"
            prep = self.pipeline.preprocessor.preprocess(full_text)
            haz = self.pipeline.hazard_detector.detect_hazards(prep)
            features = self.pipeline.similarity_engine.extract_features(prep, haz.hazards)
            vector = features.feature_vector
        else:
            vector = analysis.embedding

        summary = self._compute_historical_similarity(
            current_report_id=report_id,
            current_vector=vector,
            db=db,
        )
        return {
            "source_report_id": report_id,
            **summary,
        }


# Global analysis service singleton
analysis_service = AnalysisService()
