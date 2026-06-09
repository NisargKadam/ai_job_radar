import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import config


class Base(DeclarativeBase):
    pass


def _db_url() -> str:
    # Read live so tests can point at a temp DB via the AIJR_DB_URL env var.
    return os.environ.get("AIJR_DB_URL", config.aijr_db_url)


engine = create_engine(_db_url(), connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables and ensure the singleton SettingsRow exists.

    Rebinds the engine to the current AIJR_DB_URL on every call so test
    isolation (a fresh temp DB per test) works.
    """
    global engine
    engine = create_engine(_db_url(), connect_args={"check_same_thread": False})
    SessionLocal.configure(bind=engine)

    from app.db import models  # noqa: F401  (register mappers)

    Base.metadata.create_all(engine)
    with SessionLocal() as s:
        if s.query(models.SettingsRow).count() == 0:
            s.add(models.SettingsRow())
            s.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
