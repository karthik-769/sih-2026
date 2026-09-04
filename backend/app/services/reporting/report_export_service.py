import io
import csv
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
import openpyxl
import fitz

from app.models.safety_report import SafetyReport
from app.models.ai_analysis import AiAnalysis
from app.models.pattern import Pattern
from app.models.alert import Alert
from app.models.corrective_action import CorrectiveAction
from app.models.department import Department
from app.models.user import User
from app.models.import_batch import ImportBatch
from app.schemas.reporting import SafetyReportSummary

logger = logging.getLogger(__name__)


class ReportExportService:
    """
    Generates Safety Executive Reports and custom dataset exports (Reports, AI Analysis, Corrective Actions, Alerts, Users, Import History)
    into CSV, Excel (.xlsx), and PDF (.pdf) formats with full filtering support.
    """

    def generate_summary(
        self,
        report_type: str = "WEEKLY",
        timeframe_days: int = 30,
        department_id: Optional[int] = None,
        db: Session = None,
    ) -> SafetyReportSummary:
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(days=timeframe_days)

        query = db.query(SafetyReport, AiAnalysis).outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
        if department_id:
            query = query.filter(SafetyReport.department_id == department_id)

        records = query.all()
        total = len(records)

        risk_dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        sif_count = 0
        top_hazards_map: Dict[str, int] = {}

        for r, ai in records:
            if ai:
                lvl = ai.risk_level or "LOW"
                risk_dist[lvl] = risk_dist.get(lvl, 0) + 1
                if ai.sif_precursor or ai.sif_detected:
                    sif_count += 1
            else:
                risk_dist["LOW"] += 1

            text = f"{r.task} {r.description}".lower()
            from app.services.patterns.pattern_engine import PatternDetectionEngine
            for haz_name, kws in PatternDetectionEngine.HAZARD_KEYWORDS.items():
                if any(kw in text for kw in kws):
                    top_hazards_map[haz_name] = top_hazards_map.get(haz_name, 0) + 1

        top_hazards = [{"hazard": k, "count": v} for k, v in sorted(top_hazards_map.items(), key=lambda x: x[1], reverse=True)[:5]]

        active_patterns = db.query(Pattern).filter(Pattern.status == "ACTIVE").count()
        active_alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"])).count()
        open_actions = db.query(CorrectiveAction).filter(CorrectiveAction.status.in_(["OPEN", "ASSIGNED", "IN_PROGRESS", "OVERDUE"])).count()

        actions = db.query(CorrectiveAction).filter(CorrectiveAction.status != "RESOLVED", CorrectiveAction.due_date != None).all()
        overdue_actions = sum(1 for a in actions if a.due_date and a.due_date.replace(tzinfo=timezone.utc if a.due_date.tzinfo is None else a.due_date.tzinfo) < now)

        # Key recommendations
        patterns = db.query(Pattern).filter(Pattern.status == "ACTIVE").order_by(Pattern.risk_score.desc()).limit(3).all()
        key_recs = []
        for p in patterns:
            if p.recommendations:
                key_recs.extend(p.recommendations[:2])

        if not key_recs:
            key_recs = [
                "Maintain continuous management oversight on critical high-energy tasks.",
                "Reinforce 100% adherence to permit-to-work and zero-energy LOTO verification.",
            ]

        title = f"{report_type.replace('_', ' ').title()} Safety Intelligence & Risk Assessment Report"

        return SafetyReportSummary(
            report_title=title,
            generated_at=now,
            timeframe=f"Past {timeframe_days} Days",
            total_reports=total,
            risk_distribution=risk_dist,
            top_hazards=top_hazards,
            sif_precursors_count=sif_count,
            active_patterns_count=active_patterns,
            active_alerts_count=active_alerts,
            open_actions_count=open_actions,
            overdue_actions_count=overdue_actions,
            key_recommendations=key_recs[:5],
        )

    def export_data(
        self,
        export_type: str,  # SUMMARY, REPORTS, ACTIONS, ALERTS, USERS, IMPORTS
        export_format: str,  # csv, xlsx, pdf
        db: Session,
        department_id: Optional[int] = None,
        worker_id: Optional[int] = None,
        risk_level: Optional[str] = None,
        sif_status: Optional[str] = None,
        report_status: Optional[str] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        timeframe_days: int = 30,
    ) -> bytes:
        fmt = export_format.lower()
        now = datetime.now(timezone.utc)

        if export_type == "REPORTS":
            query = db.query(SafetyReport, AiAnalysis).outerjoin(AiAnalysis, SafetyReport.id == AiAnalysis.report_id)
            if department_id:
                query = query.filter(SafetyReport.department_id == department_id)
            if worker_id:
                query = query.filter(SafetyReport.created_by == worker_id)
            if report_status:
                query = query.filter(SafetyReport.processing_status == report_status.upper())
            if date_from:
                query = query.filter(SafetyReport.reported_at >= date_from)
            if date_to:
                query = query.filter(SafetyReport.reported_at <= date_to)

            records = query.order_by(SafetyReport.reported_at.desc()).all()

            # Filter by AI results if provided
            filtered_records = []
            for rep, ai in records:
                if risk_level and ai and ai.risk_level != risk_level.upper():
                    continue
                if sif_status == "YES" and (not ai or not (ai.sif_precursor or ai.sif_detected)):
                    continue
                if sif_status == "NO" and (ai and (ai.sif_precursor or ai.sif_detected)):
                    continue
                filtered_records.append((rep, ai))

            headers = ["Case ID", "Reported Date", "Department", "Job Role", "Task", "Incident Type", "Risk Level", "Risk Score", "SIF Precursor", "Status", "Description"]
            rows = []
            for rep, ai in filtered_records:
                rows.append([
                    rep.case_id,
                    rep.reported_at.strftime("%Y-%m-%d %H:%M") if rep.reported_at else "",
                    rep.department.name if rep.department else f"Dept #{rep.department_id}",
                    rep.job_role,
                    rep.task,
                    rep.incident_type.value if hasattr(rep.incident_type, "value") else str(rep.incident_type),
                    ai.risk_level if ai else "PENDING",
                    round(ai.risk_score, 1) if ai and ai.risk_score is not None else "N/A",
                    "YES" if ai and (ai.sif_precursor or ai.sif_detected) else "NO",
                    rep.processing_status.value if hasattr(rep.processing_status, "value") else str(rep.processing_status),
                    rep.description,
                ])

            title = "Safety Reports & AI Analysis Export"
            return self._build_tabular_export(title, headers, rows, fmt)

        elif export_type == "ACTIONS":
            query = db.query(CorrectiveAction)
            if department_id:
                query = query.filter(CorrectiveAction.department_id == department_id)
            if report_status:
                query = query.filter(CorrectiveAction.status == report_status.upper())
            actions = query.order_by(CorrectiveAction.id.desc()).all()

            headers = ["Action Number", "Title", "Priority", "Status", "Due Date", "Assignee", "Department", "Created At"]
            rows = []
            for act in actions:
                rows.append([
                    act.action_number,
                    act.title,
                    act.priority,
                    act.status,
                    act.due_date.strftime("%Y-%m-%d") if act.due_date else "None",
                    act.assignee.name if act.assignee else "Unassigned",
                    act.department.name if act.department else "N/A",
                    act.created_at.strftime("%Y-%m-%d") if act.created_at else "",
                ])
            title = "Corrective Actions Export"
            return self._build_tabular_export(title, headers, rows, fmt)

        elif export_type == "ALERTS":
            query = db.query(Alert)
            if department_id:
                query = query.filter(Alert.department_id == department_id)
            alerts = query.order_by(Alert.id.desc()).all()

            headers = ["Alert Key", "Severity", "Title", "Risk Score", "Status", "Department", "Created At"]
            rows = []
            for a in alerts:
                rows.append([
                    a.alert_key,
                    a.severity,
                    a.title,
                    round(a.risk_score, 1) if a.risk_score is not None else "",
                    a.status,
                    a.department.name if a.department else "N/A",
                    a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else "",
                ])
            title = "Early Warning Alerts Export"
            return self._build_tabular_export(title, headers, rows, fmt)

        elif export_type == "USERS":
            users = db.query(User).order_by(User.id.asc()).all()
            headers = ["User ID", "Name", "Email", "Role", "Status", "Created At"]
            rows = []
            for u in users:
                rows.append([
                    u.id,
                    u.name,
                    u.email,
                    u.role.value if hasattr(u.role, "value") else str(u.role),
                    "ACTIVE" if u.is_active else "INACTIVE",
                    u.created_at.strftime("%Y-%m-%d") if u.created_at else "",
                ])
            title = "User Directory Export"
            return self._build_tabular_export(title, headers, rows, fmt)

        elif export_type == "IMPORTS":
            batches = db.query(ImportBatch).order_by(ImportBatch.id.desc()).all()
            headers = ["Batch ID", "Filename", "File Type", "Total Records", "Imported Records", "Duplicate Records", "Failed Records", "Status", "Uploaded At"]
            rows = []
            for b in batches:
                rows.append([
                    b.batch_id,
                    b.filename,
                    b.file_type,
                    b.total_records,
                    b.imported_records,
                    b.duplicate_records,
                    b.failed_records,
                    b.status,
                    b.created_at.strftime("%Y-%m-%d %H:%M") if b.created_at else "",
                ])
            title = "Import History Audit Export"
            return self._build_tabular_export(title, headers, rows, fmt)

        else:
            # Default Summary Report
            summary = self.generate_summary(timeframe_days=timeframe_days, department_id=department_id, db=db)
            if fmt == "csv":
                return self.export_csv(summary, db)
            elif fmt == "pdf":
                return self.export_pdf(summary, db)
            else:
                return self.export_excel(summary, db)

    def _build_tabular_export(self, title: str, headers: List[str], rows: List[List[Any]], fmt: str) -> bytes:
        if fmt == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([title.upper()])
            writer.writerow([f"Exported on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
            writer.writerow([])
            writer.writerow(headers)
            for row in rows:
                writer.writerow(row)
            return output.getvalue().encode("utf-8-sig")

        elif fmt == "pdf":
            doc = fitz.open()
            page = doc.new_page()
            lines = [
                f"{title.upper()}",
                f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  |  Total Records: {len(rows)}",
                "-" * 80,
                "",
            ]
            for idx, r in enumerate(rows[:40], 1):
                summary_line = f"{idx}. " + " | ".join(str(c) for c in r[:6])
                lines.append(summary_line[:95])
            if len(rows) > 40:
                lines.append(f"... and {len(rows) - 40} additional records.")

            pdf_text = "\n".join(lines)
            page.insert_text((40, 50), pdf_text, fontsize=8.5, fontname="courier")
            stream = io.BytesIO()
            doc.save(stream)
            doc.close()
            stream.seek(0)
            return stream.getvalue()

        else:  # Excel xlsx
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Data Export"
            ws.append([title.upper()])
            ws.append([f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"])
            ws.append([])
            ws.append(headers)
            for r in rows:
                ws.append(r)
            stream = io.BytesIO()
            wb.save(stream)
            stream.seek(0)
            return stream.getvalue()

    def export_csv(self, summary: SafetyReportSummary, db: Session) -> bytes:
        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["SAFETY INTELLIGENCE EXECUTIVE SUMMARY REPORT"])
        writer.writerow(["Title", summary.report_title])
        writer.writerow(["Generated At", summary.generated_at.isoformat()])
        writer.writerow(["Timeframe", summary.timeframe])
        writer.writerow([])

        writer.writerow(["METRIC", "VALUE"])
        writer.writerow(["Total Safety Reports", summary.total_reports])
        writer.writerow(["SIF Precursors Detected", summary.sif_precursors_count])
        writer.writerow(["Active Recurring Patterns", summary.active_patterns_count])
        writer.writerow(["Active Early Warning Alerts", summary.active_alerts_count])
        writer.writerow(["Open Corrective Actions", summary.open_actions_count])
        writer.writerow(["Overdue Corrective Actions", summary.overdue_actions_count])
        writer.writerow([])

        writer.writerow(["RISK DISTRIBUTION", "COUNT"])
        for k, v in summary.risk_distribution.items():
            writer.writerow([k, v])
        writer.writerow([])

        writer.writerow(["TOP RECURRING HAZARDS", "COUNT"])
        for h in summary.top_hazards:
            writer.writerow([h.get("hazard"), h.get("count")])
        writer.writerow([])

        writer.writerow(["KEY PREVENTIVE RECOMMENDATIONS"])
        for idx, rec in enumerate(summary.key_recommendations, 1):
            writer.writerow([f"{idx}. {rec}"])

        return output.getvalue().encode("utf-8-sig")

    def export_excel(self, summary: SafetyReportSummary, db: Session) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Safety Executive Report"

        # Headers
        ws.append(["SAFETY INTELLIGENCE EXECUTIVE SUMMARY REPORT"])
        ws.append(["Title", summary.report_title])
        ws.append(["Generated At", summary.generated_at.strftime("%Y-%m-%d %H:%M:%S")])
        ws.append(["Timeframe", summary.timeframe])
        ws.append([])

        ws.append(["Key Metrics", "Value"])
        ws.append(["Total Safety Reports", summary.total_reports])
        ws.append(["SIF Precursors Detected", summary.sif_precursors_count])
        ws.append(["Active Recurring Patterns", summary.active_patterns_count])
        ws.append(["Active Early Warning Alerts", summary.active_alerts_count])
        ws.append(["Open Corrective Actions", summary.open_actions_count])
        ws.append(["Overdue Actions", summary.overdue_actions_count])
        ws.append([])

        ws.append(["Risk Level", "Report Count"])
        for k, v in summary.risk_distribution.items():
            ws.append([k, v])
        ws.append([])

        ws.append(["Top Hazard", "Report Count"])
        for h in summary.top_hazards:
            ws.append([h.get("hazard"), h.get("count")])
        ws.append([])

        ws.append(["Key Preventive Recommendations"])
        for idx, rec in enumerate(summary.key_recommendations, 1):
            ws.append([f"{idx}. {rec}"])

        # Add Active Alerts Tab
        ws_alerts = wb.create_sheet(title="Active Alerts")
        ws_alerts.append(["Alert ID", "Severity", "Title", "Risk Score", "Status", "Created At"])
        alerts = db.query(Alert).filter(Alert.status.in_(["NEW", "ACKNOWLEDGED", "IN_PROGRESS"])).all()
        for a in alerts:
            ws_alerts.append([a.alert_key, a.severity, a.title, a.risk_score, a.status, a.created_at.strftime("%Y-%m-%d %H:%M")])

        # Add Corrective Actions Tab
        ws_actions = wb.create_sheet(title="Corrective Actions")
        ws_actions.append(["Action Number", "Priority", "Title", "Status", "Due Date", "Assignee"])
        actions = db.query(CorrectiveAction).all()
        for act in actions:
            assignee = act.assignee.name if act.assignee else "Unassigned"
            due_str = act.due_date.strftime("%Y-%m-%d") if act.due_date else "None"
            ws_actions.append([act.action_number, act.priority, act.title, act.status, due_str, assignee])

        stream = io.BytesIO()
        wb.save(stream)
        stream.seek(0)
        return stream.getvalue()

    def export_pdf(self, summary: SafetyReportSummary, db: Session) -> bytes:
        doc = fitz.open()
        page = doc.new_page()

        pdf_lines = [
            f"SAFETY INTELLIGENCE EXECUTIVE SUMMARY REPORT",
            f"Title: {summary.report_title}",
            f"Generated: {summary.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}  |  Timeframe: {summary.timeframe}",
            "-" * 75,
            "",
            "1. EXECUTIVE SUMMARY & KEY METRICS",
            f"   • Total Safety Reports Logged: {summary.total_reports}",
            f"   • SIF Precursors Flagged:      {summary.sif_precursors_count}",
            f"   • Active Recurring Patterns:   {summary.active_patterns_count}",
            f"   • Active Early Warning Alerts: {summary.active_alerts_count}",
            f"   • Open Corrective Actions:     {summary.open_actions_count} (Overdue: {summary.overdue_actions_count})",
            "",
            "2. RISK DISTRIBUTION",
        ]

        for lvl, cnt in summary.risk_distribution.items():
            pdf_lines.append(f"   • {lvl:<10}: {cnt} incident(s)")

        pdf_lines.append("")
        pdf_lines.append("3. TOP RECURRING HAZARD CONCENTRATIONS")
        for h in summary.top_hazards:
            pdf_lines.append(f"   • {h.get('hazard'):<25}: {h.get('count')} reports")

        pdf_lines.append("")
        pdf_lines.append("4. STRATEGIC PREVENTIVE RECOMMENDATIONS")
        for idx, rec in enumerate(summary.key_recommendations, 1):
            pdf_lines.append(f"   {idx}. {rec}")

        pdf_text = "\n".join(pdf_lines)
        page.insert_text((40, 50), pdf_text, fontsize=9.5, fontname="courier")

        stream = io.BytesIO()
        doc.save(stream)
        doc.close()
        stream.seek(0)
        return stream.getvalue()


report_export_service = ReportExportService()
