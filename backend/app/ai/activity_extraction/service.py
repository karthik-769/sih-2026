import re
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseActivityExtractor, PreprocessedText, ActivityExtractionResult


class ActivityExtractionService(BaseActivityExtractor):
    """
    NLP Activity & Task Extraction Engine for OIL Safety Reports.
    Identifies operational activities and work categories from narrative text and task context.
    """

    ACTIVITY_ONTOLOGY = [
        {
            "activity": "Confined Space Entry",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bconfined\s+space(?:\s+entry)?\b", r"\bvessel\s+entry\b", r"\btank\s+entry\b",
                r"\bmanhole\s+entry\b", r"\bseparator\s+entry\b", r"\bcolumn\s+entry\b", r"\bentered\s+(?:the\s+)?vessel\b"
            ],
            "confidence": 0.95,
        },
        {
            "activity": "Vessel Cleaning",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bvessel\s+cleaning\b", r"\btank\s+cleaning\b", r"\bcleaning\s+(?:the\s+)?vessel\b",
                r"\bsludge\s+removal\b", r"\btank\s+washing\b", r"\bvessel\s+de-sludging\b"
            ],
            "confidence": 0.92,
        },
        {
            "activity": "Pump Maintenance",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bpump\s+(?:maintenance|repair|overhaul|servicing|inspection)\b",
                r"\bcrude\s+oil\s+pump\b", r"\bfeed\s+pump\b", r"\bcentrifugal\s+pump\b",
                r"\bpump\s+impeller\b", r"\bpump\s+bearing\b", r"\bpump\s+seal\b"
            ],
            "confidence": 0.94,
        },
        {
            "activity": "Electrical Maintenance",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\belectrical\s+(?:maintenance|repair|work|wiring|inspection)\b",
                r"\belectrician\b", r"\bswitchgear\b", r"\bpanel\s+wiring\b",
                r"\bbusbar\b", r"\bmcc\s+panel\b", r"\btransformer\s+maintenance\b",
                r"\bcircuit\s+breaker\b", r"\belectrical\s+panel\b"
            ],
            "confidence": 0.93,
        },
        {
            "activity": "Well Intervention",
            "category": "Well & Drilling Operations",
            "patterns": [
                r"\bwell\s+intervention\b", r"\bwellhead\b", r"\bwireline\b", r"\bcoiled\s+tubing\b",
                r"\bxmas\s+tree\b", r"\bchristmas\s+tree\b", r"\bwell\s+servicing\b", r"\bwell\s+workover\b",
                r"\bdrilling\s+rig\b", r"\bwell\s+head\b"
            ],
            "confidence": 0.92,
        },
        {
            "activity": "Hot Work",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bhot\s+work\b", r"\bwelding\b", r"\bcutting\s+torch\b", r"\bgrinding\b",
                r"\bgas\s+cutting\b", r"\bbrazing\b", r"\bopen\s+flame\b", r"\bwelder\b"
            ],
            "confidence": 0.93,
        },
        {
            "activity": "Pipeline Maintenance",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bpipeline\s+(?:maintenance|repair|inspection|pigging|laying)\b",
                r"\bflowline\b", r"\btrunkline\b", r"\bpig\s+launcher\b", r"\bpig\s+receiver\b",
                r"\bpipe\s+section\b", r"\bflange\s+replacement\b"
            ],
            "confidence": 0.91,
        },
        {
            "activity": "Valve Maintenance",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bvalve\s+(?:maintenance|repair|replacement|greasing|testing|servicing)\b",
                r"\bcontrol\s+valve\b", r"\besdv\b", r"\bmov\b", r"\bgate\s+valve\b", r"\bball\s+valve\b",
                r"\bpressure\s+relief\s+valve\b"
            ],
            "confidence": 0.90,
        },
        {
            "activity": "Lifting Operation",
            "category": "Logistics & Transport",
            "patterns": [
                r"\blifting\s+operation\b", r"\bcrane\s+(?:operation|lift|movement)\b",
                r"\bsuspended\s+load\b", r"\brigger\b", r"\brigging\b", r"\bhoisting\b",
                r"\bhydra\s+crane\b", r"\bwebbing\s+sling\b", r"\bchain\s+pulley\b"
            ],
            "confidence": 0.94,
        },
        {
            "activity": "Loading / Unloading",
            "category": "Logistics & Transport",
            "patterns": [
                r"\bloading\b", r"\bunloading\b", r"\btanker\s+loading\b", r"\btanker\s+decanting\b",
                r"\bchemical\s+unloading\b", r"\bcrude\s+dispatch\b", r"\bgantry\b", r"\bbulk\s+transfer\b"
            ],
            "confidence": 0.91,
        },
        {
            "activity": "Vehicle Movement",
            "category": "Logistics & Transport",
            "patterns": [
                r"\bvehicle\s+movement\b", r"\bdriving\b", r"\bforklift\b", r"\btruck\s+movement\b",
                r"\bbowser\b", r"\btrailer\b", r"\blight\s+motor\s+vehicle\b", r"\breversing\s+vehicle\b",
                r"\bspeeding\b", r"\btransportation\b"
            ],
            "confidence": 0.90,
        },
        {
            "activity": "Excavation",
            "category": "Civil & Construction",
            "patterns": [
                r"\bexcavation\b", r"\btrenching\b", r"\btrench\b", r"\bdigging\b",
                r"\bjcb\b", r"\bearth\s+moving\b", r"\bshoring\b", r"\bpits\s+digging\b"
            ],
            "confidence": 0.92,
        },
        {
            "activity": "Inspection & Monitoring",
            "category": "Process Operations",
            "patterns": [
                r"\binspection\b", r"\bmonitoring\b", r"\bpatrolling\b", r"\bgauge\s+reading\b",
                r"\broutine\s+check\b", r"\boperator\s+round\b", r"\bvisual\s+inspection\b",
                r"\but\s+gauging\b", r"\bndt\s+inspection\b"
            ],
            "confidence": 0.88,
        },
        {
            "activity": "Equipment Maintenance",
            "category": "Maintenance & Integrity",
            "patterns": [
                r"\bequipment\s+maintenance\b", r"\bpreventive\s+maintenance\b", r"\bbreakdown\s+maintenance\b",
                r"\bcompressor\s+overhaul\b", r"\bgenerator\s+servicing\b", r"\bmachine\s+repair\b"
            ],
            "confidence": 0.87,
        },
    ]

    def extract_activity(
        self,
        preprocessed: PreprocessedText,
        context: Optional[Dict[str, Any]] = None,
    ) -> ActivityExtractionResult:
        context = context or {}
        declared_task = str(context.get("task") or "").strip()
        declared_activity = str(context.get("activity") or "").strip()
        
        cleaned_lower = preprocessed.cleaned_text.lower()
        search_corpus = f"{declared_activity} {declared_task} {cleaned_lower}".strip()

        evidence: List[str] = []
        
        # Check against ontology
        for item in self.ACTIVITY_ONTOLOGY:
            for pattern in item["patterns"]:
                match = re.search(pattern, search_corpus, re.IGNORECASE)
                if match:
                    evidence.append(match.group(0))
                    return ActivityExtractionResult(
                        activity=item["activity"],
                        activity_category=item["category"],
                        confidence=item["confidence"],
                        evidence=evidence,
                        is_prototype=False,
                    )

        # Fallback to declared task if meaningful
        if declared_task and len(declared_task) >= 3 and declared_task.lower() not in ["routine", "general", "work", "n/a", "none"]:
            return ActivityExtractionResult(
                activity=declared_task.title(),
                activity_category="General Operations",
                confidence=0.75,
                evidence=[declared_task],
                is_prototype=False,
            )

        return ActivityExtractionResult(
            activity="General Plant Operations",
            activity_category="Process Operations",
            confidence=0.60,
            evidence=["Routine operational observation"],
            is_prototype=False,
        )
