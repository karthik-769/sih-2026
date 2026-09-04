from fastapi import APIRouter
from app.api.v1.endpoints import (
    health,
    auth,
    users,
    departments,
    locations,
    reports,
    imports,
    patterns,
    alerts,
    corrective_actions,
    analytics,
    reporting,
    audit_logs,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(users.router, tags=["User Management"])
api_router.include_router(departments.router, tags=["Departments"])
api_router.include_router(locations.router, tags=["Locations"])
api_router.include_router(reports.router, prefix="/reports", tags=["Safety Reports"])
api_router.include_router(imports.router, prefix="/imports", tags=["Bulk Safety Report Importer"])
api_router.include_router(patterns.router, prefix="/patterns", tags=["Safety Patterns"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["Early Warning Alerts"])
api_router.include_router(corrective_actions.router, prefix="/corrective-actions", tags=["Corrective Actions"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Advanced Safety Analytics"])
api_router.include_router(reporting.router, prefix="/reporting", tags=["Reporting & Export"])
api_router.include_router(audit_logs.router, tags=["Audit Logs"])


