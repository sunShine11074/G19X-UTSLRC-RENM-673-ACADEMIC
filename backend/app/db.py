"""Conexión a PostgreSQL y gestión de sesiones."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_session() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: abre una sesión y la cierra al terminar."""
    with SessionLocal() as sesion:
        yield sesion
