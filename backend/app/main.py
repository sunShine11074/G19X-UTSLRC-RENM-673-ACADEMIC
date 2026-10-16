"""Proyecto 077 — API.

El esquema de la base lo crea backend/02_crear_esquema.sql (SRS, 4.3 y 4.4).
La tabla de prueba `ping` se eliminó con él, junto con /api/ping.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

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


@app.get("/health", tags=["diagnóstico"])
def health() -> dict[str, str]:
    """Comprueba que la API responde, sin tocar la base de datos."""
    return {"estado": "ok"}

