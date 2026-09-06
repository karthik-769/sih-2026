import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import (
    BaseConsequenceDetector,
    PreprocessedText,
    ConsequenceDetectionResult,
)


class ConsequenceDetectionService(BaseConsequenceDetector):
    """
    NLP Worst-Case Credible Potential Consequence & Fatality Potential Engine.
    Distinguishes observed actual consequence (often 'No injury' or 'Near-miss')
    from the realistic worst-case credible potential outcome had barriers fully failed.
    """

    CONSEQUENCE_MAPPINGS = [
        {
            "hazard_category": "CONFINED_SPACE",
            "potential_consequence": "Fatal toxic gas exposure / acute atmospheric asphyxiation in enclosed space",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bconfined\s+space\b", r"\bvessel\b", r"\btank\b", r"\bmanhole\b", r"\basphyxiat\w*\b"],
        },
        {
            "hazard_category": "ELECTRICAL",
            "potential_consequence": "Fatal electrocution and catastrophic high-energy arc-flash blast",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\belectrical\b", r"\bvoltage\b", r"\benergized\b", r"\bbusbar\b", r"\bswitchgear\b", r"\bshock\b"],
        },
        {
            "hazard_category": "ENERGY_ISOLATION",
            "potential_consequence": "Severe mechanical entrapment, limb amputation, or fatal electrocution from unexpected energy release",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bloto\b", r"\blockout\b", r"\bwithout\s+isolat\w*\b", r"\bzero\s+energy\b"],
        },
        {
            "hazard_category": "WORKING_AT_HEIGHT",
            "potential_consequence": "Fatal gravitational impact / critical multi-system blunt trauma from elevated fall",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bheight\b", r"\bfall\b", r"\bscaffold\b", r"\belevated\b", r"\broof\b", r"\bladder\b"],
        },
        {
            "hazard_category": "FIRE_HOT_WORK",
            "potential_consequence": "Vapor cloud ignition, catastrophic hydrocarbon flash fire, and fatal thermal trauma",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bhot\s+work\b", r"\bwelding\b", r"\bflammable\b", r"\bhydrocarbon\b", r"\bexplosion\b", r"\bsparks\b"],
        },
        {
            "hazard_category": "FALLING_OBJECTS",
            "potential_consequence": "Fatal cranial / spinal blunt force trauma from falling object or suspended load drop",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bsuspended\s+load\b", r"\bdropped\s+object\b", r"\boverhead\b", r"\blifting\b", r"\bfell\b"],
        },
        {
            "hazard_category": "TOXIC_GAS",
            "potential_consequence": "Immediate toxic respiratory failure and fatality from acute H2S / toxic gas inhalation",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bh2s\b", r"\btoxic\s+gas\b", r"\bgas\s+leak\b", r"\batmospheric\b"],
        },
        {
            "hazard_category": "MACHINE_HAZARD",
            "potential_consequence": "Severe mechanical crushing, body entrapment, and permanent disabling injury",
            "severity": "CRITICAL",
            "fatality_potential": True,
            "patterns": [r"\bpinch\s+point\b", r"\bconveyor\b", r"\bcrush\b", r"\bentanglement\b", r"\bmoving\s+machinery\b"],
        },
        {
            "hazard_category": "PRESSURE_RELEASE",
            "potential_consequence": "High-velocity projectile impact, fluid injection trauma, or vessel rupture",
            "severity": "CRITICAL",
            "fatality_potential": True,
            "patterns": [r"\bpressure\b", r"\bpressurized\b", r"\bsteam\b", r"\bburst\b", r"\bhydraulic\b"],
        },
        {
            "hazard_category": "CHEMICAL",
            "potential_consequence": "Severe chemical eye loss, extensive caustic chemical burns, or toxic absorption",
            "severity": "CRITICAL",
            "fatality_potential": False,
            "patterns": [r"\bchemical\b", r"\bacid\b", r"\bcaustic\b", r"\bsplash\b"],
        },
        {
            "hazard_category": "VEHICLE_TRAFFIC",
            "potential_consequence": "Fatal pedestrian impact, vehicle rollover, or heavy transport crush",
            "severity": "FATAL",
            "fatality_potential": True,
            "patterns": [r"\bvehicle\b", r"\bforklift\b", r"\btruck\b", r"\bpedestrian\b", r"\bstruck\s+by\s+vehicle\b"],
        },
        {
            "hazard_category": "SLIP_TRIP_FALL",
            "potential_consequence": "Minor soft tissue contusion, sprain, or same-level laceration",
            "severity": "MINOR",
            "fatality_potential": False,
            "patterns": [r"\bslip\b", r"\btrip\b", r"\bwet\s+floor\b", r"\bpuddle\b"],
        },
    ]

    def detect_consequence(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        exposure: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> ConsequenceDetectionResult:
        context = context or {}
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_cats = {h.get("category", "") for h in hazards}
        
        # Determine actual outcome from narrative & context
        actual = context.get("actual_consequence") or "No injury"
        if "no injury" in cleaned_lower or "no one was injured" in cleaned_lower or "without incident" in cleaned_lower:
            actual = "No injury (Near-miss)"
        elif "first aid" in cleaned_lower or "minor scratch" in cleaned_lower or "minor cut" in cleaned_lower:
            actual = "Minor first-aid treatment"
        elif "medical treatment" in cleaned_lower or "laceration" in cleaned_lower:
            actual = "Medical treatment injury"
        elif "hospitalized" in cleaned_lower or "fracture" in cleaned_lower:
            actual = "Lost Time Injury (LTI)"

        # Determine potential outcome from high-energy hazards & barrier absence
        evidence: List[str] = []
        for mapping in self.CONSEQUENCE_MAPPINGS:
            if mapping["hazard_category"] in hazard_cats:
                evidence.append(f"High-energy hazard: {mapping['hazard_category']}")
                return ConsequenceDetectionResult(
                    actual_consequence=actual,
                    potential_consequence=mapping["potential_consequence"],
                    severity=mapping["severity"],
                    fatality_potential=mapping["fatality_potential"],
                    evidence=evidence,
                    is_prototype=False,
                )

        # Pattern-based matching fallback
        for mapping in self.CONSEQUENCE_MAPPINGS:
            for pattern in mapping["patterns"]:
                if re.search(pattern, cleaned_lower):
                    evidence.append(f"Narrative match: {pattern}")
                    return ConsequenceDetectionResult(
                        actual_consequence=actual,
                        potential_consequence=mapping["potential_consequence"],
                        severity=mapping["severity"],
                        fatality_potential=mapping["fatality_potential"],
                        evidence=evidence,
                        is_prototype=False,
                    )

        return ConsequenceDetectionResult(
            actual_consequence=actual,
            potential_consequence="Minor localized operational disruption or minor first-aid injury",
            severity="MINOR",
            fatality_potential=False,
            evidence=["Routine operational observation"],
            is_prototype=False,
        )
