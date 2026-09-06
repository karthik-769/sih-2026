import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseSifDetector, PreprocessedText, SifDetectionResult, ConsequenceDetectionResult


class SifDetectionService(BaseSifDetector):
    """
    Serious Injury and Fatality (SIF) Precursor Detection Engine.
    Evaluates confluence of:
      High-Energy Hazard + Worker Proximity/Exposure + Failed/Missing Critical Barrier
      = SIF Precursor (NONE, MEDIUM, HIGH, CRITICAL)
    """

    SIF_PRECURSOR_RULES = [
        {
            "category": "CONFINED_SPACE",
            "sif_category": "Confined Space",
            "energy_source": "ATMOSPHERIC_ASPHYXIATION_TOXIC",
            "required_hazard_categories": ["CONFINED_SPACE", "TOXIC_GAS", "OXYGEN_DEFICIENCY"],
            "description": "Atmospheric entrapment or oxygen depletion inside enclosed structure with fatal asphyxiation potential.",
            "fatality_potential": True,
        },
        {
            "category": "WORKING_AT_HEIGHT",
            "sif_category": "Working at Height",
            "energy_source": "GRAVITATIONAL_POTENTIAL_FALL",
            "required_hazard_categories": ["WORKING_AT_HEIGHT"],
            "description": "Gravitational fall from elevation exceeding 1.8m capable of causing fatal impact trauma.",
            "fatality_potential": True,
        },
        {
            "category": "ELECTRICAL",
            "sif_category": "Electrical Exposure",
            "energy_source": "HIGH_VOLTAGE_ARC_FLASH",
            "required_hazard_categories": ["ELECTRICAL", "ENERGY_ISOLATION"],
            "description": "Contact with live energized conductors or arc-flash potential with fatal electrocution risk.",
            "fatality_potential": True,
        },
        {
            "category": "ENERGY_ISOLATION",
            "sif_category": "Energy Isolation Failure",
            "energy_source": "STORED_HAZARDOUS_ENERGY",
            "required_hazard_categories": ["ENERGY_ISOLATION"],
            "description": "Uncontrolled unexpected release of electrical, mechanical, or fluid energy during intervention.",
            "fatality_potential": True,
        },
        {
            "category": "MACHINE_GUARDING",
            "sif_category": "Machine Guarding Failure",
            "energy_source": "MECHANICAL_CRUSH_ROTATION",
            "required_hazard_categories": ["MACHINE_HAZARD"],
            "description": "Mechanical nip points or unguarded heavy conveyors capable of traumatic amputation or crush.",
            "fatality_potential": True,
        },
        {
            "category": "CHEMICAL",
            "sif_category": "Hazardous Chemicals",
            "energy_source": "CORROSIVE_ACUTE_TOXICITY",
            "required_hazard_categories": ["CHEMICAL"],
            "description": "Bulk corrosive or toxic fluid release causing catastrophic chemical burns or respiratory failure.",
            "fatality_potential": True,
        },
        {
            "category": "FALLING_OBJECTS",
            "sif_category": "Falling Objects / Overhead Loads",
            "energy_source": "GRAVITATIONAL_SUSPENDED_MASS",
            "required_hazard_categories": ["FALLING_OBJECTS"],
            "description": "Failure of rigging, overhead bracket, or dropped heavy tooling into worker occupied zone.",
            "fatality_potential": True,
        },
        {
            "category": "FIRE_HOT_WORK",
            "sif_category": "Fire/Hot Work",
            "energy_source": "THERMAL_EXPLOSIVE_IGNITION",
            "required_hazard_categories": ["FIRE_HOT_WORK"],
            "description": "Uncontrolled thermal energy or ignition in proximity to combustible/flammable atmospheres.",
            "fatality_potential": True,
        },
        {
            "category": "VEHICLE_PEDESTRIAN",
            "sif_category": "Vehicle/Pedestrian Interaction",
            "energy_source": "MOBILE_EQUIPMENT_KINETIC",
            "required_hazard_categories": ["VEHICLE_TRAFFIC"],
            "description": "Heavy industrial transport or crane movement in shared pedestrian operating spaces.",
            "fatality_potential": True,
        },
    ]

    def detect_sif(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        exposure: Dict[str, Any],
        consequence: Optional[ConsequenceDetectionResult] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SifDetectionResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_categories = {h.get("category") for h in hazards}
        precursors: List[Dict[str, Any]] = []
        sif_categories: List[str] = []
        evidence_snippets: List[str] = []

        # Safe observation check -> Check if controls were verified present
        is_safe = any(w in cleaned_lower for w in [
            "wearing required ppe",
            "following the approved procedure",
            "good catch",
            "cleaned the area",
            "safe operational practice",
            "after gas testing",
            "after atmospheric testing",
            "loto verified",
            "standby person verification"
        ])
        has_critical_failure = any(f.get("severity") in ["CRITICAL", "HIGH"] for f in control_failures)

        if is_safe and not has_critical_failure:
            return SifDetectionResult(
                sif_precursor=False,
                sif_categories=[],
                sif_level="NONE",
                sif_precursors=[],
                confidence=0.95,
                fatality_potential=False,
                sif_detected=False,
                sif_reasoning="Controls were verified and active. No critical barrier failure detected.",
                evidence_snippets=["Safe practice / Verified controls present"],
                is_prototype=False,
            )

        # Evaluate SIF rules
        for rule in self.SIF_PRECURSOR_RULES:
            matches_hazard = any(cat in hazard_categories for cat in rule["required_hazard_categories"])
            if matches_hazard:
                precursors.append({
                    "precursor_type": rule["category"],
                    "sif_category": rule["sif_category"],
                    "energy_source": rule["energy_source"],
                    "description": rule["description"],
                    "fatality_potential": rule["fatality_potential"],
                })
                sif_categories.append(rule["sif_category"])

        # Check for Missing Critical Controls
        if control_failures and has_critical_failure:
            if "Missing Critical Controls" not in sif_categories:
                sif_categories.append("Missing Critical Controls")

        exposure_rating = exposure.get("exposure_rating", "LOW")
        has_direct_exposure = exposure_rating in ["HIGH", "EXTREME"] or exposure.get("proximity_level") == "DIRECT"
        has_sif_energy = len(precursors) > 0
        has_failure = len(control_failures) > 0

        # High energy hazard + (Exposure or Barrier failure)
        sif_precursor = has_sif_energy and (has_direct_exposure or has_failure)

        # Non-SIF cases (e.g. simple housekeeping without high energy)
        if "SLIP_TRIP_FALL" in hazard_categories and len(hazard_categories) == 1 and not has_failure:
            sif_precursor = False
            sif_categories = []
            precursors = []

        # Narrative snippet extraction for explainability
        keywords = ["without loto", "no atmospheric testing", "without gas testing", "without fall protection", 
                    "no standby person", "energized panel", "without isolating", "within the swing radius",
                    "entered the vessel", "suspended load", "unprotected edge"]
        for kw in keywords:
            if kw in cleaned_lower:
                evidence_snippets.append(kw)

        if not sif_precursor:
            sif_level = "NONE"
            confidence = 0.90
            fatality_potential = False
            sif_reasoning = "Observation does not meet Serious Injury & Fatality (SIF) precursor threshold."
        else:
            fatality_potential = (consequence.fatality_potential if consequence else False) or any(p.get("fatality_potential", False) for p in precursors)
            if exposure_rating == "EXTREME" and has_critical_failure:
                sif_level = "CRITICAL"
                confidence = 0.96
            elif has_critical_failure or exposure_rating == "HIGH":
                is_vital_hazard = any(p["energy_source"] in ["ATMOSPHERIC_ASPHYXIATION_TOXIC", "HIGH_VOLTAGE_ARC_FLASH", "GRAVITATIONAL_POTENTIAL_FALL", "STORED_HAZARDOUS_ENERGY"] for p in precursors)
                sif_level = "CRITICAL" if is_vital_hazard else "HIGH"
                confidence = 0.93
            else:
                sif_level = "MEDIUM"
                confidence = 0.86

            failed_names = [f.get("failed_control", "") for f in control_failures[:2]]
            haz_names = [h.get("hazard_type", "") for h in hazards[:2]]
            sif_reasoning = (
                f"High-energy hazard ({', '.join(haz_names) if haz_names else 'Identified Hazard'}) "
                f"with {exposure.get('proximity_level', 'DIRECT').lower()} worker exposure and "
                f"failed/missing barrier ({', '.join(failed_names) if failed_names else 'Control breakdown'}). "
                f"Worst-case outcome indicates {sif_level} SIF potential."
            )

        return SifDetectionResult(
            sif_precursor=sif_precursor,
            sif_categories=sif_categories,
            sif_level=sif_level,
            sif_precursors=precursors,
            confidence=confidence,
            fatality_potential=fatality_potential,
            sif_detected=sif_precursor,
            sif_reasoning=sif_reasoning,
            evidence_snippets=evidence_snippets,
            is_prototype=False,
        )
