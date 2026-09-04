import math
from typing import Dict, Any, Optional, List
from app.ai.interfaces import BaseSimilarityEngine, PreprocessedText, SimilarityResult


class SimilarityService(BaseSimilarityEngine):
    """
    Semantic feature vectorization and domain embedding calculation.
    Computes dense normalized representation across industrial hazard axes,
    control categories, task types, and energetic precursor vectors for cosine similarity matching.
    """

    VOCABULARY_AXES = [
        # Domain Hazard Concepts (Indices 0-14)
        "confined space tank vessel manhole entry vault silo asphyxiation oxygen gas testing",
        "working at height elevation scaffold scaffolding ladder platform roof drop edge",
        "electrical voltage energized busbar switchgear transformer arc flash shock 6.6kv",
        "lockout tagout loto isolation de-energized zero energy supply isolated valve",
        "chemical caustic acid toxic corrosive splash offloading spill solvent fumes",
        "falling object dropped overhead bracket suspended load crane rigging sling",
        "conveyor roller crush pinch rotating guard machine machinery nip point",
        "fire hot work welding torch sparks flame thermal ignition explosion",
        "vehicle truck forklift mobile equipment loader traffic pedestrian reversing",
        "pressure steam pressurized relief valve hydraulic burst line leak",
        "slip trip wet floor housekeeping puddle spill surface",
        
        # Critical Control Failures (Indices 11-15)
        "without atmospheric testing no gas test untested atmosphere",
        "no standby person without attendant entered alone",
        "without fall protection no harness missing guardrail",
        "without isolating electrical supply live maintenance no loto",
        "missing safety interlock guard removed panel cover missing no barrier",
    ]

    def extract_features(
        self,
        preprocessed: PreprocessedText,
        hazards: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
    ) -> SimilarityResult:
        cleaned_lower = preprocessed.cleaned_text.lower()
        tokens_set = set(preprocessed.tokens)
        matched_tags: List[str] = []

        # Tag extraction
        if any(w in cleaned_lower for w in ["confined", "manhole", "vessel", "tank", "silo", "asphyxiation", "oxygen", "gas testing"]):
            matched_tags.append("CONFINED_SPACE")
        if any(w in cleaned_lower for w in ["height", "elevation", "scaffold", "ladder", "roof", "fall"]):
            matched_tags.append("WORK_AT_HEIGHT")
        if any(w in cleaned_lower for w in ["voltage", "breaker", "electrical", "arc", "switchgear", "6.6kv", "busbar", "energized"]):
            matched_tags.append("ELECTRICAL_SAFETY")
        if any(w in cleaned_lower for w in ["acid", "caustic", "toxic", "chemical", "spill", "leak", "offloading"]):
            matched_tags.append("CHEMICAL_HANDLING")
        if any(w in cleaned_lower for w in ["conveyor", "roller", "crush", "pinch", "rotating", "bracket", "guard"]):
            matched_tags.append("MACHINE_GUARDING")
        if any(w in cleaned_lower for w in ["welding", "weld", "torch", "spark", "steam", "boiler", "hot work"]):
            matched_tags.append("HOT_WORK")
        if any(w in cleaned_lower for w in ["lockout", "tagout", "loto", "isolation", "de-energize", "zero energy"]):
            matched_tags.append("LOTO_ISOLATION")
        if any(w in cleaned_lower for w in ["goggles", "shield", "harness", "gloves", "helmet", "respirator", "ppe"]):
            matched_tags.append("PPE_COMPLIANCE")
        if any(w in cleaned_lower for w in ["overhead", "dropped", "fell", "crane", "rigging", "sling"]):
            matched_tags.append("SUSPENDED_LOAD")

        # Build dense semantic vector (16-dimensional continuous feature vector)
        vector: List[float] = []
        for axis_words in self.VOCABULARY_AXES:
            axis_tokens = axis_words.split()
            score = 0.0
            for tok in axis_tokens:
                if tok in tokens_set or tok in cleaned_lower:
                    score += 1.0
            vector.append(score)

        # Append hazard density & token length normalized features
        vector.append(float(len(hazards)))

        # Normalize vector to unit length (L2 norm) for fast exact cosine distance
        norm = math.sqrt(sum(x * x for x in vector))
        if norm > 0:
            normalized_vector = [round(x / norm, 4) for x in vector]
        else:
            normalized_vector = [0.0] * len(vector)

        return SimilarityResult(
            feature_vector=normalized_vector,
            embedding=normalized_vector,
            similarity_tags=matched_tags,
            is_prototype=False,
        )
