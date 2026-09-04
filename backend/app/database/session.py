import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base model class
Base = declarative_base()


def get_sqlite_fallback_url() -> str:
    """
    Returns a unified SQLite database URL whether running from root or backend directory.
    """
    from pathlib import Path
    backend_dir = Path(__file__).resolve().parent.parent.parent
    db_file = backend_dir / "safety_intelligence.db"
    return f"sqlite:///{db_file.as_posix()}"


def create_db_engine():
    """
    Creates the SQLAlchemy database engine with automatic fallback for local development.
    """
    db_url = settings.sync_database_url
    try:
        if db_url.startswith("sqlite"):
            return create_engine(db_url, connect_args={"check_same_thread": False})
        
        # Test connecting to PostgreSQL
        eng = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=10,
            max_overflow=20,
        )
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected successfully to PostgreSQL database: {settings.POSTGRES_DB}")
        return eng
    except Exception as e:
        if settings.USE_SQLITE_DEV_FALLBACK and settings.ENVIRONMENT == "development":
            fallback_url = get_sqlite_fallback_url()
            logger.warning(
                f"PostgreSQL connection to {db_url} failed ({e}). "
                f"Falling back to local development SQLite database: {fallback_url}"
            )
            return create_engine(fallback_url, connect_args={"check_same_thread": False})
        logger.error(f"Failed to connect to database: {e}")
        raise e


engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    FastAPI dependency that provides a transactional database session per request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Utility to verify database connectivity.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error during database connection check: {e}")
        return False
