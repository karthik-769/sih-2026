from typing import Dict, Any, List
from app.ai.interfaces import (
    BaseRecommendationEngine,
    SifDetectionResult,
    RiskEngineResult,
    RecommendationResult,
)


class RecommendationService(BaseRecommendationEngine):
    """
    Actionable Hierarchy-of-Controls Preventive Recommendations Engine.
    Generates targeted, hazard-specific safety directives.
    """

    SPECIFIC_SAFEGUARDS = {
        "CONFINED_SPACE": [
            {
                "priority": 1,
                "hierarchy_level": "ADMINISTRATIVE",
                "action_title": "Perform Multi-Gas Atmospheric Testing Prior to Entry",
                "action_description": "Conduct calibrated multi-gas testing at top, middle, and bottom levels for oxygen (19.5%-23.5%), flammability (<10% LEL), and toxic contaminants before issuing entry clearance.",
            },
            {
                "priority": 2,
                "hierarchy_level": "ADMINISTRATIVE",
                "action_title": "Station Stationed Standby Attendant / Entry Supervisor",
                "action_description": "Deploy a dedicated, trained hole-watch attendant stationed continuously at the portal with direct communication and emergency extraction gear.",
            },
            {
                "priority": 3,
                "hierarchy_level": "ADMINISTRATIVE",
                "action_title": "Enforce Confined Space Entry Permit-to-Work (PTW)",
                "action_description": "Verify isolation of all connected lines (lockout, blanking/blinding), forced ventilation activation, and rescue plan sign-off prior to authorizing personnel entry.",
            },
            {
                "priority": 4,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Deploy Continuous Forced Air Mechanical Ventilation",
                "action_description": "Position explosion-proof positive pressure blowers with ducting routed to bottom of space to maintain continuous fresh air circulation during occupancy.",
            },
        ],
        "WORKING_AT_HEIGHT": [
            {
                "priority": 1,
                "hierarchy_level": "PPE",
                "action_title": "Mandate 100% Fall Arrest Tie-off with Double Lanyards",
                "action_description": "Equip all personnel with certified full-body harness and shock-absorbing lanyards anchored to engineered anchor points rated for >= 22.2 kN (5,000 lbs).",
            },
            {
                "priority": 2,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Install Standard Guardrail System & Drop-Zone Barricades",
                "action_description": "Erect top rails (42 inches), midrails (21 inches), and 4-inch toeboards on all working platforms, and establish rigid ground-level exclusion barricades.",
            },
            {
                "priority": 3,
                "hierarchy_level": "ADMINISTRATIVE",
                "action_title": "Scaffolding Pre-Use Inspection & Scafftag Protocol",
                "action_description": "Require daily formal inspection by a Competent Scaffolding Inspector and tag verification (Green Safe Tag) before allowing worker access.",
            },
        ],
        "ELECTRICAL": [
            {
                "priority": 1,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Execute Verified Lockout/Tagout (LOTO) & Zero-Energy Test",
                "action_description": "Isolate upstream breakers, attach personal safety padlocks/danger tags, and perform 3-point multimeter testing (Live-Dead-Live) to confirm complete de-energization.",
            },
            {
                "priority": 2,
                "hierarchy_level": "PPE",
                "action_title": "Enforce Arc Flash Category PPE & Insulated Tool Kit",
                "action_description": "Mandate arc-rated face shield, NFPA 70E compliant arc flash suit, and 1000V rated insulated hand tools for all switchgear interventions.",
            },
            {
                "priority": 3,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Install Interlocked Panel Barriers & Warning Shields",
                "action_description": "Fit transparent Lexan dead-front covers and electrical interlocks to prevent accidental physical contact with energized busbar conductors.",
            },
        ],
        "CHEMICAL": [
            {
                "priority": 1,
                "hierarchy_level": "PPE",
                "action_title": "Mandate Full Chemical Splash Protection Suit & Face Shield",
                "action_description": "Enforce chemical-resistant neoprene/PVC apron, full-face splash shield over safety goggles, and heavy-duty nitrile gloves during chemical offloading/transfer.",
            },
            {
                "priority": 2,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Verify Emergency Eyewash & Safety Shower Operational Readiness",
                "action_description": "Inspect and test immediate adjacent emergency deluge shower and eye wash station (must deliver >= 15 min flush within 10-second travel distance).",
            },
        ],
        "FALLING_OBJECTS": [
            {
                "priority": 1,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Establish Barricaded Drop-Zone & Overhead Tool Tethering",
                "action_description": "Deploy rigid red barricade tape below elevated work areas and tether all hand tools and components with certified tool lanyards to prevent accidental drops.",
            },
        ],
        "MACHINE_HAZARD": [
            {
                "priority": 1,
                "hierarchy_level": "ENGINEERING",
                "action_title": "Reinstall and Interlock Fixed Machine Enclosure Guards",
                "action_description": "Restore all conveyor nip-point guards and wire emergency stop pull-cords along the full conveyor accessible perimeter.",
            },
        ],
        "SLIP_TRIP_FALL": [
            {
                "priority": 1,
                "hierarchy_level": "ADMINISTRATIVE",
                "action_title": "Immediate Spill Containment & Floor Decontamination",
                "action_description": "Deploy absorbent spill pads, erect yellow Caution Wet Floor warning cones, and maintain clean dry walkway standards.",
            },
        ],
    }

    def generate_recommendations(
        self,
        hazards: List[Dict[str, Any]],
        control_failures: List[Dict[str, Any]],
        sif_result: SifDetectionResult,
        risk_result: RiskEngineResult,
    ) -> RecommendationResult:
        recommendations: List[Dict[str, Any]] = []
        hazard_categories = {h.get("category") for h in hazards}
        assigned_titles = set()
        priority_counter = 1

        # Check for matching specialized safeguards
        for cat in hazard_categories:
            if cat in self.SPECIFIC_SAFEGUARDS:
                for rec in self.SPECIFIC_SAFEGUARDS[cat]:
                    if rec["action_title"] not in assigned_titles:
                        assigned_titles.add(rec["action_title"])
                        recommendations.append({
                            "priority": priority_counter,
                            "hierarchy_level": rec["hierarchy_level"],
                            "action_title": rec["action_title"],
                            "action_description": rec["action_description"],
                        })
                        priority_counter += 1
                        if priority_counter > 5:
                            break
            if priority_counter > 5:
                break

        # Fallback if no specialized category matched
        if not recommendations:
            if risk_result.risk_level in ["HIGH", "CRITICAL"] or sif_result.sif_precursor:
                recommendations.append({
                    "priority": 1,
                    "hierarchy_level": "ENGINEERING",
                    "action_title": "Implement Physical Exclusion & High-Energy Isolation",
                    "action_description": "Establish physical barricades and positive zero-energy lockout before resuming operational activities.",
                })
                recommendations.append({
                    "priority": 2,
                    "hierarchy_level": "ADMINISTRATIVE",
                    "action_title": "Conduct Shift Stand-Down and Procedure Review",
                    "action_description": "Re-brief all assigned technicians on critical control checklists and pre-task safety risk assessments.",
                })
            else:
                recommendations.append({
                    "priority": 1,
                    "hierarchy_level": "ADMINISTRATIVE",
                    "action_title": "Maintain Continuous Good Housekeeping and Inspection",
                    "action_description": "Continue routine shift inspections and immediately report any emerging abnormalities or degraded barriers.",
                })

        return RecommendationResult(
            recommendations=recommendations,
            is_prototype=False,
        )
