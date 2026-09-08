"""Database engine, session management, and backup utilities."""

from datetime import datetime
from pathlib import Path
import shutil
import sqlite3
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.config import settings

# Engine configuration
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency for obtaining a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Initializes tables in the configured database."""
    settings.init_storage_dirs()
    # Import all models so metadata is populated
    import backend.app.db.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


def backup_database(backup_dir: Path = Path("./data/backups")) -> Path:
    """
    Performs a safe, non-blocking online backup of the SQLite database.
    If using another dialect (PostgreSQL), creates a timestamped schema snapshot indication.
    """
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if settings.database_url.startswith("sqlite"):
        db_path_str = settings.database_url.replace("sqlite:///", "")
        db_path = Path(db_path_str)
        if not db_path.exists():
            # If DB file doesn't exist yet, init it
            init_db()

        target_file = backup_dir / f"signalinsight_backup_{timestamp}.db"
        # Use sqlite3 online backup API to ensure ACID consistency without locks
        src_conn = sqlite3.connect(str(db_path))
        dst_conn = sqlite3.connect(str(target_file))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        return target_file
    else:
        # Non-sqlite stub/documentation
        info_file = backup_dir / f"postgres_backup_instructions_{timestamp}.txt"
        info_file.write_text(f"For PostgreSQL, invoke: pg_dump -U user -d db > {backup_dir}/backup.sql")
        return info_file
