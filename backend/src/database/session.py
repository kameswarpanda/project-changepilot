"""Database engine and session management for ChangePilot."""
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.src.config import settings
from backend.src.database.models import Base

logger = logging.getLogger("changepilot.database.session")

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # PostgreSQL / Cloud SQL settings
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 15,
        "pool_recycle": 1800
    })

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    **engine_kwargs
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
