import re
from typing import Dict, Any, List, Optional
from app.ai.interfaces import (
    BaseExplanationGenerator,
    PreprocessedText,
    SifDetectionResult,
    RiskEngineResult,
    LifeSavingRuleResult,
    ConsequenceDetectionResult,
    ActivityExtractionResult,
    ExplanationResult,
)


class ExplanationService(BaseExplanationGenerator):
    """
    Explainable Safety Intelligence Reasoning & Verbatim Evidence Extraction Engine.
    Generates step-by-step audit rationale connecting:
    Hazard -> Exposure -> Barrier Breakdown -> Potential Consequence -> Life-Saving Rule -> SIF Classification.
    """

    def generate_explanation(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        sif_result: SifDetectionResult,
        risk_result: RiskEngineResult,
        life_saving_rule: Optional[LifeSavingRuleResult] = None,
        consequence: Optional[ConsequenceDetectionResult] = None,
        activity: Optional[ActivityExtractionResult] = None,
    ) -> ExplanationResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_types = [h.get("hazard_type", "Hazard") for h in hazards if h.get("category") not in ["GENERAL_OBSERVATION", "SAFE_OBSERVATION"]]
        hazard_names_str = ", ".join(hazard_types) if hazard_types else "routine workplace environment"

        # 1. Identify verbatim evidence snippets from original text
        highlighted_evidence: List[str] = []
        evidence_patterns = [
            r"\bentered\s+(?:a\s+)?confined\s+space\b",
            r"\bwithout\s+atmospheric\s+test(?:ing)?\b",
            r"\bno\s+atmospheric\s+test(?:ing)?\b",
            r"\bwithout\s+gas\s+test(?:ing)?\b",
            r"\bno\s+gas\s+test(?:ing)?\b",
            r"\bno\s+standby\s+person(?:\s+was\s+present)?\b",
            r"\bwithout\s+(?:proper\s+)?fall\s+protection\b",
            r"\bwithout\s+isolating(?:\s+the\s+electrical\s+supply)?\b",
            r"\bnot\s+isolated\b",
            r"\bwithout\s+applying\s+loto\b",
            r"\bpanel\s+was\s+opened\s+without\s+loto\b",
            r"\bremained\s+energized\b",
            r"\bmissing\s+(?:safety\s+)?interlock\b",
            r"\bpanel\s+cover\s+missing\b",
            r"\bexposed\s+energized\b",
            r"\bwithout\s+wearing\s+chemical\s+splash\b",
            r"\bwithout\s+insulated\s+tool\b",
            r"\bbracket\s+broke\s+loose\s+and\s+fell\b",
            r"\bwire\s+rope\s+sling\s+slipped\b",
            r"\bmissing\s+shackle\s+safety\s+pin\b",
            r"\bmissing\s+middle\s+guardrails\b",
            r"\bunfastened\s+toe-boards\b",
            r"\bwithout\s+loto\b",
            r"\bwithout\s+permit\b",
            r"\bwithin\s+the\s+swing\s+radius\b",
            r"\bwithout\s+connecting\s+the\s+fall\s+arrest\b",
            r"\bunderneath\s+suspended\s+load\b",
            r"\bnoticed\s+a\s+small\s+amount\s+of\s+water\b",
            r"\bcleaned\s+the\s+area\b",
            r"\bwearing\s+required\s+ppe\b",
            r"\bfollowing\s+the\s+approved\s+procedure\b",
        ]

        for pattern in evidence_patterns:
            match = re.search(pattern, preprocessed.cleaned_text, flags=re.IGNORECASE)
            if match:
                snippet = match.group(0).strip()
                if snippet not in highlighted_evidence:
                    highlighted_evidence.append(snippet)

        # Fallback to preprocessed phrases
        if not highlighted_evidence and preprocessed.phrases:
            for p in preprocessed.phrases[:2]:
                if len(p) > 10:
                    highlighted_evidence.append(p)

        # 2. Formulate structured natural language explanation
        if risk_result.risk_level == "LOW":
            if any("wearing required ppe" in e.lower() or "following the approved procedure" in e.lower() for e in highlighted_evidence):
                explanation = (
                    "This observation is assessed as LOW risk. Personnel were verified adhering to standard operating "
                    "procedures and utilizing required safeguards without critical barrier degradation."
                )
            elif any("cleaned the area" in e.lower() or "small amount of water" in e.lower() for e in highlighted_evidence):
                explanation = (
                    "This observation is assessed as LOW risk involving routine housekeeping remediation. "
                    "No high-energy hazardous vectors or failed life-critical barriers were observed."
                )
            else:
                explanation = (
                    f"This report is evaluated as LOW risk (Score: {risk_result.risk_score}/100). "
                    f"Workplace condition involves: {hazard_names_str}. "
                    "No Serious Injury & Fatality (SIF) precursor signals were detected."
                )
        else:
            control_names = [cf.get("failed_control") for cf in control_failures]
            control_summary = ", ".join(control_names) if control_names else "compromised safeguard"
            lsr_text = f" [IOGP Life-Saving Rule: {life_saving_rule.life_saving_rule}]" if (life_saving_rule and life_saving_rule.life_saving_rule) else ""
            pot_text = f" Potential worst-case outcome: {consequence.potential_consequence}." if consequence and consequence.potential_consequence else ""
            act_text = f" during '{activity.activity}'" if activity and activity.activity else ""

            if sif_result.sif_precursor:
                explanation = (
                    f"SIF Precursor Flagged ({sif_result.sif_level} severity, Risk Score: {risk_result.risk_score}/100){lsr_text}. "
                    f"Observed condition involves {hazard_names_str}{act_text}. "
                    f"Critical barrier breakdown identified: {control_summary}. "
                    f"Because worker exposure was proximate to high-energy release,{pot_text} "
                    "This situation exhibits significant Serious Injury or Fatality potential requiring immediate HSE intervention."
                )
            else:
                explanation = (
                    f"Classified as {risk_result.risk_level} risk (Score: {risk_result.risk_score}/100){lsr_text}. "
                    f"Identified hazard: {hazard_names_str}. "
                    f"Barrier gap: {control_summary}.{pot_text}"
                )

        return ExplanationResult(
            explanation=explanation,
            highlighted_evidence=highlighted_evidence,
            is_prototype=False,
        )
