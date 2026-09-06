import logging
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.models.import_batch import ImportBatch
from app.models.department import Department
from app.models.location import Location
from app.schemas.analytics import (
    DashboardKpis,
    TrendPoint,
    HazardTrendItem,
    DepartmentRiskItem,
    LocationRiskItem,
    ActivityRiskItem,
    LifeSavingRuleRiskItem,
    BarrierFailureRecurrenceItem,
    TrendComparisonResponse,
    SifDensityResponse,
    TopRiskAreaItem,
    RiskMapMarker,
)

logger = logging.getLogger(__name__)


def _calculate_trend(cur_count: int, prev_count: int) -> float:
    """
    Computes percentage change between current period and previous equivalent period.
    Formula: ((current - previous) / previous) * 100
    If previous is 0 and current > 0, returns 100.0 (representing newly emerging volume).
    If both are 0, returns 0.0.
    """
    if prev_count == 0:
        return 100.0 if cur_count > 0 else 0.0
    return round(((cur_count - prev_count) / prev_count) * 100.0, 1)


def _get_report_datetime(report: SafetyReport) -> datetime:
    """Safely extracts UTC datetime from safety report."""
    rep_date = report.reported_at or report.created_at
    if rep_date and rep_date.tzinfo is None:
        rep_date = rep_date.replace(tzinfo=timezone.utc)
    return rep_date or datetime.now(timezone.utc)


