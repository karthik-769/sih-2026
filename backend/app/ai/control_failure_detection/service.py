import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseControlFailureDetector, PreprocessedText, ControlFailureResult


class ControlFailureDetectionService(BaseControlFailureDetector):
    """
    Structured Barrier & Control Failure Detection Engine for OIL Operations.
    Classifies missing, bypassed, or failed safeguards across the IOGP/OSHA Barrier Hierarchy.
    """

    BARRIER_FAILURE_RULES = [
        {
            "barrier_name": "LOTO / Energy Isolation",
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Energy isolation failure / No LOTO",
            "patterns": [
                r"\bwithout\s+isolat(?:ing|ion)\b", r"\bnot\s+isolated\b",
                r"\bwithout\s+isolating\s+the\s+electrical\s+supply\b",
                r"\bno\s+loto\b", r"\bno\s+lockout\b", r"\bwithout\s+loto\b",
                r"\bnot\s+de-energiz(?:ed|ation)\b", r"\blive\s+maintenance\b",
                r"\bwithout\s+tagout\b", r"\bwithout\s+applying\s+loto\b",
                r"\bremained\s+energized\b", r"\bzero\s+energy\s+not\s+verified\b"
            ],
            "description": "Failure to achieve and verify positive zero-energy state prior to intrusive work.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "Atmospheric Testing",
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "No atmospheric testing / Gas testing failure",
            "patterns": [
                r"\bwithout\s+atmospheric\s+test(?:ing)?\b",
                r"\bno\s+atmospheric\s+test(?:ing)?\b",
                r"\bno\s+gas\s+test(?:ing)?\b",
                r"\bwithout\s+gas\s+test(?:ing)?\b",
                r"\bgas\s+testing\s+not\s+performed\b",
                r"\buntested\s+atmosphere\b",
                r"\bwithout\s+confirming\s+gas\s+testing\b"
            ],
            "description": "Personnel entered potentially hazardous volume without pre-entry multi-gas atmospheric verification.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "Standby Person",
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "No standby person / Attendant missing",
            "patterns": [
                r"\bno\s+standby\s+person\b",
                r"\bwithout\s+(?:a\s+)?standby\s+person\b",
                r"\bno\s+attendant\b",
                r"\bno\s+hole\s*watch\b",
                r"\bstandby\s+person\s+was\s+not\s+present\b",
                r"\bentered\s+alone\b"
            ],
            "description": "Confined space or high-hazard activity conducted without dedicated stationed safety attendant.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "Fall Protection",
            "hierarchy_level": "PPE",
            "failed_control": "No fall protection / Harness unhooked",
            "patterns": [
                r"\bwithout\s+(?:proper\s+)?fall\s+protection\b",
                r"\bno\s+fall\s+protection\b",
                r"\bno\s+harness\b",
                r"\bwithout\s+harness\b",
                r"\bharness\s+not\s+tied\s+off\b",
                r"\bno\s+lanyard\b",
                r"\bwithout\s+connecting\s+the\s+fall\s+arrest\b",
                r"\bmissing\s+middle\s+guardrails\b",
                r"\bunprotected\s+edge\b"
            ],
            "description": "Elevated task executed without personal fall arrest system (PFAS) or positive edge protection.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "Permit to Work",
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "Permit to Work missing / unauthorized start",
            "patterns": [
                r"\bwithout\s+permit\b",
                r"\bno\s+permit\b",
                r"\bno\s+ptw\b",
                r"\bpermit\s+not\s+issued\b",
                r"\bwithout\s+valid\s+permit\b",
                r"\bexpired\s+permit\b",
                r"\bhot\s+work\s+without\s+permit\b"
            ],
            "description": "High-risk task initiated without approved permit-to-work or job safety analysis (JSA).",
            "severity": "HIGH",
        },
        {
            "barrier_name": "Exclusion Zone",
            "hierarchy_level": "ENGINEERING",
            "failed_control": "No exclusion zone / Line of fire violation",
            "patterns": [
                r"\bno\s+exclusion\s+zone\b",
                r"\bwithin\s+the\s+swing\s+radius\b",
                r"\bunderneath\s+suspended\s+load\b",
                r"\bno\s+barricade\b",
                r"\bno\s+drop\s*zone\b",
                r"\bwalked\s+under\b",
                r"\bunauthorized\s+entry\s+in\s+work\s+area\b"
            ],
            "description": "Failure to establish or enforce physical perimeter around high-energy hazard zones.",
            "severity": "HIGH",
        },
        {
            "barrier_name": "Machine Guarding",
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Machine guarding missing or removed",
            "patterns": [
                r"\bguard\s+removed\b",
                r"\bmissing\s+guard\b",
                r"\bunguarded\s+conveyor\b",
                r"\bexposed\s+rotating\b",
                r"\bmissing\s+interlock\b",
                r"\bpanel\s+cover\s+missing\b"
            ],
            "description": "Physical safeguarding, coupling covers, or machine interlocks bypassed or omitted.",
            "severity": "HIGH",
        },
        {
            "barrier_name": "Electrical Isolation",
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Live electrical working / Inadequate grounding",
            "patterns": [
                r"\benergized\s+panel\b",
                r"\blive\s+circuit\b",
                r"\bwithout\s+insulat(?:ed|ion)\b",
                r"\bno\s+grounding\b",
                r"\bunearthed\b",
                r"\bmissing\s+arc\s+flash\s+shield\b"
            ],
            "description": "Direct interaction with energized electrical components without verified electrical isolation.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "Pressure Isolation",
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Pressure bleed-off omitted / Flange opened under pressure",
            "patterns": [
                r"\bunder\s+pressure\b",
                r"\bnot\s+depressuriz\w*\b",
                r"\bwithout\s+bleeding\s+off\b",
                r"\bline\s+pressurized\b",
                r"\bopened\s+pressurized\s+flange\b"
            ],
            "description": "Breaking pressurized containment without positive double-block and bleed verification.",
            "severity": "CRITICAL",
        },
        {
            "barrier_name": "PPE",
            "hierarchy_level": "PPE",
            "failed_control": "Personal Protective Equipment missing / non-compliant",
            "patterns": [
                r"\bwithout\s+wearing\b",
                r"\bwithout\s+ppe\b",
                r"\bno\s+ppe\b",
                r"\bonly\s+wearing\s+standard\b",
                r"\bwithout\s+face\s+shield\b",
                r"\bwithout\s+chemical\s+gloves\b",
                r"\bfailed\s+to\s+wear\b",
                r"\bno\s+safety\s+glasses\b"
            ],
            "description": "Failure to wear task-mandated PPE for specific chemical, thermal, or impact risks.",
            "severity": "MEDIUM",
        },
        {
            "barrier_name": "Procedure Compliance",
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "SOP deviation / Procedural shortcut",
            "patterns": [
                r"\bprocedure\s+not\s+followed\b",
                r"\bshortcut\b",
                r"\bwithout\s+removing\s+combustible\b",
                r"\bunapproved\s+method\b",
                r"\bdeviated\s+from\s+sop\b",
                r"\bwithout\s+toolbox\s+talk\b"
            ],
            "description": "Execution of operational task in direct contravention of standard operating procedures.",
            "severity": "MEDIUM",
        },
    ]

    def detect_failures(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> ControlFailureResult:
        failures: List[Dict[str, Any]] = []
        failed_barriers: List[Dict[str, Any]] = []
        barrier_names: List[str] = []
        
        cleaned_lower = preprocessed.cleaned_text.lower()
        matched_barriers = set()

        for rule in self.BARRIER_FAILURE_RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, cleaned_lower):
                    bname = rule["barrier_name"]
                    if bname not in matched_barriers:
                        matched_barriers.add(bname)
                        barrier_names.append(bname)
                        failed_barriers.append({
                            "barrier_name": bname,
                            "hierarchy_level": rule["hierarchy_level"],
                            "severity": rule["severity"],
                            "description": rule["description"],
                        })
                        failures.append({
                            "hierarchy_level": rule["hierarchy_level"],
                            "failed_control": rule["failed_control"],
                            "description": rule["description"],
                            "severity": rule["severity"],
                        })
                    break

        # Implied barrier failure logic for high hazard observations without safe keywords
        is_safe = any(w in cleaned_lower for w in [
            "wearing required ppe", "approved procedure", "safe condition", "all controls in place",
            "compliant", "safe observation", "after gas testing", "after atmospheric testing",
            "standby person verification", "standby person was stationed", "loto verified", "zero energy verified"
        ])
        if not failures and not is_safe:
            for h in hazards:
                cat = h.get("category")
                if cat == "CONFINED_SPACE" and "Atmospheric Testing" not in matched_barriers:
                    bname = "Atmospheric Testing"
                    matched_barriers.add(bname)
                    barrier_names.append(bname)
                    failed_barriers.append({
                        "barrier_name": bname,
                        "hierarchy_level": "ADMINISTRATIVE",
                        "severity": "HIGH",
                        "description": "Mandatory confined space pre-entry gas testing verification required.",
                    })
                    failures.append({
                        "hierarchy_level": "ADMINISTRATIVE",
                        "failed_control": "Atmospheric Testing Verification Required",
                        "description": "Mandatory confined space pre-entry gas testing verification required.",
                        "severity": "HIGH",
                    })
                elif cat == "WORKING_AT_HEIGHT" and "Fall Protection" not in matched_barriers:
                    bname = "Fall Protection"
                    matched_barriers.add(bname)
                    barrier_names.append(bname)
                    failed_barriers.append({
                        "barrier_name": bname,
                        "hierarchy_level": "PPE",
                        "severity": "HIGH",
                        "description": "Elevated maintenance requires 100% positive tie-off verification.",
                    })
                    failures.append({
                        "hierarchy_level": "PPE",
                        "failed_control": "Missing Fall Protection Verification",
                        "description": "Elevated maintenance requires 100% positive tie-off verification.",
                        "severity": "HIGH",
                    })
                elif cat == "ELECTRICAL" and "LOTO / Energy Isolation" not in matched_barriers:
                    bname = "LOTO / Energy Isolation"
                    matched_barriers.add(bname)
                    barrier_names.append(bname)
                    failed_barriers.append({
                        "barrier_name": bname,
                        "hierarchy_level": "ENGINEERING",
                        "severity": "HIGH",
                        "description": "Positive zero-energy lock and tag verification required.",
                    })
                    failures.append({
                        "hierarchy_level": "ENGINEERING",
                        "failed_control": "LOTO / Energy Isolation Verification",
                        "description": "Positive zero-energy lock and tag verification required.",
                        "severity": "HIGH",
                    })

        return ControlFailureResult(
            control_failures=failures,
            failed_barriers=failed_barriers,
            barrier_names=barrier_names,
            is_prototype=False,
        )
