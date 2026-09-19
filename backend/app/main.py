"""Proyecto 077 — API.

Prueba de extremo a extremo: PostgreSQL -> FastAPI -> navegador.
La tabla `ping` es desechable; se elimina cuando exista el esquema real
derivado del modelo entidad-relación del SRS.
"""

from datetime import datetime
from decimal import Decimal
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_serializer
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_session

app = FastAPI(
    title="Proyecto 077 — Plataforma de Gestión de Activos Financieros",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.lista_origenes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Ping(BaseModel):
    id: int
    mensaje: str
    monto: Decimal
    creado_en: datetime

    @field_serializer("monto")
    def serializar_monto(self, valor: Decimal) -> str:
        """Los importes viajan como cadena, no como número.

        JSON no distingue enteros de flotantes, y un `numeric(20,4)` convertido
        a float pierde precisión. Serializarlo como texto conserva los decimales
        exactos de extremo a extremo.
        """
        return format(valor, "f")


@app.get("/health", tags=["diagnóstico"])
def health() -> dict[str, str]:
    """Comprueba que la API responde, sin tocar la base de datos."""
    return {"estado": "ok"}


@app.get("/api/ping", response_model=list[Ping], tags=["diagnóstico"])
def leer_ping(sesion: Annotated[Session, Depends(get_session)]) -> list[Ping]:
    """Lee la tabla de prueba y demuestra la cadena completa."""
    filas = (
        sesion.execute(
            text("SELECT id, mensaje, monto, creado_en FROM ping ORDER BY id")
        )
        .mappings()
        .all()
    )
    return [Ping.model_validate(dict(fila)) for fila in filas]