class AnalyticsService:
    """
    SIF Precursor Intelligence & Safety Analytics Engine for OIL Operations.
    Calculates SIF precursor density, multi-dimensional rankings, barrier recurrence,
    Life-Saving Rule distributions, and multi-period trend comparisons from actual historical data.
    """

    DEFAULT_LOCATION_COORDINATES = {
        "Duliajan Central Field": (27.3563, 95.3182),
        "Duliajan Central Complex": (27.3563, 95.3182),
        "Digboi Refinery Asset": (27.3800, 95.6300),
        "Digboi Refinery Block 4": (27.3800, 95.6300),
        "Moran Oil Field Asset": (27.1850, 94.9250),
        "Moran Wellpad #14": (27.1850, 94.9250),
        "Jorhat Exploration Basin": (26.7509, 94.2037),
        "Jorhat Pumping Station": (26.7509, 94.2037),
        "Naharkatia Production Facility": (27.2800, 95.3500),
        "Naharkatia GGS-3": (27.2800, 95.3500),
        "Baghjan EPS-2": (27.5833, 95.3500),
        "Kumchai Rig #7": (27.3167, 96.0167),
        "Unit A": (27.3563, 95.3182),
        "Unit B": (27.3800, 95.6300),
        "Unit C": (27.1850, 94.9250),
        "Unit D": (26.7509, 94.2037),
        "Main Plant": (27.2800, 95.3500),
    }

    def get_dashboard_kpis(self, db: Session) -> DashboardKpis:
        total_reports = db.query(SafetyReport).count()
        analyses = db.query(AiAnalysis).all()
        
        critical_count = sum(1 for a in analyses if a.risk_score >= 70 or a.risk_level == "CRITICAL")
        high_count = sum(1 for a in analyses if (50 <= a.risk_score < 70) or a.risk_level == "HIGH")
        sif_count = sum(1 for a in analyses if a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"])
        
        sif_density = round((sif_count / total_reports * 100.0), 1) if total_reports > 0 else 0.0

        active_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"])).count()
        emerging_risks = db.query(Alert).filter(
            Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"]),
            Alert.alert_type.in_(["INCREASING_TREND", "EMERGING_RISK", "COMBINED_RISK", "REPEATED_SIF_PRECURSOR"])
        ).count()
        open_actions = db.query(CorrectiveAction).filter(CorrectiveAction.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "OVERDUE"])).count()

        now = datetime.now(timezone.utc)
        actions = db.query(CorrectiveAction).filter(CorrectiveAction.status != "RESOLVED", CorrectiveAction.due_date != None).all()
        overdue_count = 0
        for act in actions:
            due = act.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now:
                overdue_count += 1

        total_batches = db.query(ImportBatch).count()

        return DashboardKpis(
            total_reports=total_reports,
            critical_risk_count=critical_count,
            high_risk_count=high_count,
            sif_precursors_count=sif_count,
            sif_density=sif_density,
            active_alerts_count=active_alerts,
            emerging_risks_count=emerging_risks,
            open_actions_count=open_actions,
            overdue_actions_count=overdue_count,
            total_batches_count=total_batches,
        )

    def get_sif_density(self, db: Session) -> SifDensityResponse:
        """
        Calculates SIF Precursor Density across all dimensions:
        Overall, Locations, Activities, Departments, Life-Saving Rules, Hazards, Barrier Failures, Incident Types.
        Formula: (SIF precursor reports / total reports in group) * 100
        """
        reports_with_ai = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        total_reports = len(reports_with_ai)
        total_sif = sum(1 for _, ai in reports_with_ai if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        overall_density = round((total_sif / max(total_reports, 1)) * 100.0, 1)

        # Helper to compute group density
        def compute_group_density(extractor_fn):
            groups: Dict[str, Dict[str, int]] = {}
            for r, ai in reports_with_ai:
                keys = extractor_fn(r, ai)
                if not isinstance(keys, list):
                    keys = [keys]
                is_sif = 1 if (ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"])) else 0
                for k in keys:
                    if not k:
                        continue
                    if k not in groups:
                        groups[k] = {"total": 0, "sif": 0}
                    groups[k]["total"] += 1
                    groups[k]["sif"] += is_sif

            items = []
            for name, data in groups.items():
                tot = data["total"]
                sif = data["sif"]
                density = round((sif / max(tot, 1)) * 100.0, 1)
                items.append({
                    "name": name,
                    "total_reports": tot,
                    "sif_count": sif,
                    "sif_density": density,
                })
            return sorted(items, key=lambda x: (x["sif_density"], x["sif_count"]), reverse=True)

        by_location = compute_group_density(lambda r, ai: r.location.name if r.location else (r.site or "Unknown Location"))
        by_activity = compute_group_density(lambda r, ai: (ai.activity if ai and ai.activity else r.activity) or r.task or "General Operations")
        by_department = compute_group_density(lambda r, ai: r.department.name if r.department else "Unknown Department")
        by_life_saving_rule = compute_group_density(lambda r, ai: (ai.life_saving_rule if ai and ai.life_saving_rule else r.life_saving_rule) or "Unmapped Rule")
        
        by_hazard = compute_group_density(
            lambda r, ai: [h.get("hazard_type", "Hazard") for h in ai.hazards] if (ai and ai.hazards) else ["General Observation"]
        )
        by_barrier = compute_group_density(
            lambda r, ai: [fb.get("barrier_name", "Barrier") for fb in ai.failed_barriers] if (ai and ai.failed_barriers) else []
        )
        by_incident_type = compute_group_density(
            lambda r, ai: r.incident_type.value if hasattr(r.incident_type, "value") else str(r.incident_type)
        )

        return SifDensityResponse(
            overall_density=overall_density,
            total_reports=total_reports,
            total_sif_precursors=total_sif,
            by_location=by_location,
            by_activity=by_activity,
            by_department=by_department,
            by_life_saving_rule=by_life_saving_rule,
            by_hazard=by_hazard,
            by_barrier_failure=by_barrier,
            by_incident_type=by_incident_type,
        )

    def get_activity_risk(self, db: Session, window_days: int = 30) -> List[ActivityRiskItem]:
        """
        Rankings by SIF precursor density for operational activities with real historical period trend comparison.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        reports_with_ai = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        activity_map: Dict[str, Dict[str, Any]] = {}
        for r, ai in reports_with_ai:
            act_name = (ai.activity if ai and ai.activity else r.activity) or r.task or "General Plant Operations"
            cat = (ai.activity_category if ai and ai.activity_category else r.activity_category) or "Maintenance & Integrity"
            r_date = _get_report_datetime(r)

            if act_name not in activity_map:
                activity_map[act_name] = {
                    "category": cat,
                    "total": 0,
                    "sif": 0,
                    "cur_count": 0,
                    "prev_count": 0,
                    "scores": [],
                    "hazards": {},
                    "barriers": {},
                }
            
            activity_map[act_name]["total"] += 1
            if cur_start <= r_date <= now:
                activity_map[act_name]["cur_count"] += 1
            elif prev_start <= r_date < cur_start:
                activity_map[act_name]["prev_count"] += 1

            if ai:
                if ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]:
                    activity_map[act_name]["sif"] += 1
                if ai.risk_score > 0:
                    activity_map[act_name]["scores"].append(ai.risk_score)
                for h in ai.hazards:
                    ht = h.get("hazard_type", "Hazard")
                    activity_map[act_name]["hazards"][ht] = activity_map[act_name]["hazards"].get(ht, 0) + 1
                for b in ai.failed_barriers:
                    bn = b.get("barrier_name", "Barrier")
                    activity_map[act_name]["barriers"][bn] = activity_map[act_name]["barriers"].get(bn, 0) + 1

        items: List[ActivityRiskItem] = []
        for act, data in activity_map.items():
            tot = data["total"]
            sif = data["sif"]
            density = round((sif / max(tot, 1)) * 100.0, 1)
            avg_risk = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 35.0
            top_h = max(data["hazards"], key=data["hazards"].get) if data["hazards"] else "Operational Risk"
            top_b = max(data["barriers"], key=data["barriers"].get) if data["barriers"] else "Procedure Verification"
            
            # Real historical comparison between current window and previous window
            trend = _calculate_trend(data["cur_count"], data["prev_count"])

            items.append(
                ActivityRiskItem(
                    activity=act,
                    activity_category=data["category"],
                    total_reports=tot,
                    sif_count=sif,
                    sif_density=density,
                    avg_risk_score=avg_risk,
                    top_hazard=top_h,
                    top_barrier_failure=top_b,
                    trend_percentage=trend,
                )
            )

        # Prioritize by SIF density, then SIF count
        return sorted(items, key=lambda x: (x.sif_density, x.sif_count), reverse=True)

    def get_location_risk(self, db: Session, window_days: int = 30) -> List[LocationRiskItem]:
        """
        Rankings by SIF precursor density for operating locations with real historical period trend comparison.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        locations = db.query(Location).all()
        items = []

        for loc in locations:
            loc_reports = (
                db.query(SafetyReport, AiAnalysis)
                .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
                .filter(SafetyReport.location_id == loc.id)
                .all()
            )

            total_reps = len(loc_reports)
            scores = [ai.risk_score for _, ai in loc_reports if ai and ai.risk_score > 0]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            sif_cnt = sum(1 for _, ai in loc_reports if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
            crit_cnt = sum(1 for _, ai in loc_reports if ai and (ai.risk_score >= 70 or ai.risk_level == "CRITICAL"))
            sif_density = round((sif_cnt / max(total_reps, 1)) * 100.0, 1)

            # Real historical period counts for this location
            cur_loc_cnt = sum(1 for r, _ in loc_reports if cur_start <= _get_report_datetime(r) <= now)
            prev_loc_cnt = sum(1 for r, _ in loc_reports if prev_start <= _get_report_datetime(r) < cur_start)
            trend_pct = _calculate_trend(cur_loc_cnt, prev_loc_cnt)

            open_acts = db.query(CorrectiveAction).filter(CorrectiveAction.location_id == loc.id, CorrectiveAction.status != "RESOLVED").count()

            # Main hazard & Top barrier
            haz_counts: Dict[str, int] = {}
            barrier_counts: Dict[str, int] = {}
            for r, ai in loc_reports:
                if ai:
                    for h in ai.hazards:
                        ht = h.get("hazard_type", "Hazard")
                        haz_counts[ht] = haz_counts.get(ht, 0) + 1
                    for b in ai.failed_barriers:
                        bn = b.get("barrier_name", "Barrier")
                        barrier_counts[bn] = barrier_counts.get(bn, 0) + 1

            main_haz = max(haz_counts, key=haz_counts.get) if haz_counts else "Operational Hazards"
            top_bar = max(barrier_counts, key=barrier_counts.get) if barrier_counts else "Procedure Compliance"

            lat = loc.latitude
            lon = loc.longitude
            if not lat or not lon:
                coord = self.DEFAULT_LOCATION_COORDINATES.get(loc.name, (27.3563, 95.3182))
                lat, lon = coord

            risk_lvl = "CRITICAL" if (avg_score >= 65 or sif_density >= 25.0 or crit_cnt >= 2) else ("HIGH" if (avg_score >= 45 or sif_density >= 15.0 or sif_cnt >= 1) else ("MEDIUM" if avg_score >= 25 else "LOW"))

            items.append(
                LocationRiskItem(
                    location_id=loc.id,
                    location_name=loc.name,
                    total_reports=total_reps,
                    avg_risk_score=avg_score,
                    sif_count=sif_cnt,
                    sif_density=sif_density,
                    trend_percentage=trend_pct,
                    critical_count=crit_cnt,
                    open_actions_count=open_acts,
                    risk_level=risk_lvl,
                    latitude=lat,
                    longitude=lon,
                    main_hazard=main_haz,
                    top_barrier_failure=top_bar,
                )
            )

        # Rank by SIF density
        return sorted(items, key=lambda x: (x.sif_density, x.sif_count), reverse=True)

    def get_life_saving_rules_risk(self, db: Session, window_days: int = 30) -> List[LifeSavingRuleRiskItem]:
        """
        Calculates IOGP Life-Saving Rules risk breakdown with real historical period trend comparison.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        reports_with_ai = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        lsr_map: Dict[str, Dict[str, Any]] = {}
        for r, ai in reports_with_ai:
            lsr = (ai.life_saving_rule if ai and ai.life_saving_rule else r.life_saving_rule)
            if not lsr:
                continue

            r_date = _get_report_datetime(r)

            if lsr not in lsr_map:
                lsr_map[lsr] = {
                    "total": 0,
                    "sif": 0,
                    "cur_count": 0,
                    "prev_count": 0,
                    "scores": [],
                    "hazards": {},
                    "barriers": {},
                    "locations": {},
                    "activities": {},
                }

            lsr_map[lsr]["total"] += 1
            if cur_start <= r_date <= now:
                lsr_map[lsr]["cur_count"] += 1
            elif prev_start <= r_date < cur_start:
                lsr_map[lsr]["prev_count"] += 1

            if ai:
                if ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]:
                    lsr_map[lsr]["sif"] += 1
                if ai.risk_score > 0:
                    lsr_map[lsr]["scores"].append(ai.risk_score)
                for h in ai.hazards:
                    ht = h.get("hazard_type", "Hazard")
                    lsr_map[lsr]["hazards"][ht] = lsr_map[lsr]["hazards"].get(ht, 0) + 1
                for b in ai.failed_barriers:
                    bn = b.get("barrier_name", "Barrier")
                    lsr_map[lsr]["barriers"][bn] = lsr_map[lsr]["barriers"].get(bn, 0) + 1
            
            loc_name = r.location.name if r.location else (r.site or "Main Field")
            lsr_map[lsr]["locations"][loc_name] = lsr_map[lsr]["locations"].get(loc_name, 0) + 1
            
            act_name = (ai.activity if ai and ai.activity else r.activity) or r.task or "Operational Activity"
            lsr_map[lsr]["activities"][act_name] = lsr_map[lsr]["activities"].get(act_name, 0) + 1

        items: List[LifeSavingRuleRiskItem] = []
        for rule, data in lsr_map.items():
            tot = data["total"]
            sif = data["sif"]
            density = round((sif / max(tot, 1)) * 100.0, 1)
            avg_risk = round(sum(data["scores"]) / len(data["scores"]), 1) if data["scores"] else 40.0
            trend = _calculate_trend(data["cur_count"], data["prev_count"])

            top_h = sorted(data["hazards"].keys(), key=lambda k: data["hazards"][k], reverse=True)[:3]
            top_b = sorted(data["barriers"].keys(), key=lambda k: data["barriers"][k], reverse=True)[:3]
            top_l = sorted(data["locations"].keys(), key=lambda k: data["locations"][k], reverse=True)[:3]
            top_a = sorted(data["activities"].keys(), key=lambda k: data["activities"][k], reverse=True)[:3]

            items.append(
                LifeSavingRuleRiskItem(
                    rule_name=rule,
                    total_reports=tot,
                    sif_count=sif,
                    sif_density=density,
                    avg_risk_score=avg_risk,
                    trend_percentage=trend,
                    top_hazards=top_h,
                    top_barrier_failures=top_b,
                    top_locations=top_l,
                    top_activities=top_a,
                )
            )

        return sorted(items, key=lambda x: (x.sif_density, x.sif_count), reverse=True)

    def get_barrier_failures_recurrence(self, db: Session, window_days: int = 30) -> List[BarrierFailureRecurrenceItem]:
        """
        Calculates Top Recurring Barrier & Safeguard Failures with real historical period trend comparison.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        reports_with_ai = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        barrier_map: Dict[str, Dict[str, Any]] = {}
        for r, ai in reports_with_ai:
            if not ai or not ai.failed_barriers:
                continue
            is_sif = 1 if (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]) else 0
            r_date = _get_report_datetime(r)
            
            for fb in ai.failed_barriers:
                bname = fb.get("barrier_name", "Barrier")
                hlevel = fb.get("hierarchy_level", "ENGINEERING")
                if bname not in barrier_map:
                    barrier_map[bname] = {
                        "hierarchy_level": hlevel,
                        "total": 0,
                        "sif": 0,
                        "cur_count": 0,
                        "prev_count": 0,
                        "activities": {},
                        "locations": {},
                    }
                barrier_map[bname]["total"] += 1
                barrier_map[bname]["sif"] += is_sif
                if cur_start <= r_date <= now:
                    barrier_map[bname]["cur_count"] += 1
                elif prev_start <= r_date < cur_start:
                    barrier_map[bname]["prev_count"] += 1

                act = (ai.activity if ai.activity else r.activity) or r.task or "General Task"
                barrier_map[bname]["activities"][act] = barrier_map[bname]["activities"].get(act, 0) + 1

                loc = r.location.name if r.location else (r.site or "Main Plant")
                barrier_map[bname]["locations"][loc] = barrier_map[bname]["locations"].get(loc, 0) + 1

        items: List[BarrierFailureRecurrenceItem] = []
        for bname, data in barrier_map.items():
            tot = data["total"]
            sif = data["sif"]
            density = round((sif / max(tot, 1)) * 100.0, 1)
            trend = _calculate_trend(data["cur_count"], data["prev_count"])

            top_acts = sorted(data["activities"].keys(), key=lambda k: data["activities"][k], reverse=True)[:3]
            top_locs = sorted(data["locations"].keys(), key=lambda k: data["locations"][k], reverse=True)[:3]

            items.append(
                BarrierFailureRecurrenceItem(
                    barrier_name=bname,
                    hierarchy_level=data["hierarchy_level"],
                    total_reports=tot,
                    sif_count=sif,
                    sif_density=density,
                    trend_percentage=trend,
                    affected_activities=top_acts,
                    affected_locations=top_locs,
                )
            )

        return sorted(items, key=lambda x: (x.sif_count, x.total_reports), reverse=True)

    def get_trend_comparison(self, db: Session, window_days: int = 30) -> TrendComparisonResponse:
        """
        Compares current period (last X days) vs previous period (prior X days)
        for early-warning emerging risk detection. Equal window durations are strictly preserved.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        cur_reports = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .filter(SafetyReport.reported_at >= cur_start, SafetyReport.reported_at <= now)
            .all()
        )

        prev_reports = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .filter(SafetyReport.reported_at >= prev_start, SafetyReport.reported_at < cur_start)
            .all()
        )

        # Current period metrics
        cur_tot = len(cur_reports)
        cur_sif = sum(1 for _, ai in cur_reports if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        cur_density = round((cur_sif / max(cur_tot, 1)) * 100.0, 1) if cur_tot > 0 else 0.0
        cur_scores = [ai.risk_score for _, ai in cur_reports if ai and ai.risk_score > 0]
        cur_avg_risk = round(sum(cur_scores) / len(cur_scores), 1) if cur_scores else 0.0

        # Previous period metrics
        prev_tot = len(prev_reports)
        prev_sif = sum(1 for _, ai in prev_reports if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
        prev_density = round((prev_sif / max(prev_tot, 1)) * 100.0, 1) if prev_tot > 0 else 0.0
        prev_scores = [ai.risk_score for _, ai in prev_reports if ai and ai.risk_score > 0]
        prev_avg_risk = round(sum(prev_scores) / len(prev_scores), 1) if prev_scores else 0.0

        # Real percentage changes with safe zero handling
        freq_change = _calculate_trend(cur_tot, prev_tot)
        sif_change = _calculate_trend(cur_sif, prev_sif)
        density_change = round(cur_density - prev_density, 1)
        risk_change = round(cur_avg_risk - prev_avg_risk, 1)

        # Extract emerging signals based on genuine metric increases
        signals = []
        if sif_change > 15.0 or (cur_sif > prev_sif and cur_sif >= 2):
            signals.append({
                "signal_type": "SIF_PRECURSOR_SURGE",
                "severity": "CRITICAL" if sif_change > 30.0 else "HIGH",
                "title": f"SIF Precursor Volume Increased by {sif_change}%",
                "description": f"SIF precursor signals surged in the active {window_days}-day window ({cur_sif} events) compared to prior period ({prev_sif} events).",
                "metric_change": f"+{sif_change}% SIF Count",
            })
        
        # Check for recurring barrier surges
        cur_barriers: Dict[str, int] = {}
        for _, ai in cur_reports:
            if ai and ai.failed_barriers:
                for b in ai.failed_barriers:
                    bn = b.get("barrier_name", "Barrier")
                    cur_barriers[bn] = cur_barriers.get(bn, 0) + 1
        
        for bn, count in sorted(cur_barriers.items(), key=lambda x: x[1], reverse=True)[:2]:
            if count >= 2:
                signals.append({
                    "signal_type": "BARRIER_BREAKDOWN",
                    "severity": "HIGH",
                    "title": f"Recurring Barrier Failure: {bn}",
                    "description": f"Detected {count} instances of {bn} breakdown in the active {window_days}-day monitoring window.",
                    "metric_change": f"{count} occurrences",
                })

        return TrendComparisonResponse(
            window_days=window_days,
            current_period_reports=cur_tot,
            previous_period_reports=prev_tot,
            frequency_change_pct=freq_change,
            current_sif_count=cur_sif,
            previous_sif_count=prev_sif,
            sif_count_change_pct=sif_change,
            current_sif_density=cur_density,
            previous_sif_density=prev_density,
            sif_density_change=density_change,
            current_avg_risk=cur_avg_risk,
            previous_avg_risk=prev_avg_risk,
            risk_score_change=risk_change,
            emerging_signals=signals,
        )

    def get_risk_trend(self, db: Session, weeks: int = 4) -> List[TrendPoint]:
        """
        Weekly time-series risk scores and SIF precursor metrics based on real database records.
        """
        now = datetime.now(timezone.utc)
        trend_points: List[TrendPoint] = []

        for i in range(weeks - 1, -1, -1):
            start_date = now - timedelta(days=(i + 1) * 7)
            end_date = now - timedelta(days=i * 7)
            label = f"Week {weeks - i}"

            reports_in_week = (
                db.query(SafetyReport, AiAnalysis)
                .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
                .filter(SafetyReport.reported_at >= start_date, SafetyReport.reported_at < end_date)
                .all()
            )

            count = len(reports_in_week)
            ai_scores = [ai.risk_score for _, ai in reports_in_week if ai and ai.risk_score > 0]
            avg_risk = sum(ai_scores) / len(ai_scores) if ai_scores else 0.0
            sifs = sum(1 for _, ai in reports_in_week if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
            density = round((sifs / max(count, 1)) * 100.0, 1) if count > 0 else 0.0

            trend_points.append(
                TrendPoint(
                    period=f"W{weeks - i}",
                    label=label,
                    value=round(avg_risk, 1),
                    count=count,
                    sif_count=sifs,
                    sif_density=density,
                )
            )

        return trend_points

    def get_hazard_trend(self, db: Session) -> List[HazardTrendItem]:
        reports = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        hazard_counts: Dict[str, int] = {}
        hazard_sifs: Dict[str, int] = {}
        total = max(len(reports), 1)

        for r, ai in reports:
            is_sif = ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"])
            if ai and ai.hazards:
                for h in ai.hazards:
                    ht = h.get("hazard_type", "Hazard")
                    hazard_counts[ht] = hazard_counts.get(ht, 0) + 1
                    if is_sif:
                        hazard_sifs[ht] = hazard_sifs.get(ht, 0) + 1
            else:
                hazard_counts["General Observation"] = hazard_counts.get("General Observation", 0) + 1

        items = []
        for haz, cnt in sorted(hazard_counts.items(), key=lambda x: x[1], reverse=True)[:7]:
            sif_c = hazard_sifs.get(haz, 0)
            density = round((sif_c / max(cnt, 1)) * 100.0, 1)
            items.append(
                HazardTrendItem(
                    hazard=haz,
                    count=cnt,
                    percentage=round((cnt / total) * 100.0, 1),
                    sif_count=sif_c,
                    sif_density=density,
                )
            )
        return items

    def get_sif_trend(self, db: Session, window_days: int = 30) -> Dict[str, Any]:
        """
        Computes real SIF precursor volume, density, category breakdown, and historical trend.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        analyses_with_rep = (
            db.query(AiAnalysis, SafetyReport)
            .join(SafetyReport, AiAnalysis.report_id == SafetyReport.id)
            .all()
        )
        total_analyzed = max(len(analyses_with_rep), 1)
        sif_analyses = [a for a, _ in analyses_with_rep if a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"]]

        sif_count = len(sif_analyses)
        sif_percentage = round((sif_count / total_analyzed) * 100.0, 1)

        # Real period comparison
        cur_sif = sum(1 for a, r in analyses_with_rep if (a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"]) and cur_start <= _get_report_datetime(r) <= now)
        prev_sif = sum(1 for a, r in analyses_with_rep if (a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"]) and prev_start <= _get_report_datetime(r) < cur_start)
        sif_trend_val = _calculate_trend(cur_sif, prev_sif)
        sif_trend_str = f"+{sif_trend_val}%" if sif_trend_val > 0 else f"{sif_trend_val}%"

        sif_cats: Dict[str, int] = {}
        for a in sif_analyses:
            if a.sif_categories:
                for c in a.sif_categories:
                    sif_cats[str(c)] = sif_cats.get(str(c), 0) + 1
            else:
                sif_cats["High Risk Precursor"] = sif_cats.get("High Risk Precursor", 0) + 1

        return {
            "sif_count": sif_count,
            "total_analyzed": total_analyzed,
            "sif_percentage": sif_percentage,
            "sif_density": sif_percentage,
            "sif_categories": [{"category": k, "count": v} for k, v in sorted(sif_cats.items(), key=lambda x: x[1], reverse=True)],
            "sif_trend": sif_trend_str,
        }

    def get_department_risk(self, db: Session, window_days: int = 30) -> List[DepartmentRiskItem]:
        """
        Department risk breakdown with real historical period trend comparison.
        """
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=window_days)
        prev_start = now - timedelta(days=window_days * 2)

        depts = db.query(Department).all()
        items = []

        for d in depts:
            dept_reports = (
                db.query(SafetyReport, AiAnalysis)
                .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
                .filter(SafetyReport.department_id == d.id)
                .all()
            )

            total_reps = len(dept_reports)
            scores = [ai.risk_score for _, ai in dept_reports if ai and ai.risk_score > 0]
            avg_score = round(sum(scores) / len(scores), 1) if scores else 0.0
            sif_cnt = sum(1 for _, ai in dept_reports if ai and (ai.sif_precursor or ai.sif_detected or ai.sif_level in ["HIGH", "CRITICAL"]))
            crit_cnt = sum(1 for _, ai in dept_reports if ai and (ai.risk_score >= 70 or ai.risk_level == "CRITICAL"))
            sif_density = round((sif_cnt / max(total_reps, 1)) * 100.0, 1)

            # Real historical period counts for this department
            cur_dept_cnt = sum(1 for r, _ in dept_reports if cur_start <= _get_report_datetime(r) <= now)
            prev_dept_cnt = sum(1 for r, _ in dept_reports if prev_start <= _get_report_datetime(r) < cur_start)
            trend_pct = _calculate_trend(cur_dept_cnt, prev_dept_cnt)

            risk_lvl = "CRITICAL" if avg_score >= 65 or crit_cnt >= 2 else ("HIGH" if avg_score >= 45 or sif_cnt >= 1 else ("MEDIUM" if avg_score >= 25 else "LOW"))

            items.append(
                DepartmentRiskItem(
                    department_id=d.id,
                    department_name=d.name,
                    total_reports=total_reps,
                    avg_risk_score=avg_score,
                    sif_count=sif_cnt,
                    sif_density=sif_density,
                    trend_percentage=trend_pct,
                    critical_count=crit_cnt,
                    risk_level=risk_lvl,
                )
            )

        return sorted(items, key=lambda x: (x.sif_density, x.avg_risk_score), reverse=True)

    def get_top_risk_areas(self, db: Session) -> List[TopRiskAreaItem]:
        loc_risks = self.get_location_risk(db)
        top_areas = []
        for rank, lr in enumerate(loc_risks[:5], start=1):
            top_areas.append(
                TopRiskAreaItem(
                    rank=rank,
                    location_id=lr.location_id,
                    location_name=lr.location_name,
                    risk_level=lr.risk_level,
                    risk_score=lr.avg_risk_score,
                    main_hazard=lr.main_hazard or "Operational Hazards",
                    sif_count=lr.sif_count,
                    sif_density=lr.sif_density,
                    total_reports=lr.total_reports,
                    open_actions=lr.open_actions_count,
                )
            )
        return top_areas

    def get_risk_map_markers(self, db: Session) -> List[RiskMapMarker]:
        loc_risks = self.get_location_risk(db)
        markers = []

        for lr in loc_risks:
            alerts = db.query(Alert).filter(Alert.location_id == lr.location_id).order_by(Alert.id.desc()).limit(3).all()
            alert_titles = [a.title for a in alerts]

            markers.append(
                RiskMapMarker(
                    location_id=lr.location_id,
                    location_name=lr.location_name,
                    latitude=lr.latitude or 27.3563,
                    longitude=lr.longitude or 95.3182,
                    risk_score=lr.avg_risk_score,
                    risk_level=lr.risk_level,
                    total_reports=lr.total_reports,
                    high_risk_reports=lr.critical_count,
                    sif_precursors=lr.sif_count,
                    sif_density=lr.sif_density,
                    top_hazards=[lr.main_hazard] if lr.main_hazard else ["Operational Hazards"],
                    open_corrective_actions=lr.open_actions_count,
                    recent_alerts=alert_titles,
                )
            )

        return markers


analytics_service = AnalyticsService()
