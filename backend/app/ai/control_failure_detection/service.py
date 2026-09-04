import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseControlFailureDetector, PreprocessedText, ControlFailureResult


class ControlFailureDetectionService(BaseControlFailureDetector):
    """
    Identifies missing, failed, or bypassed critical safety controls across the Hierarchy of Controls.
    """

    CRITICAL_CONTROL_RULES = [
        {
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "No atmospheric testing",
            "patterns": [
                r"\bwithout\s+atmospheric\s+test(?:ing)?\b",
                r"\bno\s+atmospheric\s+test(?:ing)?\b",
                r"\bno\s+gas\s+test(?:ing)?\b",
                r"\bwithout\s+gas\s+test(?:ing)?\b",
                r"\bgas\s+testing\s+not\s+performed\b",
                r"\buntested\s+atmosphere\b"
            ],
            "description": "Personnel entered potentially hazardous volume without pre-entry multi-gas atmospheric verification.",
            "severity": "CRITICAL",
        },
        {
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "No standby person",
            "patterns": [
                r"\bno\s+standby\s+person\b",
                r"\bwithout\s+(?:a\s+)?standby\s+person\b",
                r"\bno\s+attendant\b",
                r"\bno\s+hole\s*watch\b",
                r"\bstandby\s+person\s+was\s+not\s+present\b",
                r"\bentered\s+alone\b"
            ],
            "description": "Confined space or high-hazard activity conducted without dedicated, stationed safety attendant.",
            "severity": "CRITICAL",
        },
        {
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "No permit / Confined space procedure failure",
            "patterns": [
                r"\bwithout\s+permit\b",
                r"\bno\s+permit\b",
                r"\bno\s+ptw\b",
                r"\bpermit\s+not\s+issued\b",
                r"\bconfined\s+space\s+procedure\s+failure\b",
                r"\bwithout\s+valid\s+permit\b"
            ],
            "description": "High-risk permit-to-work requirements omitted or bypassed prior to commencement.",
            "severity": "HIGH",
        },
        {
            "hierarchy_level": "PPE",
            "failed_control": "No fall protection",
            "patterns": [
                r"\bwithout\s+(?:proper\s+)?fall\s+protection\b",
                r"\bno\s+fall\s+protection\b",
                r"\bno\s+harness\b",
                r"\bwithout\s+harness\b",
                r"\bharness\s+not\s+tied\s+off\b",
                r"\bno\s+lanyard\b",
                r"\bmissing\s+middle\s+guardrails\b"
            ],
            "description": "Elevated task executed without personal fall arrest system (PFAS) or positive edge protection.",
            "severity": "CRITICAL",
        },
        {
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Energy isolation failure / No LOTO",
            "patterns": [
                r"\bwithout\s+isolat(?:ing|ion)\b",
                r"\bnot\s+isolated\b",
                r"\bwithout\s+isolating\s+the\s+electrical\s+supply\b",
                r"\bno\s+loto\b",
                r"\bno\s+lockout\b",
                r"\bnot\s+de-energiz(?:ed|ation)\b",
                r"\blive\s+maintenance\b",
                r"\bwithout\s+tagout\b"
            ],
            "description": "Failure to achieve and verify verified zero-energy state prior to intrusive maintenance.",
            "severity": "CRITICAL",
        },
        {
            "hierarchy_level": "PPE",
            "failed_control": "No PPE / Inadequate PPE",
            "patterns": [
                r"\bwithout\s+wearing\b",
                r"\bwithout\s+ppe\b",
                r"\bno\s+ppe\b",
                r"\bonly\s+wearing\s+standard\b",
                r"\bwithout\s+insulated\s+tool\b",
                r"\bwithout\s+chemical\s+splash\b",
                r"\bfailed\s+to\s+wear\b",
                r"\bwithout\s+face\s+shield\b",
                r"\bwithout\s+gloves\b"
            ],
            "description": "Required task-specific personal protective equipment omitted or non-compliant with task risk.",
            "severity": "HIGH",
        },
        {
            "hierarchy_level": "ENGINEERING",
            "failed_control": "Guard removed / Safety barrier missing",
            "patterns": [
                r"\bmissing\s+(?:safety\s+)?interlock\b",
                r"\bpanel\s+cover\s+missing\b",
                r"\bguard\s+removed\b",
                r"\bbarrier\s+was\s+not\s+installed\b",
                r"\bno\s+safety\s+barrier\b",
                r"\bdrop-zone\s+barrier\s+was\s+not\s+installed\b",
                r"\bexposed\s+energized\b",
                r"\bunfastened\s+toe-boards\b",
                r"\bmissing\s+shackle\s+safety\s+pin\b"
            ],
            "description": "Physical safeguarding, machine interlock, or drop-zone barricade omitted or bypassed.",
            "severity": "HIGH",
        },
        {
            "hierarchy_level": "ADMINISTRATIVE",
            "failed_control": "Procedure not followed / Procedural shortcut",
            "patterns": [
                r"\bprocedure\s+not\s+followed\b",
                r"\bshortcut\b",
                r"\bwithout\s+removing\s+metal\b",
                r"\bgreen\s+safe-to-use\s+tag\s+was\s+immediately\s+removed\b",
                r"\bunapproved\s+method\b",
                r"\bdeviated\s+from\s+sop\b"
            ],
            "description": "Operational task executed in direct contravention of standard operating procedures.",
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
        cleaned_lower = preprocessed.cleaned_text.lower()
        matched_controls = set()

        for rule in self.CRITICAL_CONTROL_RULES:
            for pattern in rule["patterns"]:
                if re.search(pattern, cleaned_lower):
                    if rule["failed_control"] not in matched_controls:
                        matched_controls.add(rule["failed_control"])
                        failures.append({
                            "hierarchy_level": rule["hierarchy_level"],
                            "failed_control": rule["failed_control"],
                            "description": rule["description"],
                            "severity": rule["severity"],
                        })
                    break

        # If high risk hazard detected without explicit safe condition keywords, check for implied control failure
        is_safe_observation = any(w in cleaned_lower for w in ["wearing required ppe", "approved procedure", "safe condition", "cleaned the area"])
        if not failures and not is_safe_observation:
            for h in hazards:
                cat = h.get("category")
                if cat == "CONFINED_SPACE" and "No atmospheric testing" not in matched_controls:
                    failures.append({
                        "hierarchy_level": "ADMINISTRATIVE",
                        "failed_control": "Possible confined-space procedure failure",
                        "description": "Mandatory confined space pre-entry protocols require verification.",
                        "severity": "HIGH",
                    })
                    break
                elif cat == "WORKING_AT_HEIGHT" and "No fall protection" not in matched_controls:
                    failures.append({
                        "hierarchy_level": "PPE",
                        "failed_control": "Missing Fall Protection Verification",
                        "description": "Elevated maintenance require 100% positive tie-off verification.",
                        "severity": "HIGH",
                    })
                    break
                elif cat == "ELECTRICAL" and "Energy isolation failure / No LOTO" not in matched_controls:
                    failures.append({
                        "hierarchy_level": "ENGINEERING",
                        "failed_control": "Electrical Isolation Verification Required",
                        "description": "Positive zero-energy lock and tag verification required.",
                        "severity": "HIGH",
                    })
                    break

        return ControlFailureResult(
            control_failures=failures,
            is_prototype=False,
        )
