"""Database engine and session management for ChangePilot."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.config import settings
from backend.src.database.models import Base

logger = logging.getLogger("changepilot.database.session")

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info(f"Database schema initialized ({settings.database_url})")
    except Exception as e:
        logger.warning(f"Database init warning (non-fatal): {e}")


def get_db():
    """FastAPI database session dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
