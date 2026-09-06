import logging
from app.main import app
from app.core.config import settings
from app.database.init_db import init_database

logger = logging.getLogger(__name__)

# Ensure tables and seed users exist for serverless requests
try:
    init_database(seed=settings.SEED_DEMO_DATA)
except Exception as e:
    logger.warning("Vercel serverless init_database notice: %s", e)

__all__ = ["app"]