import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.department import Department
from app.models.location import Location

logger = logging.getLogger(__name__)


class PatternDetectionEngine:
    """
    Analyzes historical safety reports and their AI analyses across
    hazards, SIF precursors, control/barrier failures, activities, Life-Saving Rules,
    locations, and departments. Detects multi-dimensional recurring patterns and emerging risks.
    """

    HAZARD_KEYWORDS = {
        "Confined Space": ["confined", "vessel", "tank", "pit", "manhole", "atmospheric", "gas test", "oxygen", "toxic"],
        "Working at Height": ["height", "scaffold", "ladder", "fall", "harness", "platform", "roof", "guardrail"],
        "Electrical Exposure": ["electrical", "energized", "breaker", "voltage", "cable", "loto", "isolation", "switchgear", "shock", "arc"],
        "Energy Isolation / LOTO": ["loto", "lockout", "tagout", "isolation", "energized", "valve", "zero energy"],
        "Machine Guarding": ["guard", "rotating", "pinch", "roller", "conveyor", "moving part", "interlock"],
        "Chemical & Toxic Exposure": ["chemical", "acid", "caustic", "chlorine", "solvent", "spill", "leak", "fume", "toxic", "h2s"],
        "Fire & Hot Work": ["fire", "hot work", "welding", "grinding", "spark", "flammable", "gas leak"],
        "Vehicle & Mobile Equipment": ["forklift", "crane", "vehicle", "truck", "pedestrian", "traffic", "collision", "bowser"],
        "Pressure Systems": ["pressure", "pressurized", "steam", "relief valve", "flange", "hydraulic"],
        "Lifting & Dropped Objects": ["lifting", "crane", "suspended load", "dropped object", "rigging", "shackle"],
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

        records = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        if not records:
            logger.info("No safety reports found for pattern detection.")
            return []

        # Clusters across dimensions
        hazard_clusters: Dict[str, List[tuple]] = {}
        sif_clusters: Dict[str, List[tuple]] = {}
        location_clusters: Dict[int, List[tuple]] = {}
        dept_clusters: Dict[int, List[tuple]] = {}
        activity_clusters: Dict[str, List[tuple]] = {}
        barrier_clusters: Dict[str, List[tuple]] = {}
        lsr_clusters: Dict[str, List[tuple]] = {}
        combined_clusters: Dict[str, List[tuple]] = {}

        for report, ai in records:
            rep_date = report.reported_at or report.created_at
            if rep_date and rep_date.tzinfo is None:
                rep_date = rep_date.replace(tzinfo=timezone.utc)

            text_corpus = f"{report.task} {report.description}".lower()
            if ai and ai.hazards:
                text_corpus += " " + " ".join(str(h) for h in ai.hazards).lower()

            # 1. Hazard matching
            matched_hazards = []
            for haz_name, kws in self.HAZARD_KEYWORDS.items():
                if any(kw in text_corpus for kw in kws):
                    matched_hazards.append(haz_name)
            if not matched_hazards:
                matched_hazards.append("General Safety Hazard")

            for haz in matched_hazards:
                hazard_clusters.setdefault(haz, []).append((report, ai, rep_date))

            # 2. SIF matching
            is_sif = False
            sif_cats = []
            if ai:
                is_sif = ai.sif_precursor or ai.sif_detected or (ai.sif_level in ["HIGH", "CRITICAL"])
                if ai.sif_categories:
                    sif_cats = [str(c) for c in ai.sif_categories]

            if is_sif:
                for sc in sif_cats or ["Unspecified SIF Precursor"]:
                    sif_clusters.setdefault(sc, []).append((report, ai, rep_date))

            # 3. Location & Department
            if report.location_id:
                location_clusters.setdefault(report.location_id, []).append((report, ai, rep_date))
            if report.department_id:
                dept_clusters.setdefault(report.department_id, []).append((report, ai, rep_date))

            # 4. Activity
            act_name = (ai.activity if ai and ai.activity else report.activity) or report.task or "General Operations"
            activity_clusters.setdefault(act_name, []).append((report, ai, rep_date))

            # 5. Barrier failures
            if ai and ai.failed_barriers:
                for fb in ai.failed_barriers:
                    bname = fb.get("barrier_name", "Barrier")
                    barrier_clusters.setdefault(bname, []).append((report, ai, rep_date))

            # 6. Life-Saving Rule
            lsr_name = (ai.life_saving_rule if ai and ai.life_saving_rule else report.life_saving_rule)
            if lsr_name:
                lsr_clusters.setdefault(lsr_name, []).append((report, ai, rep_date))

            # 7. Combined Multi-dimensional Pattern (Activity + Location + LSR + SIF)
            if is_sif and lsr_name and report.location_id:
                comb_key = f"{act_name}|{report.location_id}|{lsr_name}"
                combined_clusters.setdefault(comb_key, []).append((report, ai, rep_date))

        persisted_patterns: List[Pattern] = []

        # Build Hazard Patterns
        for haz_name, cluster in hazard_clusters.items():
            if len(cluster) >= 2 or any(ai and ai.sif_precursor for _, ai, _ in cluster):
                p = self._build_hazard_pattern(haz_name, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Location Patterns
        for loc_id, cluster in location_clusters.items():
            high_risk_in_loc = [t for t in cluster if t[1] and (t[1].risk_score >= 50 or t[1].sif_precursor)]
            if len(high_risk_in_loc) >= 2 or len(cluster) >= 3:
                p = self._build_location_pattern(loc_id, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Department Patterns
        for dept_id, cluster in dept_clusters.items():
            sif_in_dept = [t for t in cluster if t[1] and t[1].sif_precursor]
            if len(sif_in_dept) >= 2 or len(cluster) >= 4:
                p = self._build_department_pattern(dept_id, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Activity Patterns
        for act_name, cluster in activity_clusters.items():
            sif_in_act = [t for t in cluster if t[1] and (t[1].sif_precursor or t[1].sif_level in ["HIGH", "CRITICAL"])]
            if len(sif_in_act) >= 2 or len(cluster) >= 4:
                p = self._build_activity_pattern(act_name, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Barrier Failure Patterns
        for bname, cluster in barrier_clusters.items():
            if len(cluster) >= 2:
                p = self._build_barrier_pattern(bname, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Life-Saving Rule Patterns
        for lsr_name, cluster in lsr_clusters.items():
            sif_in_lsr = [t for t in cluster if t[1] and t[1].sif_precursor]
            if len(sif_in_lsr) >= 2 or len(cluster) >= 3:
                p = self._build_lsr_pattern(lsr_name, cluster, current_cutoff, previous_cutoff, db)
                if p:
                    persisted_patterns.append(p)

        # Build Combined Multi-Dimensional Patterns
        for comb_key, cluster in combined_clusters.items():
            if len(cluster) >= 2:
                p = self._build_combined_pattern(comb_key, cluster, current_cutoff, previous_cutoff, db)
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
        clean_key = haz_name.upper().replace(' ', '_').replace('/', '_').replace('&', '_')
        pattern_key = f"PAT_HAZ_{clean_key}"
        title = f"Recurring Hazard Pattern: {haz_name}"

        loc_counts: Dict[int, int] = {}
        dept_counts: Dict[int, int] = {}
        for r, _, _ in cluster:
            if r.location_id:
                loc_counts[r.location_id] = loc_counts.get(r.location_id, 0) + 1
            if r.department_id:
                dept_counts[r.department_id] = dept_counts.get(r.department_id, 0) + 1

        top_loc_id = max(loc_counts, key=loc_counts.get) if loc_counts else None
        top_dept_id = max(dept_counts, key=dept_counts.get) if dept_counts else None

        current_period_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_period_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        
        trend_pct = round(((current_period_count - prev_period_count) / max(prev_period_count, 1)) * 100.0, 1) if prev_period_count > 0 else (100.0 if current_period_count > 0 else 0.0)
        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)

        scoring_factors = {
            "frequency_factor": min(len(cluster) * 5, 30),
            "sif_precursor_factor": min(sif_count * 12, 35),
            "trend_factor": 15 if trend_pct >= 20 else (8 if trend_pct > 0 else 0),
            "density_factor": min(int(sif_density * 0.2), 20),
        }
        risk_score = float(min(max(sum(scoring_factors.values()), 15.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = self._synthesize_recommendations(haz_name, cluster)
        report_ids = [r.id for r, _, _ in cluster]
        case_ids = [r.case_id for r, _, _ in cluster]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="HAZARD_RECURRENCE",
            hazard_category=haz_name,
            sif_category="SIF Precursor" if sif_count > 0 else None,
            activity=None,
            life_saving_rule=None,
            failed_barriers=[],
            department_id=top_dept_id,
            location_id=top_loc_id,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors=scoring_factors,
            evidence_report_ids=report_ids,
            evidence_case_ids=case_ids,
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
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

        haz_counts: Dict[str, int] = {}
        for r, ai, _ in cluster:
            text = f"{r.task} {r.description}".lower()
            for haz_name, kws in self.HAZARD_KEYWORDS.items():
                if any(kw in text for kw in kws):
                    haz_counts[haz_name] = haz_counts.get(haz_name, 0) + 1
        top_haz = max(haz_counts, key=haz_counts.get) if haz_counts else "Operational Hazards"

        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else (100.0 if cur_count > 0 else 0.0)

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)

        scoring_factors = {
            "location_concentration_factor": min(len(cluster) * 6, 30),
            "sif_factor": min(sif_count * 15, 35),
            "trend_factor": 15 if trend_pct >= 25 else 0,
            "density_factor": min(int(sif_density * 0.2), 20),
        }
        risk_score = float(min(max(sum(scoring_factors.values()), 20.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Conduct targeted safety integrity audit at {loc_name}.",
            f"Review control implementation for {top_haz} at {loc_name}.",
            "Reinforce supervisory oversight and toolbox talk verification.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="LOCATION_CONCENTRATION",
            hazard_category=top_haz,
            sif_category="Location Precursor Spike" if sif_count > 0 else None,
            activity=None,
            life_saving_rule=None,
            failed_barriers=[],
            department_id=None,
            location_id=loc_id,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors=scoring_factors,
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
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
        title = f"Department Safety Risk: {dept_name}"

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)
        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else 0.0

        risk_score = float(min(max(len(cluster) * 5 + sif_count * 10 + (15 if trend_pct > 0 else 0), 20.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Hold departmental HSE stand-down meeting for {dept_name}.",
            "Review task-specific standard operating procedures and risk assessments.",
            "Verify personal protective equipment and tool inspection compliance.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="DEPARTMENT_RISK",
            hazard_category=None,
            sif_category="Department SIF Risk" if sif_count > 0 else None,
            activity=None,
            life_saving_rule=None,
            failed_barriers=[],
            department_id=dept_id,
            location_id=None,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors={"department_reports": len(cluster), "sif_precursors": sif_count},
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
            db=db,
        )

    def _build_activity_pattern(
        self,
        act_name: str,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        clean_key = act_name.upper().replace(' ', '_').replace('/', '_')
        pattern_key = f"PAT_ACT_{clean_key}"
        title = f"Recurring SIF Risk in Activity: {act_name}"

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)

        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else (100.0 if cur_count > 0 else 0.0)

        risk_score = float(min(max(len(cluster) * 4 + sif_count * 12 + (15 if trend_pct > 15 else 0), 25.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Review standard operating procedures specifically for '{act_name}'.",
            "Mandate pre-job safety analysis (JSA) checklist before task execution.",
            "Verify all critical barrier verifications before commencing work.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="ACTIVITY_RECURRENCE",
            hazard_category=None,
            sif_category="Activity SIF Risk",
            activity=act_name,
            life_saving_rule=None,
            failed_barriers=[],
            department_id=None,
            location_id=None,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors={"activity_volume": len(cluster), "sif_precursors": sif_count, "density": sif_density},
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
            db=db,
        )

    def _build_barrier_pattern(
        self,
        bname: str,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        clean_key = bname.upper().replace(' ', '_').replace('/', '_')
        pattern_key = f"PAT_BAR_{clean_key}"
        title = f"Recurring Control Failure: {bname}"

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)

        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else (100.0 if cur_count > 0 else 0.0)

        risk_score = float(min(max(len(cluster) * 6 + sif_count * 14 + (15 if trend_pct > 10 else 0), 30.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Conduct rigorous verification audit on barrier: {bname}.",
            "Reinforce isolation/testing verification protocol with frontline crew.",
            "Verify physical equipment integrity and calibration logs.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="CONTROL_FAILURE",
            hazard_category=None,
            sif_category="Barrier Failure Recurrence",
            activity=None,
            life_saving_rule=None,
            failed_barriers=[bname],
            department_id=None,
            location_id=None,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors={"barrier_failures": len(cluster), "sif_precursors": sif_count},
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
            db=db,
        )

    def _build_lsr_pattern(
        self,
        lsr_name: str,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        clean_key = lsr_name.upper().replace(' ', '_').replace('/', '_')
        pattern_key = f"PAT_LSR_{clean_key}"
        title = f"Life-Saving Rule Risk: {lsr_name}"

        sif_count = sum(1 for _, ai, _ in cluster if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        sif_density = round((sif_count / max(len(cluster), 1)) * 100.0, 1)

        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else (100.0 if cur_count > 0 else 0.0)

        risk_score = float(min(max(len(cluster) * 5 + sif_count * 12 + (15 if trend_pct > 15 else 0), 30.0), 100.0))
        risk_level = "CRITICAL" if risk_score >= 70 else ("HIGH" if risk_score >= 50 else ("MEDIUM" if risk_score >= 30 else "LOW"))

        recs = [
            f"Launch focused campaign on IOGP Life-Saving Rule: '{lsr_name}'.",
            "Mandate stop-work authority briefing whenever controls for this rule are absent.",
            "Conduct peer verification audits across active work permits.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="LIFE_SAVING_RULE",
            hazard_category=None,
            sif_category="Life-Saving Rule Precursor",
            activity=None,
            life_saving_rule=lsr_name,
            failed_barriers=[],
            department_id=None,
            location_id=None,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors={"lsr_incidents": len(cluster), "sif_precursors": sif_count},
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
            db=db,
        )

    def _build_combined_pattern(
        self,
        comb_key: str,
        cluster: List[tuple],
        current_cutoff: datetime,
        previous_cutoff: datetime,
        db: Session,
    ) -> Optional[Pattern]:
        parts = comb_key.split("|")
        act_name = parts[0]
        loc_id = int(parts[1])
        lsr_name = parts[2]

        loc = db.query(Location).filter(Location.id == loc_id).first()
        loc_name = loc.name if loc else f"Site #{loc_id}"

        clean_key = f"{act_name}_{loc_id}_{lsr_name}".upper().replace(' ', '_').replace('/', '_')
        pattern_key = f"PAT_COMB_{clean_key}"
        title = f"Critical Combined Risk: {act_name} at {loc_name} ({lsr_name})"

        sif_count = len(cluster)
        sif_density = 100.0

        cur_count = sum(1 for _, _, dt in cluster if dt and dt >= current_cutoff)
        prev_count = sum(1 for _, _, dt in cluster if dt and previous_cutoff <= dt < current_cutoff)
        trend_pct = round(((cur_count - prev_count) / max(prev_count, 1)) * 100.0, 1) if prev_count > 0 else (100.0 if cur_count > 0 else 0.0)

        risk_score = 88.0  # High priority multi-dimensional pattern
        risk_level = "CRITICAL"

        recs = [
            f"Immediate executive safety intervention for {act_name} operations at {loc_name}.",
            f"Perform comprehensive verification of {lsr_name} controls before next shift.",
            "Deploy specialized HSE officer to oversee work permit issuance.",
        ]
        dates = [dt for _, _, dt in cluster if dt]

        return self._upsert_pattern(
            pattern_key=pattern_key,
            title=title,
            pattern_type="COMBINED_RISK",
            hazard_category=None,
            sif_category="Multi-Dimensional SIF Cluster",
            activity=act_name,
            life_saving_rule=lsr_name,
            failed_barriers=[],
            department_id=None,
            location_id=loc_id,
            risk_score=risk_score,
            risk_level=risk_level,
            frequency_count=len(cluster),
            sif_count=sif_count,
            sif_density=sif_density,
            trend_percentage=trend_pct,
            scoring_factors={"combined_dimensions": 4, "sif_precursors": sif_count, "density": 100.0},
            evidence_report_ids=[r.id for r, _, _ in cluster],
            evidence_case_ids=[r.case_id for r, _, _ in cluster],
            recommendations=recs,
            first_dt=min(dates) if dates else datetime.now(timezone.utc),
            last_dt=max(dates) if dates else datetime.now(timezone.utc),
            db=db,
        )

    def _synthesize_recommendations(self, haz_name: str, cluster: List[tuple]) -> List[str]:
        if "Confined" in haz_name:
            return [
                "Enforce mandatory multi-gas testing at top, middle, and bottom before vessel entry.",
                "Verify continuous presence of certified hole-watch / standby person.",
                "Review confined space permit-to-work checklist with all shifts.",
            ]
        elif "Height" in haz_name:
            return [
                "Mandate 100% positive fall arrest tie-off with certified double lanyards.",
                "Install standard top/mid guardrails and secure toe-boards on all platforms.",
                "Ensure scaffolding is inspected daily and tagged with Scafftag.",
            ]
        elif "Electrical" in haz_name or "Energy" in haz_name:
            return [
                "Enforce strict Lockout/Tagout (LOTO) and zero-energy physical multimeter verification.",
                "Ensure arc-flash PPE and insulated tool kits are utilized for switchgear interventions.",
                "Conduct refresher training on electrical safety isolation protocols.",
            ]
        elif "Machine" in haz_name:
            return [
                "Re-fit physical machine guards and interlocks on all rotating conveyor equipment.",
                "Verify emergency stop pull-cords along conveyor perimeters.",
            ]
        elif "Chemical" in haz_name:
            return [
                "Mandate chemical splash suits, face shields, and heavy-duty nitrile gloves.",
                "Verify emergency eyewash and deluge shower operational readiness.",
            ]
        return [
            "Perform immediate task risk assessment and pre-shift toolbox talk.",
            "Verify all required physical barriers and PPE safeguards before resuming work.",
        ]

    def _upsert_pattern(
        self,
        pattern_key: str,
        title: str,
        pattern_type: str,
        hazard_category: Optional[str],
        sif_category: Optional[str],
        activity: Optional[str],
        life_saving_rule: Optional[str],
        failed_barriers: List[str],
        department_id: Optional[int],
        location_id: Optional[int],
        risk_score: float,
        risk_level: str,
        frequency_count: int,
        sif_count: int,
        sif_density: float,
        trend_percentage: float,
        scoring_factors: Dict[str, Any],
        evidence_report_ids: List[int],
        evidence_case_ids: List[str],
        recommendations: List[str],
        first_dt: datetime,
        last_dt: datetime,
        db: Session,
    ) -> Pattern:
        existing = db.query(Pattern).filter(Pattern.pattern_key == pattern_key).first()
        if existing:
            existing.title = title
            existing.pattern_type = pattern_type
            existing.hazard_category = hazard_category
            existing.sif_category = sif_category
            existing.activity = activity
            existing.life_saving_rule = life_saving_rule
            existing.failed_barriers = failed_barriers
            existing.department_id = department_id
            existing.location_id = location_id
            existing.risk_score = risk_score
            existing.risk_level = risk_level
            existing.frequency_count = frequency_count
            existing.sif_count = sif_count
            existing.sif_density = sif_density
            existing.trend_percentage = trend_percentage
            existing.scoring_factors = scoring_factors
            existing.evidence_report_ids = evidence_report_ids
            existing.evidence_case_ids = evidence_case_ids
            existing.recommendations = recommendations
            existing.last_detected_at = last_dt
            db.add(existing)
            return existing
        else:
            new_p = Pattern(
                pattern_key=pattern_key,
                title=title,
                pattern_type=pattern_type,
                hazard_category=hazard_category,
                sif_category=sif_category,
                activity=activity,
                life_saving_rule=life_saving_rule,
                failed_barriers=failed_barriers,
                department_id=department_id,
                location_id=location_id,
                risk_score=risk_score,
                risk_level=risk_level,
                frequency_count=frequency_count,
                sif_count=sif_count,
                sif_density=sif_density,
                trend_percentage=trend_percentage,
                scoring_factors=scoring_factors,
                evidence_report_ids=evidence_report_ids,
                evidence_case_ids=evidence_case_ids,
                recommendations=recommendations,
                status="ACTIVE",
                first_detected_at=first_dt,
                last_detected_at=last_dt,
            )
            db.add(new_p)
            return new_p


pattern_engine = PatternDetectionEngine()
