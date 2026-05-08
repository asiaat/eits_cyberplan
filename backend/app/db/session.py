from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from functools import lru_cache

from app.core.config import get_settings


@lru_cache()
def get_engine():
    """Lazy initialization of database engine."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False,
    )


@lru_cache()
def get_session_maker():
    """Get session maker from engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


Base = declarative_base()


def get_db():
    """Get database session."""
    SessionLocal = get_session_maker()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class _SessionLocalProxy:
    """Lazy proxy for SessionLocal to avoid eager initialization."""
    def __call__(self, *args, **kwargs):
        return get_session_maker()(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(get_session_maker(), name)


SessionLocal = _SessionLocalProxy()