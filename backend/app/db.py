"""Conexión a PostgreSQL y sesiones de SQLAlchemy (§3.2).

Reglas de todo el backend (§3.2 y §3.6): sin `metadata.create_all()`, sin `session.merge`,
sin `relationship()` de escritura, sin `Sequence()`, sin `default=`/`onupdate=` de Python en
las columnas con valor de la base, y sin `FOR UPDATE` sin `OF`. Aislamiento READ COMMITTED,
el de PostgreSQL por omisión (RF-28 depende de él).
"""

from collections.abc import Iterator

from fastapi import Request
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.config import Settings

ZONA_BASE = "America/Mexico_City"


def crear_motor_bd(config: Settings) -> Engine:
    """Crea el Engine sin eco y sin parámetros en los errores (RNF-04; RNF-05)."""
    return create_engine(
        config.database_url.get_secret_value(),
        pool_pre_ping=True,
        hide_parameters=True,
    )


def crear_fabrica(engine: Engine) -> sessionmaker[Session]:
    """Fábrica de sesiones; cada servicio que escribe termina con `sesion.commit()`."""
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def obtener_sesion(request: Request) -> Iterator[Session]:
    """Dependencia de FastAPI: una sesión por solicitud; al cerrar sin commit, se deshace."""
    with request.app.state.fabrica_sesiones() as sesion:
        yield sesion


def comprobar_base(engine: Engine) -> None:
    """Comprueba al arrancar que el rol no sea superusuario y que la zona sea la de la Ciudad de México.

    Los mensajes no incluyen la URL de la base (RNF-05).
    """
    with engine.connect() as conexion:
        es_superusuario = conexion.execute(
            text("SELECT rolsuper FROM pg_roles WHERE rolname = current_user")
        ).scalar_one()
        zona = conexion.execute(text("SELECT current_setting('TimeZone')")).scalar_one()
    if es_superusuario:
        raise RuntimeError(
            "DATABASE_URL usa un rol superusuario; la API se conecta solo con app_077 (4.3)."
        )
    if zona != ZONA_BASE:
        raise RuntimeError(
            f"La zona horaria de la sesión de la base es {zona}, no {ZONA_BASE} (RD-15); "
            "ejecuta 02_crear_esquema.sql en la base de DATABASE_URL."
        )
