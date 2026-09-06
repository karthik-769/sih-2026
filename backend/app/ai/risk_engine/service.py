from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseRiskEngine, SifDetectionResult, RiskEngineResult


class RiskEngineService(BaseRiskEngine):
    """
    Explainable, Deterministic Quantitative Risk Calculation Engine (0-100).
    Aggregates Hazard Severity, Control Integrity Breakdown, Worker Exposure, and SIF Precursors.
    """

    def calculate_risk(
        self,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        exposure: Dict[str, Any],
        sif_result: SifDetectionResult,
        consequence: Optional[Any] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> RiskEngineResult:
        # Check for pure safe observation or fully controlled practice with no failed barriers
        hazard_categories = {h.get("category") for h in hazards}
        if ("SAFE_OBSERVATION" in hazard_categories or len(control_failures) == 0) and not sif_result.sif_precursor:
            return RiskEngineResult(
                risk_score=15.0,
                risk_level="LOW",
                scoring_breakdown={
                    "base_score": 10.0,
                    "hazard_severity_pts": 5.0,
                    "control_failure_penalty_pts": 0.0,
                    "exposure_multiplier_pts": 0.0,
                    "sif_precursor_boost_pts": 0.0,
                    "synergy_pts": 0.0,
                    "status": "Safe operational practice / controls verified intact",
                },
                is_prototype=False,
            )

        if "SLIP_TRIP_FALL" in hazard_categories and len(hazard_categories) == 1 and len(control_failures) == 0 and not sif_result.sif_precursor:
            return RiskEngineResult(
                risk_score=18.0,
                risk_level="LOW",
                scoring_breakdown={
                    "base_score": 10.0,
                    "hazard_severity_pts": 8.0,
                    "control_failure_penalty_pts": 0.0,
                    "exposure_multiplier_pts": 0.0,
                    "sif_precursor_boost_pts": 0.0,
                    "synergy_pts": 0.0,
                    "status": "Low-level housekeeping observation",
                },
                is_prototype=False,
            )

        base_score = 15.0

        # 1. Hazard Severity Contribution (up to 30 pts)
        hazard_pts = 0.0
        for h in hazards:
            sev = h.get("severity_level", "LOW")
            if sev == "CRITICAL":
                hazard_pts += 15.0
            elif sev == "HIGH":
                hazard_pts += 10.0
            elif sev == "MEDIUM":
                hazard_pts += 5.0
            else:
                hazard_pts += 2.0
        hazard_pts = min(hazard_pts, 30.0)

        # 2. Control Failure Penalty (up to 30 pts)
        control_pts = 0.0
        for cf in control_failures:
            cf_sev = cf.get("severity", "MEDIUM")
            if cf_sev == "CRITICAL":
                control_pts += 15.0
            elif cf_sev == "HIGH":
                control_pts += 10.0
            else:
                control_pts += 5.0
        control_pts = min(control_pts, 30.0)

        # 3. Worker Exposure Contribution (up to 15 pts)
        exp_rating = exposure.get("exposure_rating", "LOW")
        if exp_rating == "EXTREME":
            exp_pts = 15.0
        elif exp_rating == "HIGH":
            exp_pts = 10.0
        elif exp_rating == "MODERATE":
            exp_pts = 5.0
        else:
            exp_pts = 0.0

        # 4. SIF Precursor Severity Boost (up to 25 pts)
        sif_pts = 0.0
        if sif_result.sif_precursor:
            if sif_result.sif_level == "CRITICAL":
                sif_pts = 25.0
            elif sif_result.sif_level == "HIGH":
                sif_pts = 20.0
            elif sif_result.sif_level == "MEDIUM":
                sif_pts = 12.0
            else:
                sif_pts = 5.0

        # 5. Multi-Hazard Synergy Bonus
        synergy_pts = 5.0 if len(hazards) > 2 else 0.0

        raw_score = base_score + hazard_pts + control_pts + exp_pts + sif_pts + synergy_pts
        final_score = round(min(max(raw_score, 0.0), 100.0), 1)

        # Map to Risk Level
        # 0-24: LOW, 25-49: MEDIUM, 50-74: HIGH, 75-100: CRITICAL
        if final_score >= 75.0:
            risk_level = "CRITICAL"
        elif final_score >= 50.0:
            risk_level = "HIGH"
        elif final_score >= 25.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        breakdown = {
            "base_score": base_score,
            "hazard_severity_pts": hazard_pts,
            "control_failure_penalty_pts": control_pts,
            "exposure_multiplier_pts": exp_pts,
            "sif_precursor_boost_pts": sif_pts,
            "synergy_pts": synergy_pts,
            "total_computed_score": final_score,
        }

        return RiskEngineResult(
            risk_score=final_score,
            risk_level=risk_level,
            scoring_breakdown=breakdown,
            is_prototype=False,
        )
