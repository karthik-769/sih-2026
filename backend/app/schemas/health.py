from typing import Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Overall service status")


class SystemHealthDetails(BaseModel):
    status: str = Field("ok", description="Overall service status")
    environment: str = Field("development", description="Current runtime environment")
    version: str = Field("0.1.0", description="API version")
    database_connected: bool = Field(False, description="PostgreSQL database connectivity status")
