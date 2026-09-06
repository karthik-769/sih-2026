import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseHazardDetector, PreprocessedText, HazardDetectionResult


class HazardDetectionService(BaseHazardDetector):
    """
    NLP & Domain Ontology Hazard Detection Engine.
    Identifies hazardous agents, energy sources, operational vectors, and atmospheric threats.
    """

    HAZARD_ONTOLOGY = [
        {
            "category": "CONFINED_SPACE",
            "hazard_type": "Confined Space",
            "patterns": [
                r"\bconfined\s+space\b", r"\bmanhole\b", r"\bvessel\s+entry\b", r"\btank\s+entry\b",
                r"\bsilo\b", r"\bvault\b", r"\bpit\s+entry\b", r"\bsewer\b", r"\benclosed\s+space\b"
            ],
            "description": "Enclosed or partially enclosed space with restricted entry/exit and dangerous atmospheric risk.",
            "confidence": 0.95,
            "severity_level": "CRITICAL",
        },
        {
            "category": "TOXIC_GAS",
            "hazard_type": "Toxic Gas Exposure",
            "patterns": [
                r"\btoxic\s+gas\b", r"\bgas\s+test(?:ing)?\b", r"\batmospheric\s+test(?:ing)?\b",
                r"\bh2s\b", r"\bcarbon\s+monoxide\b", r"\btoxic\s+fumes\b", r"\bchlorine\b",
                r"\bammonia\s+gas\b", r"\bgas\s+leak\b", r"\bhazardous\s+atmosphere\b"
            ],
            "description": "Hazardous airborne contaminants, toxic fumes, or noxious gases with acute toxicity potential.",
            "confidence": 0.92,
            "severity_level": "CRITICAL",
        },
        {
            "category": "OXYGEN_DEFICIENCY",
            "hazard_type": "Oxygen Deficiency",
            "patterns": [
                r"\boxygen\s+deficiency\b", r"\basphyxiation\b", r"\blow\s+oxygen\b",
                r"\batmospheric\s+test(?:ing)?\b", r"\bconfined\s+space\b", r"\bnitrogen\s+purge\b"
            ],
            "description": "Sub-oxygenated atmosphere (<19.5% O2) creating imminent asphyxiation risk.",
            "confidence": 0.88,
            "severity_level": "CRITICAL",
        },
        {
            "category": "WORKING_AT_HEIGHT",
            "hazard_type": "Working at Height",
            "patterns": [
                r"\bheight\b", r"\belevation\b", r"\belevated\b", r"\belevated\s+platform\b",
                r"\bunprotected\s+edge\b", r"\bscaffold(?:ing)?\b", r"\bladder\b",
                r"\broof\b", r"\bworking\s+platform\b", r"\bopen\s+edge\b", r"\bguardrail\b",
                r"\b\d+\s*m(?:eter)?s?\s+(?:height|elevation|drop)\b", r"\bfall\s+protection\b"
            ],
            "description": "Work performed at elevated positions where gravity fall can cause severe trauma or fatality.",
            "confidence": 0.93,
            "severity_level": "HIGH",
        },
        {
            "category": "ELECTRICAL",
            "hazard_type": "Electrical Exposure",
            "patterns": [
                r"\belectrical\b", r"\belectrician\b", r"\bvoltage\b", r"\benergized\b",
                r"\bbusbar\b", r"\bswitchgear\b", r"\btransformer\b", r"\barc\s+flash\b",
                r"\belectric\s+shock\b", r"\b6\.6kv\b", r"\b415v\b", r"\b11kv\b",
                r"\belectrical\s+supply\b", r"\blive\s+wire\b", r"\bbattery\s+bank\b"
            ],
            "description": "High or low voltage electrical energy with fatal electrocution and arc-flash blast risk.",
            "confidence": 0.94,
            "severity_level": "CRITICAL",
        },
        {
            "category": "ENERGY_ISOLATION",
            "hazard_type": "Energy Isolation Failure",
            "patterns": [
                r"\bwithout\s+isolat(?:ing|ion)\b", r"\bnot\s+isolated\b", r"\bloto\b",
                r"\blockout\b", r"\btagout\b", r"\bzero\s+energy\b", r"\bde-energiz(?:ed|ation)\b",
                r"\bisolating\s+the\s+electrical\s+supply\b", r"\bisolation\s+failure\b"
            ],
            "description": "Inadequate or absent lockout/tagout leading to unexpected release of hazardous energy.",
            "confidence": 0.92,
            "severity_level": "HIGH",
        },
        {
            "category": "CHEMICAL",
            "hazard_type": "Hazardous Chemicals",
            "patterns": [
                r"\bchemical\b", r"\bcaustic\b", r"\bacid\b", r"\bsulfuric\b", r"\bhydrochloric\b",
                r"\bcorrosive\b", r"\bsplash\b", r"\boffloading\b", r"\bchemical\s+burn\b",
                r"\btoxic\s+release\b", r"\bsolvent\b"
            ],
            "description": "Corrosive, toxic, or reactive chemical agents capable of severe chemical burns or systemic poisoning.",
            "confidence": 0.90,
            "severity_level": "HIGH",
        },
        {
            "category": "FALLING_OBJECTS",
            "hazard_type": "Falling Objects",
            "patterns": [
                r"\bfell\b", r"\bfalling\b", r"\bdropped\s+object\b", r"\boverhead\b",
                r"\bbracket\s+fell\b", r"\bdrop\s*zone\b", r"\bsuspended\s+load\b",
                r"\blifting\s+lug\b", r"\brigging\s+slip\b", r"\bhoist\b"
            ],
            "description": "Unsecured overhead objects or suspended masses with gravitational impact potential.",
            "confidence": 0.91,
            "severity_level": "HIGH",
        },
        {
            "category": "MACHINE_HAZARD",
            "hazard_type": "Machine Hazard / Moving Machinery",
            "patterns": [
                r"\bconveyor\b", r"\broller\b", r"\bcrush\b", r"\bpinch\s+point\b",
                r"\brotating\b", r"\bmachine\s+guard\b", r"\bgearbox\b", r"\bentanglement\b",
                r"\bdrive\s+belt\b", r"\bchain\s+drive\b", r"\bmoving\s+machinery\b"
            ],
            "description": "Unguarded or moving mechanical parts with pinch, entrapment, and crush hazards.",
            "confidence": 0.89,
            "severity_level": "HIGH",
        },
        {
            "category": "FIRE_HOT_WORK",
            "hazard_type": "Fire / Hot Work",
            "patterns": [
                r"\bfire\b", r"\bhot\s+work\b", r"\bwelding\b", r"\btorch\b", r"\bsparks\b",
                r"\bflame\b", r"\bcombustible\b", r"\bflammable\b", r"\bignition\b", r"\bexplosion\b"
            ],
            "description": "Open flame, hot slag, thermal ignition, or explosive atmospheric deflagration.",
            "confidence": 0.88,
            "severity_level": "HIGH",
        },
        {
            "category": "PRESSURE_RELEASE",
            "hazard_type": "Pressure / Fluid Release",
            "patterns": [
                r"\bpressure\b", r"\bsteam\b", r"\bpressurized\b", r"\brelief\s+valve\b",
                r"\bhydraulic\b", r"\bflange\s+leak\b", r"\bhigh\s+pressure\b", r"\bburst\b"
            ],
            "description": "Stored pneumatic, hydraulic, or steam pressure capable of violent discharge.",
            "confidence": 0.85,
            "severity_level": "MEDIUM",
        },
        {
            "category": "VEHICLE_TRAFFIC",
            "hazard_type": "Vehicle / Pedestrian Interaction",
            "patterns": [
                r"\bforklift\b", r"\btruck\b", r"\bvehicle\b", r"\bmobile\s+equipment\b",
                r"\bloader\b", r"\bcrane\s+travel\b", r"\btraffic\b", r"\bpedestrian\b",
                r"\breversing\b", r"\bstruck\s+by\s+vehicle\b"
            ],
            "description": "Heavy industrial transport or mobile plant operating in worker pedestrian thoroughfares.",
            "confidence": 0.87,
            "severity_level": "HIGH",
        },
        {
            "category": "SLIP_TRIP_FALL",
            "hazard_type": "Slip / Trip / Fall",
            "patterns": [
                r"\bslip\b", r"\btrip\b", r"\bwater\s+near\b", r"\bwet\s+floor\b",
                r"\bpuddle\b", r"\bspill\s+on\s+floor\b", r"\buneven\s+surface\b",
                r"\bhousekeeping\b", r"\bcleaned\s+the\s+area\b"
            ],
            "description": "Same-level footing hazard due to liquid residue, debris, or surface irregularity.",
            "confidence": 0.86,
            "severity_level": "LOW",
        },
    ]

    def detect_hazards(self, preprocessed: PreprocessedText, context: Optional[Dict[str, Any]] = None) -> HazardDetectionResult:
        detected: List[Dict[str, Any]] = []
        cleaned_lower = preprocessed.cleaned_text.lower()
        matched_categories = set()

        for ont in self.HAZARD_ONTOLOGY:
            matched_keywords = []
            for pattern in ont["patterns"]:
                matches = re.findall(pattern, cleaned_lower)
                if matches:
                    matched_keywords.extend(matches if isinstance(matches[0], str) else [matches[0]])

            if matched_keywords:
                matched_categories.add(ont["category"])
                detected.append({
                    "category": ont["category"],
                    "hazard_type": ont["hazard_type"],
                    "description": ont["description"],
                    "confidence": ont["confidence"],
                    "severity_level": ont["severity_level"],
                    "keywords_matched": list(set(matched_keywords)),
                })

        # Contextual Hazard Synergy Logic
        # e.g., Confined Space without testing automatically triggers Toxic Gas & Oxygen Deficiency
        if "CONFINED_SPACE" in matched_categories and ("TOXIC_GAS" not in matched_categories or "OXYGEN_DEFICIENCY" not in matched_categories):
            is_gas_tested = "after gas testing" in cleaned_lower or "after atmospheric testing" in cleaned_lower or "gas testing completed" in cleaned_lower
            if not is_gas_tested and ("without atmospheric testing" in cleaned_lower or "no gas test" in cleaned_lower or "without gas testing" in cleaned_lower or "untested" in cleaned_lower):
                if "TOXIC_GAS" not in matched_categories:
                    detected.append({
                        "category": "TOXIC_GAS",
                        "hazard_type": "Toxic Gas Exposure",
                        "description": "Hazardous atmospheric contaminant accumulation in unventilated confined volume.",
                        "confidence": 0.91,
                        "severity_level": "CRITICAL",
                        "keywords_matched": ["confined space", "untested atmosphere"],
                    })
                if "OXYGEN_DEFICIENCY" not in matched_categories:
                    detected.append({
                        "category": "OXYGEN_DEFICIENCY",
                        "hazard_type": "Oxygen Deficiency",
                        "description": "Displacement or depletion of breathable oxygen inside enclosed vessel.",
                        "confidence": 0.89,
                        "severity_level": "CRITICAL",
                        "keywords_matched": ["confined space", "no atmospheric testing"],
                    })

        # Fallback if text describes safe condition or unspecified general observation
        if not detected:
            if any(w in cleaned_lower for w in ["ppe", "wearing", "approved procedure", "compliant", "safe", "routine"]):
                detected.append({
                    "category": "SAFE_OBSERVATION",
                    "hazard_type": "Safe Operational Practice",
                    "description": "Workers observed following approved procedures and standard safeguards.",
                    "confidence": 0.95,
                    "severity_level": "LOW",
                    "keywords_matched": ["safe observation", "compliant"],
                })
            else:
                detected.append({
                    "category": "GENERAL_OBSERVATION",
                    "hazard_type": "Operational Workplace Observation",
                    "description": "General safety observation captured for facility tracking.",
                    "confidence": 0.60,
                    "severity_level": "LOW",
                    "keywords_matched": [],
                })

        return HazardDetectionResult(
            hazards=detected,
            is_prototype=False,
        )
