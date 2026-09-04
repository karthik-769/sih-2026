import logging
from sqlalchemy import text
from app.database.session import Base, engine, SessionLocal
from app.database.seed import seed_database
# Import models to ensure they are registered with Base metadata
import app.models  # noqa: F401

logger = logging.getLogger(__name__)


def migrate_sqlite_columns() -> None:
    """
    Safely adds newly added model columns to existing SQLite tables if not present.
    """
    try:
        if engine.dialect.name != "sqlite":
            return

        with engine.connect() as conn:
            # Check ai_analyses table columns
            result = conn.execute(text("PRAGMA table_info(ai_analyses)")).fetchall()
            if result:
                existing_cols = {row[1] for row in result}
                
                new_columns = [
                    ("status", "VARCHAR(50) NOT NULL DEFAULT 'COMPLETED'"),
                    ("model_name", "VARCHAR(100) NOT NULL DEFAULT 'safety-intelligence-nlp-v1'"),
                    ("sif_precursor", "BOOLEAN NOT NULL DEFAULT 0"),
                    ("sif_categories", "JSON NOT NULL DEFAULT '[]'"),
                    ("highlighted_evidence", "JSON NOT NULL DEFAULT '[]'"),
                    ("similar_incidents", "JSON NOT NULL DEFAULT '{}'"),
                    ("embedding", "JSON"),
                ]

                for col_name, col_type in new_columns:
                    if col_name not in existing_cols:
                        logger.info(f"Adding missing column '{col_name}' to 'ai_analyses' table...")
                        conn.execute(text(f"ALTER TABLE ai_analyses ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

            # Check safety_reports table columns
            sr_result = conn.execute(text("PRAGMA table_info(safety_reports)")).fetchall()
            if sr_result:
                existing_sr_cols = {row[1] for row in sr_result}
                sr_new_columns = [
                    ("source_type", "VARCHAR(50) NOT NULL DEFAULT 'MANUAL'"),
                    ("source_file", "VARCHAR(255)"),
                    ("source_row", "INTEGER"),
                    ("source_page", "INTEGER"),
                    ("import_batch_id", "INTEGER"),
                ]
                for col_name, col_type in sr_new_columns:
                    if col_name not in existing_sr_cols:
                        logger.info(f"Adding missing column '{col_name}' to 'safety_reports' table...")
                        conn.execute(text(f"ALTER TABLE safety_reports ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

            # Check import_batches table columns
            ib_result = conn.execute(text("PRAGMA table_info(import_batches)")).fetchall()
            if ib_result:
                existing_ib_cols = {row[1] for row in ib_result}
                ib_new_columns = [
                    ("failed_records", "INTEGER NOT NULL DEFAULT 0"),
                    ("error_records", "INTEGER NOT NULL DEFAULT 0"),
                    ("ai_completed_records", "INTEGER NOT NULL DEFAULT 0"),
                    ("ai_failed_records", "INTEGER NOT NULL DEFAULT 0"),
                ]
                for col_name, col_type in ib_new_columns:
                    if col_name not in existing_ib_cols:
                        logger.info(f"Adding missing column '{col_name}' to 'import_batches' table...")
                        conn.execute(text(f"ALTER TABLE import_batches ADD COLUMN {col_name} {col_type}"))
                        conn.commit()

            # Migrate legacy roles (SUPERVISOR, SAFETY_OFFICER) to ADMIN safely
            users_check = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")).fetchone()
            if users_check:
                migrated = conn.execute(text("UPDATE users SET role = 'ADMIN' WHERE role IN ('SUPERVISOR', 'SAFETY_OFFICER')"))
                conn.commit()
                if migrated.rowcount > 0:
                    logger.info(f"Migrated {migrated.rowcount} legacy user(s) to ADMIN role.")
    except Exception as e:
        logger.warning(f"SQLite column/data migration check note: {e}")


def init_database(seed: bool = True) -> None:
    """
    Creates all database tables based on SQLAlchemy models and optionally seeds demo data.
    """
    logger.info("Initializing database schema...")
    Base.metadata.create_all(bind=engine)
    migrate_sqlite_columns()
    logger.info("Database schema and migrations verified.")

    if seed:
        db = SessionLocal()
        try:
            seed_database(db)
        finally:
            db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_database(seed=True)
