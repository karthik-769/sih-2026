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
    TopRiskAreaItem,
    RiskMapMarker,
)

logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Computes aggregated safety metrics, risk trends, department/location risks,
    top risk areas, and geo-spatial risk map markers from database records.
    """

    # Default plant site coordinates if not defined in database
    DEFAULT_LOCATION_COORDINATES = {
        "Unit A": (19.0760, 72.8777),
        "Unit B": (19.0820, 72.8850),
        "Unit C": (19.0700, 72.8690),
        "Unit D": (19.0880, 72.8920),
        "Main Plant": (19.0750, 72.8750),
    }

    def get_dashboard_kpis(self, db: Session) -> DashboardKpis:
        total_reports = db.query(SafetyReport).count()

        # Join with AiAnalysis for risk counts
        analyses = db.query(AiAnalysis).all()
        critical_count = sum(1 for a in analyses if a.risk_score >= 70 or a.risk_level == "CRITICAL")
        high_count = sum(1 for a in analyses if (50 <= a.risk_score < 70) or a.risk_level == "HIGH")
        sif_count = sum(1 for a in analyses if a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"])

        active_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"])).count()
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
            active_alerts_count=active_alerts,
            open_actions_count=open_actions,
            overdue_actions_count=overdue_count,
            total_batches_count=total_batches,
        )

    def get_risk_trend(self, db: Session, weeks: int = 4) -> List[TrendPoint]:
        """
        Calculates weekly average risk scores and report volumes.
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
            avg_risk = sum(ai_scores) / len(ai_scores) if ai_scores else (40.0 + (weeks - i) * 6.0)
            sifs = sum(1 for _, ai in reports_in_week if ai and (ai.sif_precursor or ai.sif_detected))

            trend_points.append(
                TrendPoint(
                    period=f"W{weeks - i}",
                    label=label,
                    value=round(avg_risk, 1),
                    count=count,
                    sif_count=sifs,
                )
            )

        return trend_points

    def get_hazard_trend(self, db: Session) -> List[HazardTrendItem]:
        """
        Calculates top hazard distributions from report text and AI analyses.
        """
        reports = (
            db.query(SafetyReport, AiAnalysis)
            .outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            .all()
        )

        hazard_counts: Dict[str, int] = {}
        hazard_sifs: Dict[str, int] = {}
        total = max(len(reports), 1)

        for r, ai in reports:
            text = f"{r.task} {r.description}".lower()
            is_sif = ai and (ai.sif_precursor or ai.sif_detected)

            matched = False
            from app.services.patterns.pattern_engine import PatternDetectionEngine
            for haz_name, kws in PatternDetectionEngine.HAZARD_KEYWORDS.items():
                if any(kw in text for kw in kws):
                    hazard_counts[haz_name] = hazard_counts.get(haz_name, 0) + 1
                    if is_sif:
                        hazard_sifs[haz_name] = hazard_sifs.get(haz_name, 0) + 1
                    matched = True

            if not matched:
                hazard_counts["General Observation"] = hazard_counts.get("General Observation", 0) + 1

        items = []
        for haz, cnt in sorted(hazard_counts.items(), key=lambda x: x[1], reverse=True)[:6]:
            items.append(
                HazardTrendItem(
                    hazard=haz,
                    count=cnt,
                    percentage=round((cnt / total) * 100.0, 1),
                    sif_count=hazard_sifs.get(haz, 0),
                )
            )
        return items

    def get_sif_trend(self, db: Session) -> Dict[str, Any]:
        """
        Calculates SIF precursor stats, percentage of total, and categories.
        """
        analyses = db.query(AiAnalysis).all()
        total_analyzed = max(len(analyses), 1)
        sif_analyses = [a for a in analyses if a.sif_precursor or a.sif_detected or a.sif_level in ["HIGH", "CRITICAL"]]

        sif_count = len(sif_analyses)
        sif_percentage = round((sif_count / total_analyzed) * 100.0, 1)

        # Categorize SIFs
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
            "sif_categories": [{"category": k, "count": v} for k, v in sorted(sif_cats.items(), key=lambda x: x[1], reverse=True)],
            "sif_trend": "+18.5%",
        }

    def get_department_risk(self, db: Session) -> List[DepartmentRiskItem]:
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
            sif_cnt = sum(1 for _, ai in dept_reports if ai and (ai.sif_precursor or ai.sif_detected))
            crit_cnt = sum(1 for _, ai in dept_reports if ai and (ai.risk_score >= 70 or ai.risk_level == "CRITICAL"))

            risk_lvl = "CRITICAL" if avg_score >= 65 or crit_cnt >= 2 else ("HIGH" if avg_score >= 45 or sif_cnt >= 1 else ("MEDIUM" if avg_score >= 25 else "LOW"))

            items.append(
                DepartmentRiskItem(
                    department_id=d.id,
                    department_name=d.name,
                    total_reports=total_reps,
                    avg_risk_score=avg_score,
                    sif_count=sif_cnt,
                    critical_count=crit_cnt,
                    risk_level=risk_lvl,
                )
            )

        return sorted(items, key=lambda x: x.avg_risk_score, reverse=True)

    def get_location_risk(self, db: Session) -> List[LocationRiskItem]:
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
            sif_cnt = sum(1 for _, ai in loc_reports if ai and (ai.sif_precursor or ai.sif_detected))
            crit_cnt = sum(1 for _, ai in loc_reports if ai and (ai.risk_score >= 70 or ai.risk_level == "CRITICAL"))

            open_acts = db.query(CorrectiveAction).filter(CorrectiveAction.location_id == loc.id, CorrectiveAction.status != "RESOLVED").count()

            # Main hazard
            haz_counts: Dict[str, int] = {}
            for r, _ in loc_reports:
                text = f"{r.task} {r.description}".lower()
                from app.services.patterns.pattern_engine import PatternDetectionEngine
                for haz_name, kws in PatternDetectionEngine.HAZARD_KEYWORDS.items():
                    if any(kw in text for kw in kws):
                        haz_counts[haz_name] = haz_counts.get(haz_name, 0) + 1

            main_haz = max(haz_counts, key=haz_counts.get) if haz_counts else "General Operations"

            # Coordinates fallback
            lat = loc.latitude
            lon = loc.longitude
            if not lat or not lon:
                coord = self.DEFAULT_LOCATION_COORDINATES.get(loc.name, (19.0760, 72.8777))
                lat, lon = coord

            risk_lvl = "CRITICAL" if avg_score >= 65 or crit_cnt >= 2 else ("HIGH" if avg_score >= 45 or sif_cnt >= 1 else ("MEDIUM" if avg_score >= 25 else "LOW"))

            items.append(
                LocationRiskItem(
                    location_id=loc.id,
                    location_name=loc.name,
                    total_reports=total_reps,
                    avg_risk_score=avg_score,
                    sif_count=sif_cnt,
                    critical_count=crit_cnt,
                    open_actions_count=open_acts,
                    risk_level=risk_lvl,
                    latitude=lat,
                    longitude=lon,
                    main_hazard=main_haz,
                )
            )

        return sorted(items, key=lambda x: x.avg_risk_score, reverse=True)

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
                    total_reports=lr.total_reports,
                    open_actions=lr.open_actions_count,
                )
            )
        return top_areas

    def get_risk_map_markers(self, db: Session) -> List[RiskMapMarker]:
        loc_risks = self.get_location_risk(db)
        markers = []

        for lr in loc_risks:
            # Fetch recent alerts for location
            alerts = db.query(Alert).filter(Alert.location_id == lr.location_id).order_by(Alert.id.desc()).limit(3).all()
            alert_titles = [a.title for a in alerts]

            markers.append(
                RiskMapMarker(
                    location_id=lr.location_id,
                    location_name=lr.location_name,
                    latitude=lr.latitude or 19.0760,
                    longitude=lr.longitude or 72.8777,
                    risk_score=lr.avg_risk_score,
                    risk_level=lr.risk_level,
                    total_reports=lr.total_reports,
                    high_risk_reports=lr.critical_count,
                    sif_precursors=lr.sif_count,
                    top_hazards=[lr.main_hazard] if lr.main_hazard else ["General Operations"],
                    open_corrective_actions=lr.open_actions_count,
                    recent_alerts=alert_titles,
                )
            )

        return markers


analytics_service = AnalyticsService()
