import logging
from typing import Generator
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from app.core.config import settings

logger = logging.getLogger(__name__)

# Base model class
Base = declarative_base()


def get_sqlite_fallback_url() -> str:
    """
    Returns a unified SQLite database URL whether running from root, backend, or Vercel serverless (/tmp).
    """
    import os
    from pathlib import Path

    if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        return "sqlite:////tmp/safety_intelligence.db"

    backend_dir = Path(__file__).resolve().parent.parent.parent
    db_file = backend_dir / "safety_intelligence.db"
    return f"sqlite:///{db_file.as_posix()}"


def ensure_schema_columns(eng):
    """
    Safe schema evolution helper for local SQLite development and PostgreSQL.
    Ensures newly introduced domain columns exist without requiring destructive table drops.
    """
    try:
        inspector = inspect(eng)
        table_names = inspector.get_table_names()

        # Columns to ensure in safety_reports
        if "safety_reports" in table_names:
            cols = {c["name"] for c in inspector.get_columns("safety_reports")}
            new_cols = [
                ("activity", "VARCHAR(100)"),
                ("activity_category", "VARCHAR(100)"),
                ("site", "VARCHAR(100)"),
                ("field", "VARCHAR(100)"),
                ("installation", "VARCHAR(100)"),
                ("actual_consequence", "VARCHAR(100) DEFAULT 'No injury'"),
                ("potential_consequence", "VARCHAR(255)"),
                ("fatality_potential", "BOOLEAN DEFAULT 0"),
                ("life_saving_rule", "VARCHAR(100)"),
            ]
            with eng.connect() as conn:
                for col_name, col_type in new_cols:
                    if col_name not in cols:
                        try:
                            conn.execute(text(f"ALTER TABLE safety_reports ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logger.info(f"Added column {col_name} to safety_reports")
                        except Exception as ce:
                            logger.debug(f"Column {col_name} note: {ce}")

        # Columns to ensure in ai_analyses
        if "ai_analyses" in table_names:
            cols = {c["name"] for c in inspector.get_columns("ai_analyses")}
            new_cols = [
                ("activity", "VARCHAR(100)"),
                ("activity_category", "VARCHAR(100)"),
                ("activity_confidence", "FLOAT DEFAULT 0.85"),
                ("life_saving_rule", "VARCHAR(100)"),
                ("life_saving_rule_confidence", "FLOAT DEFAULT 0.85"),
                ("life_saving_rule_evidence", "JSON DEFAULT '[]'"),
                ("failed_barriers", "JSON DEFAULT '[]'"),
                ("actual_consequence", "VARCHAR(100) DEFAULT 'No injury'"),
                ("potential_consequence", "VARCHAR(255) DEFAULT ''"),
                ("potential_consequence_severity", "VARCHAR(50) DEFAULT 'NONE'"),
                ("fatality_potential", "BOOLEAN DEFAULT 0"),
                ("sif_reasoning", "TEXT DEFAULT ''"),
                ("evidence_snippets", "JSON DEFAULT '[]'"),
                ("review_status", "VARCHAR(50) DEFAULT 'PENDING'"),
                ("reviewed_by", "INTEGER"),
                ("reviewed_at", "DATETIME"),
                ("original_ai_decision", "JSON"),
                ("final_hse_decision", "JSON"),
                ("review_comment", "TEXT"),
            ]
            with eng.connect() as conn:
                for col_name, col_type in new_cols:
                    if col_name not in cols:
                        try:
                            conn.execute(text(f"ALTER TABLE ai_analyses ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logger.info(f"Added column {col_name} to ai_analyses")
                        except Exception as ce:
                            logger.debug(f"Column {col_name} note: {ce}")

        # Columns to ensure in patterns
        if "patterns" in table_names:
            cols = {c["name"] for c in inspector.get_columns("patterns")}
            new_cols = [
                ("activity", "VARCHAR(100)"),
                ("activity_category", "VARCHAR(100)"),
                ("life_saving_rule", "VARCHAR(100)"),
                ("failed_barriers", "JSON DEFAULT '[]'"),
                ("sif_density", "FLOAT DEFAULT 0.0"),
            ]
            with eng.connect() as conn:
                for col_name, col_type in new_cols:
                    if col_name not in cols:
                        try:
                            conn.execute(text(f"ALTER TABLE patterns ADD COLUMN {col_name} {col_type}"))
                            conn.commit()
                            logger.info(f"Added column {col_name} to patterns")
                        except Exception as ce:
                            logger.debug(f"Column {col_name} note: {ce}")
    except Exception as e:
        logger.debug(f"Schema column ensure note: {e}")


def create_db_engine():
    """
    Creates the SQLAlchemy database engine with automatic fallback for local development.
    """
    db_url = settings.sync_database_url
    try:
        if db_url.startswith("sqlite"):
            eng = create_engine(db_url, connect_args={"check_same_thread": False})
            ensure_schema_columns(eng)
            return eng
        
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
        ensure_schema_columns(eng)
        logger.info(f"Connected successfully to PostgreSQL database: {settings.POSTGRES_DB}")
        return eng
    except Exception as e:
        if settings.USE_SQLITE_DEV_FALLBACK and settings.ENVIRONMENT == "development":
            fallback_url = get_sqlite_fallback_url()
            logger.warning(
                f"PostgreSQL connection to {db_url} failed ({e}). "
                f"Falling back to local development SQLite database: {fallback_url}"
            )
            eng = create_engine(fallback_url, connect_args={"check_same_thread": False})
            ensure_schema_columns(eng)
            return eng
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
