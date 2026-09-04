import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.alert import Alert
from app.models.location import Location
from app.models.department import Department
from app.services.patterns.pattern_engine import pattern_engine

logger = logging.getLogger(__name__)


class EarlyWarningEngine:
    """
    Evaluates safety patterns and recent incident records against early warning rules.
    Generates data-backed alerts with evidence explanations and built-in deduplication.
    """

    def evaluate_patterns_and_generate_alerts(self, db: Session) -> List[Alert]:
        """
        Runs pattern detection and evaluates early warning rules to generate/update alerts.
        """
        # 1. Update patterns
        patterns = pattern_engine.analyze_all_patterns(db)
        generated_alerts: List[Alert] = []

        for p in patterns:
            alert = self._evaluate_pattern_for_alert(p, db)
            if alert:
                generated_alerts.append(alert)

        db.commit()
        return generated_alerts

    def _evaluate_pattern_for_alert(self, pattern: Pattern, db: Session) -> Optional[Alert]:
        """
        Checks if a pattern breaches early warning threshold rules.
        """
        # Rule threshold check:
        # Generate alert if risk_score >= 40 OR sif_count >= 1 OR frequency >= 3 OR trend >= 25%
        should_alert = (
            pattern.risk_score >= 40.0
            or pattern.sif_count >= 1
            or pattern.frequency_count >= 3
            or pattern.trend_percentage >= 25.0
        )

        if not should_alert:
            return None

        # Determine Alert Type
        if pattern.sif_count >= 2:
            alert_type = "REPEATED_SIF_PRECURSOR"
        elif pattern.pattern_type == "LOCATION_CONCENTRATION":
            alert_type = "HIGH_RISK_LOCATION"
        elif pattern.trend_percentage >= 30.0:
            alert_type = "INCREASING_TREND"
        elif pattern.scoring_factors.get("control_failure_factor", 0) >= 10:
            alert_type = "REPEATED_CONTROL_FAILURE"
        elif pattern.risk_score >= 70:
            alert_type = "REPEATED_HIGH_RISK_HAZARD"
        else:
            alert_type = "COMBINED_RISK"

        # Severity
        if pattern.risk_score >= 70 or pattern.sif_count >= 2:
            severity = "CRITICAL"
        elif pattern.risk_score >= 50 or pattern.sif_count >= 1:
            severity = "HIGH"
        elif pattern.risk_score >= 30:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        # Resolve location & department names
        loc_name = pattern.location.name if pattern.location else "Multiple Units"
        dept_name = pattern.department.name if pattern.department else "Operations"

        title = f"Early Warning: {pattern.title}"
        description = (
            f"Automated early warning triggered by {pattern.frequency_count} recurring reports "
            f"involving {pattern.hazard_category or 'critical safety risks'} across {loc_name} ({dept_name})."
        )

        # Build Data-Backed Explanation Evidence
        explanation_evidence = self._generate_explanation_evidence(pattern, loc_name, dept_name, db)

        alert_key = f"ALERT_{pattern.pattern_key}"

        return self._upsert_alert(
            alert_key=alert_key,
            pattern_id=pattern.id,
            alert_type=alert_type,
            title=title,
            description=description,
            severity=severity,
            risk_score=pattern.risk_score,
            department_id=pattern.department_id,
            location_id=pattern.location_id,
            hazard_category=pattern.hazard_category,
            sif_category=pattern.sif_category,
            explanation_evidence=explanation_evidence,
            contributing_report_ids=pattern.evidence_report_ids or [],
            contributing_case_ids=pattern.evidence_case_ids or [],
            recommended_actions=pattern.recommendations or [],
            db=db,
        )

    def _generate_explanation_evidence(
        self,
        pattern: Pattern,
        loc_name: str,
        dept_name: str,
        db: Session,
    ) -> List[str]:
        """
        Creates factual, data-driven explanation bullet points based on actual database evidence.
        """
        evidence = []
        evidence.append(f"{pattern.frequency_count} related safety reports recorded in active monitoring period.")

        if pattern.sif_count > 0:
            evidence.append(
                f"{pattern.sif_count} report(s) classified as Serious Injury or Fatality (SIF) precursors."
            )

        if pattern.hazard_category:
            evidence.append(f"Primary recurring hazard identified: {pattern.hazard_category}.")

        if pattern.location_id:
            evidence.append(f"Location concentration: {loc_name} accounts for the majority of these hazard reports.")

        if pattern.department_id:
            evidence.append(f"Department involved: {dept_name} operations and maintenance.")

        if pattern.trend_percentage > 0:
            evidence.append(f"Hazard incident frequency increased by {pattern.trend_percentage}% over previous period.")

        # Add contributing Case IDs
        if pattern.evidence_case_ids:
            case_preview = ", ".join(pattern.evidence_case_ids[:5])
            if len(pattern.evidence_case_ids) > 5:
                case_preview += f" (+{len(pattern.evidence_case_ids) - 5} more)"
            evidence.append(f"Contributing incident cases: {case_preview}.")

        return evidence

    def _upsert_alert(
        self,
        alert_key: str,
        pattern_id: Optional[int],
        alert_type: str,
        title: str,
        description: str,
        severity: str,
        risk_score: float,
        department_id: Optional[int],
        location_id: Optional[int],
        hazard_category: Optional[str],
        sif_category: Optional[str],
        explanation_evidence: List[str],
        contributing_report_ids: List[int],
        contributing_case_ids: List[str],
        recommended_actions: List[str],
        db: Session,
    ) -> Alert:
        """
        Ensures alert deduplication: If an active alert exists for this pattern,
        updates the evidence and score rather than creating duplicates.
        """
        existing = db.query(Alert).filter(Alert.alert_key == alert_key).first()

        if existing:
            # Update existing alert with new evidence
            existing.title = title
            existing.description = description
            existing.severity = severity
            existing.risk_score = risk_score
            existing.explanation_evidence = explanation_evidence
            existing.contributing_report_ids = contributing_report_ids
            existing.contributing_case_ids = contributing_case_ids
            existing.recommended_actions = recommended_actions
            existing.department_id = department_id
            existing.location_id = location_id
            existing.hazard_category = hazard_category
            existing.sif_category = sif_category
            # If it was resolved earlier but risk recurred, reactivate
            if existing.status in ["RESOLVED", "DISMISSED"]:
                existing.status = "NEW"
            db.add(existing)
            return existing
        else:
            new_alert = Alert(
                alert_key=alert_key,
                pattern_id=pattern_id,
                alert_type=alert_type,
                title=title,
                description=description,
                severity=severity,
                risk_score=risk_score,
                department_id=department_id,
                location_id=location_id,
                hazard_category=hazard_category,
                sif_category=sif_category,
                explanation_evidence=explanation_evidence,
                contributing_report_ids=contributing_report_ids,
                contributing_case_ids=contributing_case_ids,
                recommended_actions=recommended_actions,
                status="NEW",
            )
            db.add(new_alert)
            return new_alert


early_warning_engine = EarlyWarningEngine()
