"""Proyecto 077 — API.

El esquema de la base lo crean backend/02_crear_esquema.sql y los scripts 03 y 04
(SRS, 4.3 y 4.4); la aplicación no crea tablas.

`crear_app(config)` arma la aplicación. `app` es perezosa (PEP 562): se crea con
`cargar_config()` la primera vez que alguien la pide, así que `fastapi dev app/main.py` y
`uvicorn app.main:app` funcionan, e importar este módulo no lee backend/.env.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.config import Settings, cargar_config
from app.db import comprobar_base, crear_fabrica, crear_motor_bd
from app.errores import importar_si_existe, registrar_manejadores

# Cada módulo expone `router: APIRouter`; si aún no existe, se omite.
MODULOS_DE_RUTAS = (
    "app.api.rutas_cuentas",
    "app.api.rutas_portafolios",
    "app.api.rutas_transacciones",
    "app.api.rutas_consultas",
)


def _bajo_api(ruta: str) -> bool:
    return ruta == "/api" or ruta.startswith("/api/")


class MiddlewareSinCache:
    """`Cache-Control: no-store` en toda respuesta bajo /api (D-43)."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or not _bajo_api(scope.get("path", "")):
            await self.app(scope, receive, send)
            return

        async def enviar(mensaje: Message) -> None:
            if mensaje["type"] == "http.response.start":
                cabeceras = [(k, v) for k, v in mensaje.get("headers", []) if k.lower() != b"cache-control"]
                cabeceras.append((b"cache-control", b"no-store"))
                mensaje = {**mensaje, "headers": cabeceras}
            await send(mensaje)

        await self.app(scope, receive, enviar)


def crear_app(config: Settings | None = None) -> FastAPI:
    """Crea la aplicación con su Engine, sus manejadores, sus middlewares y sus rutas."""
    if config is None:
        config = cargar_config()
    engine = crear_motor_bd(config)

    @asynccontextmanager
    async def ciclo_de_vida(_: FastAPI) -> AsyncIterator[None]:
        await run_in_threadpool(comprobar_base, engine)
        try:
            yield
        finally:
            engine.dispose()

    # Comprobación de Origin en todo método que escribe (D-41); la define WP3.
    dependencias: list[Any] = []
    dependencias_cuentas = importar_si_existe("app.cuentas.dependencias")
    if dependencias_cuentas is not None:
        dependencias.append(Depends(dependencias_cuentas.verificar_origen))

    app = FastAPI(
        title="Proyecto 077 — Plataforma de Gestión de Activos Financieros",
        version="0.1.0",
        lifespan=ciclo_de_vida,
        dependencies=dependencias,
    )
    app.state.config = config
    app.state.engine = engine
    app.state.fabrica_sesiones = crear_fabrica(engine)

    registrar_manejadores(app)  # primero: su middleware del 500 queda dentro de los demás
    app.add_middleware(MiddlewareSinCache)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.lista_origenes,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health", tags=["diagnóstico"])
    def health() -> dict[str, str]:
        """Comprueba que la API responde, sin tocar la base de datos."""
        return {"estado": "ok"}

    for nombre in MODULOS_DE_RUTAS:
        modulo = importar_si_existe(nombre)
        if modulo is not None:
            app.include_router(modulo.router)

    return app


_app: FastAPI | None = None


def __getattr__(nombre: str) -> Any:
    """`app` perezosa (PEP 562): se crea una sola vez, al pedirla."""
    global _app
    if nombre == "app":
        if _app is None:
            _app = crear_app(cargar_config())
        return _app
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def __dir__() -> list[str]:
    return sorted([*globals(), "app"])
