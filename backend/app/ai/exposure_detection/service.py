import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseExposureDetector, PreprocessedText, ExposureDetectionResult


class ExposureDetectionService(BaseExposureDetector):
    """
    Evaluates personnel proximity, line-of-fire orientation, and exposed hazard vectors.
    """

    def detect_exposure(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ExposureDetectionResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_categories = {h.get("category") for h in hazards}

        # Check for direct involvement actions
        is_direct_action = bool(re.search(
            r"\b(entered|working|performing|attempted|operating|replacing|began|cleaning|offloading|driver observed|technician)\b",
            cleaned_lower
        ))

        # Check for proximity clues
        if any(w in cleaned_lower for w in ["entered", "inside", "hands-on", "contact", "struck", "touching", "30 cm", "landed near"]):
            proximity = "DIRECT"
            rating = "HIGH"
        elif any(w in cleaned_lower for w in ["near", "meters", "vicinity", "approaching", "bystander", "observed", "adjacent"]):
            proximity = "IMMEDIATE_VICINITY"
            rating = "MODERATE"
        else:
            proximity = "DIRECT" if is_direct_action else "PERIPHERAL"
            rating = "MODERATE" if is_direct_action else "LOW"

        # Safe observation attenuation
        is_safe = any(w in cleaned_lower for w in ["wearing required ppe", "following the approved procedure", "cleaned the area", "routine maintenance"])
        if is_safe and not any(h.get("category") in ["CONFINED_SPACE", "ELECTRICAL", "WORKING_AT_HEIGHT"] and "without" in cleaned_lower for h in hazards):
            rating = "LOW"
            proximity = "PERIPHERAL"

        # Specific exposure vector formulation
        exposed_hazard_list = []
        if "CONFINED_SPACE" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to confined-space atmosphere")
        if "TOXIC_GAS" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to toxic gas / oxygen deficiency")
        if "ELECTRICAL" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to electrical energy")
        if "WORKING_AT_HEIGHT" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to fall hazard")
        if "CHEMICAL" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to hazardous chemicals")
        if "FALLING_OBJECTS" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to overhead suspended load / falling objects")
        if "MACHINE_HAZARD" in hazard_categories:
            exposed_hazard_list.append("Worker exposed to moving machinery / pinch points")

        if not exposed_hazard_list:
            exposed_hazard_str = "No critical energetic exposure identified"
        else:
            exposed_hazard_str = "; ".join(exposed_hazard_list)

        # Extreme rating if critical hazard with direct proximity without control
        if any(cat in ["CONFINED_SPACE", "ELECTRICAL", "WORKING_AT_HEIGHT"] for cat in hazard_categories) and proximity == "DIRECT" and not is_safe:
            rating = "EXTREME" if "without" in cleaned_lower or "no " in cleaned_lower else "HIGH"

        duration = "SHORT_TERM"
        if any(w in cleaned_lower for w in ["shift", "routine", "all day", "continuous", "daily"]):
            duration = "CONTINUOUS"
        elif any(w in cleaned_lower for w in ["intermittent", "periodic", "occasional"]):
            duration = "EXTENDED"

        worker_exposure = {
            "exposure_rating": rating,
            "proximity_level": proximity,
            "duration_estimate": duration,
            "exposed_hazard": exposed_hazard_str,
            "line_of_fire_detected": proximity in ["DIRECT", "IMMEDIATE_VICINITY"],
            "notes": f"Exposure evaluated as {rating} under {proximity.lower()} proximity conditions.",
        }

        return ExposureDetectionResult(
            worker_exposure=worker_exposure,
            is_prototype=False,
        )
