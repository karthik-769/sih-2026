import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import (
    BaseLifeSavingRuleMapper,
    PreprocessedText,
    ActivityExtractionResult,
    SifDetectionResult,
    LifeSavingRuleResult,
)


class LifeSavingRuleMappingService(BaseLifeSavingRuleMapper):
    """
    IOGP (International Association of Oil & Gas Producers) Life-Saving Rules Mapping Engine.
    Maps safety observations to official IOGP Life-Saving Rules using multi-dimensional evidence:
    Hazard + Activity + Barrier Failure + Exposure + Narrative Evidence.
    """

    IOGP_RULES_TAXONOMY = [
        {
            "rule": "Energy Isolation",
            "icon": "zap-off",
            "description": "Verify isolation and zero energy before work begins.",
            "hazards": ["ENERGY_ISOLATION", "ELECTRICAL", "PRESSURE_RELEASE", "MACHINE_HAZARD"],
            "barriers": ["LOTO / Energy Isolation", "Zero Energy Verification", "Electrical Isolation", "Pressure Isolation", "Lockout/Tagout"],
            "activities": ["Pump Maintenance", "Electrical Maintenance", "Valve Maintenance", "Equipment Maintenance"],
            "patterns": [
                r"\bloto\b", r"\blockout\b", r"\btagout\b", r"\bzero\s+energy\b",
                r"\bwithout\s+isolat(?:ing|ion)\b", r"\bnot\s+isolated\b", r"\bde-energiz\w*\b",
                r"\benergized\s+panel\b", r"\blive\s+(?:wire|conductor|terminal|equipment)\b"
            ],
            "confidence_base": 0.94,
        },
        {
            "rule": "Confined Space",
            "icon": "box",
            "description": "Obtain authorization before entering a confined space and ensure atmospheric testing.",
            "hazards": ["CONFINED_SPACE", "TOXIC_GAS", "OXYGEN_DEFICIENCY", "CHEMICAL"],
            "barriers": ["Atmospheric Testing", "Standby Person", "Permit to Work", "Gas Detection", "Continuous Ventilation"],
            "activities": ["Confined Space Entry", "Vessel Cleaning", "Tank Cleaning"],
            "patterns": [
                r"\bconfined\s+space\b", r"\bvessel\s+entry\b", r"\btank\s+entry\b", r"\bmanhole\b",
                r"\batmospheric\s+test(?:ing)?\b", r"\bgas\s+test(?:ing)?\b", r"\bstandby\s+person\b",
                r"\bhole\s*watch\b", r"\buntested\s+atmosphere\b", r"\bentered\s+(?:the\s+)?vessel\b"
            ],
            "confidence_base": 0.96,
        },
        {
            "rule": "Work at Height",
            "icon": "arrow-up-circle",
            "description": "Protect yourself against a fall when working at height.",
            "hazards": ["WORKING_AT_HEIGHT", "FALLING_OBJECTS"],
            "barriers": ["Fall Protection", "Safety Harness / Lanyard", "Guardrails & Barricades", "Scaffolding Tagging"],
            "activities": ["Scaffolding", "Elevated Maintenance", "Roof Work", "Rig Work"],
            "patterns": [
                r"\bwork(?:ing)?\s+at\s+height\b", r"\bfall\s+protection\b", r"\bharness\b",
                r"\blanyard\b", r"\belevated\s+platform\b", r"\bscaffold\b", r"\bladder\b",
                r"\bunprotected\s+edge\b", r"\b100%\s+tie-off\b", r"\bopen\s+edge\b"
            ],
            "confidence_base": 0.93,
        },
        {
            "rule": "Line of Fire",
            "icon": "crosshair",
            "description": "Keep yourself and others out of the line of fire and away from moving objects.",
            "hazards": ["FALLING_OBJECTS", "MACHINE_HAZARD", "PRESSURE_RELEASE", "VEHICLE_TRAFFIC"],
            "barriers": ["Exclusion Zone", "Barricading", "Machine Guarding", "Traffic Separation", "Drop Zone Clearance"],
            "activities": ["Lifting Operation", "Vehicle Movement", "Pipeline Maintenance", "Equipment Maintenance"],
            "patterns": [
                r"\bline\s+of\s+fire\b", r"\bsuspended\s+load\b", r"\bswing\s+radius\b",
                r"\bdrop\s*zone\b", r"\bpinch\s+point\b", r"\bunderneath\s+the\s+load\b",
                r"\bstruck\s+by\b", r"\bmoving\s+machinery\b", r"\bstored\s+energy\b"
            ],
            "confidence_base": 0.92,
        },
        {
            "rule": "Hot Work",
            "icon": "flame",
            "description": "Control flammables and ignition sources during hot work.",
            "hazards": ["FIRE_HOT_WORK", "TOXIC_GAS", "CHEMICAL"],
            "barriers": ["Hot Work Permit", "Gas Testing", "Fire Watch", "Combustible Clearing", "Flashback Arrestor"],
            "activities": ["Hot Work", "Welding", "Grinding", "Cutting"],
            "patterns": [
                r"\bhot\s+work\b", r"\bwelding\b", r"\bgas\s+cutting\b", r"\bgrinding\b",
                r"\bflammable\s+vapors\b", r"\bhydrocarbon\s+line\b", r"\bfire\s+watch\b",
                r"\bspark\b", r"\bcombustible\b", r"\bopen\s+flame\b"
            ],
            "confidence_base": 0.93,
        },
        {
            "rule": "Lifting Operations",
            "icon": "anchor",
            "description": "Plan lifting operations and control the area around suspended loads.",
            "hazards": ["FALLING_OBJECTS", "MACHINE_HAZARD"],
            "barriers": ["Lifting Plan", "Certified Rigging", "Exclusion Zone", "Qualified Rigger / Signalman"],
            "activities": ["Lifting Operation", "Rigging", "Crane Maintenance"],
            "patterns": [
                r"\blifting\s+operation\b", r"\bcrane\b", r"\bsuspended\s+load\b", r"\brigging\b",
                r"\brigger\b", r"\bhoist\b", r"\bshackle\b", r"\bsling\b", r"\blifting\s+lug\b",
                r"\btandem\s+lift\b"
            ],
            "confidence_base": 0.91,
        },
        {
            "rule": "Driving",
            "icon": "truck",
            "description": "Follow safe driving rules and maintain vehicle separation.",
            "hazards": ["VEHICLE_TRAFFIC"],
            "barriers": ["Speed Control", "Seatbelts", "Traffic Separation", "Vehicle Pre-check", "Journey Management"],
            "activities": ["Vehicle Movement", "Loading / Unloading", "Transportation"],
            "patterns": [
                r"\bdriving\b", r"\bvehicle\b", r"\bforklift\b", r"\btruck\b", r"\bbowser\b",
                r"\btrailer\b", r"\bspeeding\b", r"\bseat\s*belt\b", r"\breversing\b",
                r"\bpedestrian\s+pathway\b"
            ],
            "confidence_base": 0.90,
        },
        {
            "rule": "Working with Hazardous Substances",
            "icon": "biohazard",
            "description": "Protect yourself from chemical and toxic hazards.",
            "hazards": ["CHEMICAL", "TOXIC_GAS"],
            "barriers": ["Chemical PPE", "Safety Shower / Eyewash", "Ventilation", "Closed Sampling System", "Spill Containment"],
            "activities": ["Chemical Handling", "Loading / Unloading", "Vessel Cleaning"],
            "patterns": [
                r"\bhazardous\s+substance\b", r"\bchemical\b", r"\bcaustic\b", r"\bacid\b",
                r"\btoxic\s+chemical\b", r"\bh2s\b", r"\bcorrosive\b", r"\bchemical\s+splash\b",
                r"\bsds\b", r"\bmsds\b"
            ],
            "confidence_base": 0.91,
        },
        {
            "rule": "Pressure Systems",
            "icon": "gauge",
            "description": "Depressurize and verify zero pressure before breaking containment.",
            "hazards": ["PRESSURE_RELEASE", "ENERGY_ISOLATION"],
            "barriers": ["Pressure Depressurization", "Bleed-off Verification", "Double Block and Bleed", "PRV Testing"],
            "activities": ["Pipeline Maintenance", "Valve Maintenance", "Well Intervention"],
            "patterns": [
                r"\bpressure\s+system\b", r"\bpressurized\b", r"\bhigh\s+pressure\b",
                r"\bdepressuriz\w*\b", r"\bbleed\s+off\b", r"\bflange\s+break\b",
                r"\bbreaking\s+containment\b", r"\bstored\s+pressure\b"
            ],
            "confidence_base": 0.89,
        },
        {
            "rule": "Excavation",
            "icon": "shovel",
            "description": "Obtain clearance before excavating and ensure trench shoring.",
            "hazards": ["MACHINE_HAZARD", "CONFINED_SPACE", "ELECTRICAL"],
            "barriers": ["Excavation Permit", "Underground Cable Detection", "Shoring / Benching", "Barricading"],
            "activities": ["Excavation", "Civil & Construction"],
            "patterns": [
                r"\bexcavation\b", r"\btrench\b", r"\bshor(?:ing|ed)\b", r"\bunderground\s+cable\b",
                r"\bcave-in\b", r"\bdigging\b", r"\btrenching\b"
            ],
            "confidence_base": 0.92,
        },
        {
            "rule": "Electrical Safety",
            "icon": "zap",
            "description": "Only qualified personnel work on electrical systems with verified isolation.",
            "hazards": ["ELECTRICAL", "ENERGY_ISOLATION"],
            "barriers": ["Electrical Isolation", "Insulated Tools", "Arc Flash PPE", "Earth Grounding"],
            "activities": ["Electrical Maintenance"],
            "patterns": [
                r"\belectrical\s+safety\b", r"\belectrical\s+panel\b", r"\bswitchgear\b",
                r"\barc\s+flash\b", r"\belectrocution\b", r"\b6\.6kv\b", r"\b415v\b",
                r"\blive\s+busbar\b", r"\belectrician\b"
            ],
            "confidence_base": 0.93,
        },
        {
            "rule": "Dropped Objects",
            "icon": "arrow-down",
            "description": "Secure tools, equipment, and materials at height to prevent dropped objects.",
            "hazards": ["FALLING_OBJECTS", "WORKING_AT_HEIGHT"],
            "barriers": ["Tool Lanyards", "Toe Boards", "Drop Matting", "Overhead Protection Netting"],
            "activities": ["Scaffolding", "Well Intervention", "Lifting Operation"],
            "patterns": [
                r"\bdropped\s+object\b", r"\bfalling\s+object\b", r"\btool\s+tether\b",
                r"\btool\s+lanyard\b", r"\btoe\s*board\b", r"\bdrop\s*zone\b", r"\bfell\s+from\s+height\b"
            ],
            "confidence_base": 0.90,
        },
    ]

    def map_life_saving_rule(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        exposure: Dict[str, Any],
        activity: ActivityExtractionResult,
        sif_result: SifDetectionResult,
        context: Optional[Dict[str, Any]] = None,
    ) -> LifeSavingRuleResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        hazard_cats = {h.get("category", "") for h in hazards}
        control_names = {c.get("failed_control", "").lower() for c in control_failures}
        activity_name = activity.activity.lower()

        candidate_scores: List[Dict[str, Any]] = []

        for rule in self.IOGP_RULES_TAXONOMY:
            score = 0.0
            evidence: List[str] = []

            # 1. Pattern matching on narrative text
            for pattern in rule["patterns"]:
                match = re.search(pattern, cleaned_lower)
                if match:
                    score += 25.0
                    evidence.append(match.group(0))

            # 2. Hazard category overlap
            for hc in rule["hazards"]:
                if hc in hazard_cats:
                    score += 20.0
                    evidence.append(f"Hazard: {hc}")

            # 3. Control / Barrier failure alignment
            for bf in rule["barriers"]:
                if any(bf.lower() in cn for cn in control_names):
                    score += 25.0
                    evidence.append(f"Failed Barrier: {bf}")

            # 4. Activity alignment
            for act in rule["activities"]:
                if act.lower() in activity_name or activity_name in act.lower():
                    score += 20.0
                    evidence.append(f"Activity: {act}")

            # 5. SIF synergy boost
            if sif_result.sif_precursor and score > 20.0:
                score += 10.0

            if score > 0:
                candidate_scores.append({
                    "rule": rule["rule"],
                    "score": score,
                    "confidence": min(0.98, rule["confidence_base"] + (0.02 if score > 50 else -0.05)),
                    "evidence": list(set(evidence)),
                })

        if candidate_scores:
            # Sort by highest match score
            candidate_scores.sort(key=lambda x: x["score"], reverse=True)
            top = candidate_scores[0]
            return LifeSavingRuleResult(
                life_saving_rule=top["rule"],
                confidence=top["confidence"],
                evidence=top["evidence"],
                matched_rules=candidate_scores[:3],
                is_prototype=False,
            )

        return LifeSavingRuleResult(
            life_saving_rule=None,
            confidence=0.0,
            evidence=[],
            matched_rules=[],
            is_prototype=False,
        )
