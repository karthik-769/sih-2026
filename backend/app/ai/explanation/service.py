import re
from typing import Dict, Any, List
from app.ai.interfaces import (
    BaseExplanationGenerator,
    PreprocessedText,
    SifDetectionResult,
    RiskEngineResult,
    ExplanationResult,
)


class ExplanationService(BaseExplanationGenerator):
    """
    Generates structured, human-readable safety intelligence explanations.
    Addresses danger rationale, detected hazards, control breakdowns, and serious consequence pathways,
    while isolating key verbatim highlighted evidence from the original report text.
    """

    def generate_explanation(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        sif_result: SifDetectionResult,
        risk_result: RiskEngineResult,
    ) -> ExplanationResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_types = [h.get("hazard_type", "Hazard") for h in hazards if h.get("category") not in ["GENERAL_OBSERVATION", "SAFE_OBSERVATION"]]
        hazard_names_str = ", ".join(hazard_types) if hazard_types else "routine workplace environment"

        # 1. Identify highlighted verbatim evidence phrases from original text
        highlighted_evidence: List[str] = []
        evidence_patterns = [
            r"\bentered\s+(?:a\s+)?confined\s+space\b",
            r"\bwithout\s+atmospheric\s+test(?:ing)?\b",
            r"\bno\s+atmospheric\s+test(?:ing)?\b",
            r"\bno\s+standby\s+person(?:\s+was\s+present)?\b",
            r"\bwithout\s+(?:proper\s+)?fall\s+protection\b",
            r"\bwithout\s+isolating(?:\s+the\s+electrical\s+supply)?\b",
            r"\bnot\s+isolated\b",
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

        # Fallback if no specific regex triggered: pick salient phrase
        if not highlighted_evidence and preprocessed.phrases:
            for p in preprocessed.phrases[:2]:
                if len(p) > 10:
                    highlighted_evidence.append(p)

        # 2. Formulate structured natural language explanation
        if risk_result.risk_level == "LOW":
            if any("wearing required ppe" in e.lower() or "following the approved procedure" in e.lower() for e in highlighted_evidence):
                explanation = (
                    "This report is classified as LOW risk because personnel were verified adhering to standard safe operating "
                    "procedures and wearing appropriate personal protective equipment without compromised safety barriers."
                )
            elif any("cleaned the area" in e.lower() or "small amount of water" in e.lower() for e in highlighted_evidence):
                explanation = (
                    "This report is classified as LOW risk involving routine housekeeping and immediate floor remediation. "
                    "No high-energy hazards or critical control failures were present."
                )
            else:
                explanation = (
                    f"This report is classified as LOW risk (Score: {risk_result.risk_score}/100). "
                    f"Identified conditions: {hazard_names_str}. "
                    "No immediate Serious Injury or Fatality (SIF) precursors were detected."
                )
        else:
            control_names = [cf.get("failed_control") for cf in control_failures]
            control_summary = ", ".join(control_names) if control_names else "unverified safeguards"

            danger_clause = f"This report is classified as {risk_result.risk_level} (Score: {risk_result.risk_score}/100) because "

            if sif_result.sif_precursor:
                sif_cat_str = ", ".join(sif_result.sif_categories) if sif_result.sif_categories else "High-Energy Hazard"
                consequence_clause = (
                    f"These are critical control breakdowns ({control_summary}) involving {sif_cat_str} that directly expose "
                    f"the worker to high-energy vectors and could result in a serious, life-altering injury or fatality (SIF event)."
                )
            else:
                consequence_clause = (
                    f"Control evaluation identified: {control_summary}. "
                    "Without timely remediation, repeated exposure could escalate operational risk."
                )

            explanation = (
                f"{danger_clause}the operational activity involves {hazard_names_str}. "
                f"{consequence_clause}"
            )

        return ExplanationResult(
            explanation=explanation,
            highlighted_evidence=highlighted_evidence,
            is_prototype=False,
        )
