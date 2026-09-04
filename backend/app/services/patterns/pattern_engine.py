import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.department import Department
from app.models.location import Location

logger = logging.getLogger(__name__)


class PatternDetectionEngine:
    """
    Analyzes historical safety reports and their AI analyses across
    hazards, SIF precursors, control failures, locations, and departments.
    Calculates explainable pattern risk scores and trend deltas.
    """

    # Major industrial hazard taxonomy categories
    HAZARD_KEYWORDS = {
        "Confined Space": ["confined", "vessel", "tank", "pit", "manhole", "atmospheric", "gas test", "oxygen", "toxic"],
        "Working at Height": ["height", "scaffold", "ladder", "fall", "harness", "platform", "roof", "guardrail"],
        "Electrical Exposure": ["electrical", "energized", "breaker", "voltage", "cable", "loto", "isolation", "switchgear", "shock", "arc"],
        "Energy Isolation / LOTO": ["loto", "lockout", "tagout", "isolation", "energized", "valve", "pressure"],
        "Machine Guarding": ["guard", "rotating", "pinch", "roller", "conveyor", "moving part", "interlock"],
        "Chemical & Toxic Exposure": ["chemical", "acid", "caustic", "chlorine", "solvent", "spill", "leak", "fume", "toxic"],
        "Fire & Hot Work": ["fire", "hot work", "welding", "grinding", "spark", "flammable", "gas leak"],
        "Vehicle & Mobile Equipment": ["forklift", "crane", "vehicle", "truck", "pedestrian", "traffic", "collision"],
    }

    def __init__(self, current_window_days: int = 30, comparison_window_days: int = 30):
        self.current_window_days = current_window_days
        self.comparison_window_days = comparison_window_days

    def analyze_all_patterns(self, db: Session) -> List[Pattern]:
        """
        Runs comprehensive pattern detection across all dimensions and updates database patterns.
        """
        now = datetime.now(timezone.utc)
        current_cutoff = now - timedelta(days=self.current_window_days)
        previous_cutoff = current_cutoff - timedelta(days=self.comparison_window_days)

        # 1. Fetch all analyzed reports with their AI analyses
        records = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        if not records:
            logger.info("No safety reports found for pattern detection.")
            return []

        # 2. Cluster reports into pattern candidates
        hazard_clusters: Dict[str, List[tuple]] = {}
        sif_clusters: Dict[str, List[tuple]] = {}
        location_clusters: Dict[int, List[tuple]] = {}
        dept_clusters: Dict[int, List[tuple]] = {}

        for report, ai in records:
            rep_date = report.reported_at or report.created_at
            if rep_date and rep_date.tzinfo is None:
                rep_date = rep_date.replace(tzinfo=timezone.utc)

            # Detect hazard category
            text_corpus = f"{report.task} {report.description}".lower()
            if ai and ai.hazards:
                text_corpus += " " + " ".join(str(h) for h in ai.hazards).lower()

            matched_hazards = []
            for haz_name, kws in self.HAZARD_KEYWORDS.items():
                if any(kw in text_corpus for kw in kws):
                    matched_hazards.append(haz_name)

            if not matched_hazards:
                matched_hazards.append("General Safety Hazard")

            for haz in matched_hazards:
                hazard_clusters.setdefault(haz, []).append((report, ai, rep_date))

            # Cluster SIF precursors
            is_sif = False
            sif_cats = []
            if ai:
                is_sif = ai.sif_precursor or ai.sif_detected or (ai.sif_level in ["HIGH", "CRITICAL"])
                if ai.sif_categories:
                    sif_cats = [str(c) for c in ai.sif_categories]

            if is_sif:
                for sc in sif_cats or ["Unspecified SIF Precursor"]:
                    sif_clusters.setdefault(sc, []).append((report, ai, rep_date))

            # Cluster by location
            if report.location_id:
                location_clusters.setdefault(report.location_id, []).append((report, ai, rep_date))

            # Cluster by department
            if report.department_id:
                dept_clusters.setdefault(report.department_id, []).append((report, ai, rep_date))

        persisted_patterns: List[Pattern] = []

        # 3. Build Hazard Recurrence Patterns
        for haz_name, cluster in hazard_clusters.items():
            if len(cluster) >= 2 or any(ai and ai.sif_precursor for _, ai, _ in cluster):
                p = self._build_hazard_pattern(haz_name, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # 4. Build Location Concentration Patterns
        for loc_id, cluster in location_clusters.items():
            high_risk_in_loc = [t for t in cluster if t[1] and (t[1].risk_score >= 50 or t[1].sif_precursor)]
            if len(high_risk_in_loc) >= 2 or len(cluster) >= 3:
                p = self._build_location_pattern(loc_id, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # 5. Build Department Risk Patterns
        for dept_id, cluster in dept_clusters.items():
            sif_in_dept = [t for t in cluster if t[1] and t[1].sif_precursor]
            if len(sif_in_dept) >= 2 or len(cluster) >= 4:
                p = self._build_department_pattern(dept_id, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        db.commit()
        return persisted_patterns

    def _build_hazard_pattern(
        self,
        haz_name: str,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        pattern_key = f"PAT_HAZ_{haz_name.upper().replace(' ', '_').replace('/', '_')}"
        title = f"Recurring Hazard Pattern: {haz_name}"

        # Analyze locations and departments involved
        loc_counts: Dict[int, int] = {}
        dept_counts: Dict[int, int] = {}
        for r, _, _ in cluster:
            if r.location_id:
                loc_counts[r.location_id] = loc_counts.get(r.location_id, 0) + 1
            if r.department_id:
                dept_counts[r.department_id] = dept_counts.get(r.department_id, 0) + 1

        top_loc_id = max(loc_counts, key=loc_counts.get) if loc_counts else None
        top_dept_id = max(dept_counts, key=dept_counts.get) if dept_counts else None

        # Calculate frequency and trend
        current_period_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_period_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        
        trend_pct = 0.0
        if prev_period_count > 0:
            trend_pct = round(((current_period_count - prev_period_count) / prev_period_count) * 100.0, 1)
        elif current_period_count > 0:
            trend_pct = 100.0

        # SIF count
        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected))

        # Explainable factor weights
        scoring_factors = {}
        # 1. Base Frequency Score (up to 30)
        freq_pts = min(len(cluster) * 6, 30)
        scoring_factors["frequency_factor"] = freq_pts

        # 2. SIF Precursor Contribution (up to 35)
        sif_pts = min(sif_count * 15, 35)
        scoring_factors["sif_precursor_factor"] = sif_pts

        # 3. Control Failure Recurrence (up to 20)
        cf_count = sum(len(ai.control_failures) for _, ai, _ in cluster if ai and ai.control_failures)
        cf_pts = min(cf_count * 5, 20)
        scoring_factors["control_failure_factor"] = cf_pts

        # 4. Trend Increase (up to 15)
        trend_pts = 15 if trend_pct >= 25 else (10 if trend_pct > 0 else 0)
        scoring_factors["trend_increase_factor"] = trend_pts

        raw_score = sum(scoring_factors.values())
        risk_score = float(min(max(raw_score, 10.0), 100.0))

        # Severity
        if risk_score >= 70:
            risk_level = "CRITICAL"
        elif risk_score >= 50:
            risk_level = "HIGH"
        elif risk_score >= 30:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Synthesize recommendations
        recs = self._synthesize_recommendations(haz_name, cluster)

        report_ids = [r.id for r, _, _ in cluster]
        case_ids = [r.case_id for r, _, _ in cluster]
        dates = [dt for _, _, dt in cluster if dt]
        first_dt = min(dates) if dates else datetime.now(timezone.utc)
        last_dt = max(dates) if dates else datetime.now(timezone.utc)

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="HAZARD_RECURRENCE",
            hazard_category=haz_name,
            sif_category="SIF Precursor" if sif_count > 0 else None,
            department_id=top_dept_id,
            location_id=top_loc_id,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            trend_percentage=trend_pct,
            scoring_factors=scoring_factors,
            evidence_report_ids=report_ids,
            evidence_case_ids=case_ids,
            recommendations=recs,
            first_dt=first_dt,
            last_dt=last_dt,
            db=db,
        )

    def _build_location_pattern(
        self,
        loc_id: int,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        loc = db.query(Location).filter(Location.id == loc_id).first()
        loc_name = loc.name if loc else f"Location #{loc_id}"
        pattern_key = f"PAT_LOC_{loc_id}"
        title = f"High Risk Concentration in {loc_name}"

        # Dominant hazard in this location
        haz_counts: Dict[str, int] = {}
        for r, ai, _ in cluster:
            text_corpus = f"{r.task} {r.description}".lower()
            for haz_name, kws in self.HAZARD_KEYWORDS.items():
                if any(kw in text_corpus for kw in kws):
                    haz_counts[haz_name] = haz_counts.get(haz_name, 0) + 1

        top_haz = max(haz_counts, key=haz_counts.get) if haz_counts else "Operational Hazards"

        current_period_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_period_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        
        trend_pct = 0.0
        if prev_period_count > 0:
            trend_pct = round(((current_period_count - prev_period_count) / prev_period_count) * 100.0, 1)
        elif current_period_count > 0:
            trend_pct = 100.0

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected))
        avg_ai_risk = sum(ai.risk_score for _, ai, _ in cluster if ai) / max(len(cluster), 1)

        scoring_factors = {
            "location_density_factor": min(len(cluster) * 7, 30),
            "sif_concentration_factor": min(sif_count * 15, 35),
            "average_risk_weight": round(min(avg_ai_risk * 0.25, 25), 1),
            "trend_factor": 10 if trend_pct > 0 else 0,
        }

        risk_score = float(min(max(sum(scoring_factors.values()), 15.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Conduct targeted plant safety stand-down and risk audit across {loc_name}.",
            f"Mandate supervisory pre-task verification for all {top_haz.lower()} tasks in {loc_name}.",
            f"Review critical control verifications and barrier compliance in {loc_name}.",
        ]

        report_ids = [r.id for r, _, _ in cluster]
        case_ids = [r.case_id for r, _, _ in cluster]
        dates = [dt for _, _, dt in cluster if dt]
        first_dt = min(dates) if dates else datetime.now(timezone.utc)
        last_dt = max(dates) if dates else datetime.now(timezone.utc)

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="LOCATION_CONCENTRATION",
            hazard_category=top_haz,
            sif_category="SIF Precursor" if sif_count > 0 else None,
            department_id=cluster[0][0].department_id if cluster else None,
            location_id=loc_id,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            trend_percentage=trend_pct,
            scoring_factors=scoring_factors,
            evidence_report_ids=report_ids,
            evidence_case_ids=case_ids,
            recommendations=recs,
            first_dt=first_dt,
            last_dt=last_dt,
            db=db,
        )

    def _build_department_pattern(
        self,
        dept_id: int,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        dept = db.query(Department).filter(Department.id == dept_id).first()
        dept_name = dept.name if dept else f"Department #{dept_id}"
        pattern_key = f"PAT_DEPT_{dept_id}"
        title = f"High SIF Precursor Rate in {dept_name} Department"

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected))
        scoring_factors = {
            "department_volume_factor": min(len(cluster) * 5, 25),
            "sif_volume_factor": min(sif_count * 18, 45),
            "control_failure_rate": min(sum(len(ai.control_failures) for _, ai, _ in cluster if ai and ai.control_failures) * 4, 20),
            "severity_factor": 10,
        }

        risk_score = float(min(max(sum(scoring_factors.values()), 20.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Review department standard operating procedures (SOPs) for high-energy maintenance in {dept_name}.",
            f"Implement refresher training on critical lifesaving controls for all {dept_name} personnel.",
            f"Require supervisory sign-off on permits to work across {dept_name} operations.",
        ]

        report_ids = [r.id for r, _, _ in cluster]
        case_ids = [r.case_id for r, _, _ in cluster]
        dates = [dt for _, _, dt in cluster if dt]
        first_dt = min(dates) if dates else datetime.now(timezone.utc)
        last_dt = max(dates) if dates else datetime.now(timezone.utc)

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="DEPARTMENT_RISK",
            hazard_category=None,
            sif_category="SIF Precursor" if sif_count > 0 else None,
            department_id=dept_id,
            location_id=None,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            trend_percentage=25.0,
            scoring_factors=scoring_factors,
            evidence_report_ids=report_ids,
            evidence_case_ids=case_ids,
            recommendations=recs,
            first_dt=first_dt,
            last_dt=last_dt,
            db=db,
        )

    def _synthesize_recommendations(self, haz_name: str, cluster: List[tuple]) -> List[str]:
        """
        Combines individual report-level recommendations into synthesized pattern-level actions.
        """
        collected_recs = []
        for _, ai, _ in cluster:
            if ai and ai.recommendations:
                for r in ai.recommendations:
                    txt = r if isinstance(r, str) else r.get("recommendation", "")
                    if txt and txt not in collected_recs:
                        collected_recs.append(txt)

        if haz_name == "Confined Space":
            return [
                "Implement mandatory confined-space entry verification, including atmospheric gas testing before every entry.",
                "Enforce strict standby-person deployment and verify emergency rescue retrieval equipment on-site.",
                "Ensure continuous atmospheric monitoring and positive ventilation throughout the work duration.",
            ]
        elif haz_name == "Electrical Exposure" or haz_name == "Energy Isolation / LOTO":
            return [
                "Mandate zero-energy state verification (test-before-touch) and Lockout/Tagout (LOTO) padlocking prior to work.",
                "Provide certified arc flash PPE and insulated tools for all high voltage maintenance operations.",
                "Enforce secondary supervisor verification before racking out or performing breaker maintenance.",
            ]
        elif haz_name == "Working at Height":
            return [
                "Mandate 100% tie-off with certified safety harnesses and dual shock-absorbing lanyards for work > 1.8 meters.",
                "Perform daily scaffolding, platform, and guardrail pre-use safety inspections.",
                "Install certified anchor points and engineered lifelines in high-risk plant zones.",
            ]
        elif haz_name == "Machine Guarding":
            return [
                "Enforce zero-tolerance policy against operating or clearing machinery with guards removed.",
                "Install interlocking safety switches that immediately de-energize equipment upon guard removal.",
                "Establish strict stop-and-isolate protocols prior to clearing material jams.",
            ]

        # General synthesis
        return collected_recs[:3] if collected_recs else [
            f"Review task risk assessments and job safety analyses (JSA) for {haz_name}.",
            "Reinforce critical control adherence and supervisor presence during high-risk tasks.",
            "Conduct safety toolbox talks highlighting recent hazard patterns.",
        ]

    def _upsert_pattern(
        self,
        pattern_key: str,
        title: str,
        pattern_type: str,
        hazard_category: Optional[str],
        sif_category: Optional[str],
        department_id: Optional[int],
        location_id: Optional[int],
        risk_score: float,
        risk_level: str,
        frequency_count: int,
        sif_count: int,
        trend_percentage: float,
        scoring_factors: dict,
        evidence_report_ids: list,
        evidence_case_ids: list,
        recommendations: list,
        first_dt: datetime,
        last_dt: datetime,
        db: Session,
    ) -> Pattern:
        existing = db.query(Pattern).filter(Pattern.pattern_key == pattern_key).first()
        if existing:
            existing.title = title
            existing.hazard_category = hazard_category
            existing.sif_category = sif_category
            existing.department_id = department_id
            existing.location_id = location_id
            existing.risk_score = risk_score
            existing.risk_level = risk_level
            existing.frequency_count = frequency_count
            existing.sif_count = sif_count
            existing.trend_percentage = trend_percentage
            existing.scoring_factors = scoring_factors
            existing.evidence_report_ids = evidence_report_ids
            existing.evidence_case_ids = evidence_case_ids
            existing.recommendations = recommendations
            existing.last_detected_at = last_dt
            existing.status = "ACTIVE"
            db.add(existing)
            return existing
        else:
            new_pattern = Pattern(
                pattern_key=pattern_key,
                title=title,
                pattern_type=pattern_type,
                hazard_category=hazard_category,
                sif_category=sif_category,
                department_id=department_id,
                location_id=location_id,
                risk_score=risk_score,
                risk_level=risk_level,
                frequency_count=frequency_count,
                sif_count=sif_count,
                trend_percentage=trend_percentage,
                scoring_factors=scoring_factors,
                evidence_report_ids=evidence_report_ids,
                evidence_case_ids=evidence_case_ids,
                recommendations=recommendations,
                first_detected_at=first_dt,
                last_detected_at=last_dt,
                status="ACTIVE",
            )
            db.add(new_pattern)
            return new_pattern


pattern_engine = PatternDetectionEngine()
