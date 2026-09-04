from fastapi import APIRouter
from app.schemas.health import HealthResponse, SystemHealthDetails
from app.database.session import check_db_connection
from app.core.config import settings

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service Health Check",
    description="Returns standard operational health status.",
)
def get_health() -> HealthResponse:
    """
    Standard health check endpoint returning { 'status': 'ok' }.
    """
    return HealthResponse(status="ok")


@router.get(
    "/health/details",
    response_model=SystemHealthDetails,
    summary="System Health Diagnostics",
    description="Returns detailed operational metrics including DB connectivity.",
)
def get_health_details() -> SystemHealthDetails:
    """
    Detailed diagnostics including database connection status.
    """
    db_ok = check_db_connection()
    return SystemHealthDetails(
        status="ok" if db_ok else "degraded",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        database_connected=db_ok,
    )
