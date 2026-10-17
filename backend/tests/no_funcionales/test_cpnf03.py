"""CPNF-03: acceso solo a lo propio en toda la API (RNF-03; RF-02; RD-01; RD-02; §4.1; §8.4).

Recorre `app.openapi()["paths"]`:
- Las rutas públicas son una lista blanca (§4.1); todas las demás llevan `security`.
- Cada operación con `security` tiene un cuerpo de ejemplo en `EJEMPLOS`: una operación sin
  ejemplo hace fallar la prueba, así que la cobertura es del 100 %.
- Sin cookie: 401.
- Con la cookie de A sobre los ids de B, en la ruta y en el cuerpo: 404 con el mismo cuerpo,
  byte a byte, que con el id inexistente 2**62.
- La huella de la base (conteo y md5 de las 5 tablas de cuenta), tomada por el dueño, no cambia.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI
from psycopg import sql

from tests.conftest import TABLAS_DE_CUENTA, ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.no_funcional, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
INEXISTENTE = 2**62
RUTAS_PUBLICAS = frozenset(
    {
        ("GET", "/health"),
        ("GET", "/api/aviso-privacidad"),
        ("POST", "/api/cuentas"),
        ("POST", "/api/sesion"),
        ("DELETE", "/api/sesion"),
    }
)
PARAMETRO_PORTAFOLIO = "{portafolio_id}"
SEGURIDAD = [{"sesion_077": []}]


@dataclass(frozen=True)
class Datos:
    """Ids y nombres de una cuenta, para armar rutas y cuerpos."""

    portafolio: int
    nombre_portafolio: str
    intermediario: int
    instrumento: int


@dataclass(frozen=True)
class Ejemplo:
    """Cuerpo de ejemplo de una operación y los campos del cuerpo que son ids de recursos propios."""

    cuerpo: Callable[[Datos], dict[str, Any] | None] = lambda _: None
    ids_cuerpo: tuple[str, ...] = field(default=())


def _transaccion(d: Datos) -> dict[str, Any]:
    return {
        "intermediario_id": d.intermediario,
        "instrumento_id": d.instrumento,
        "tipo": "compra",
        "fecha_concertacion": "2026-09-15",
        "cantidad": "1",
        "precio": "104.00",
        "importe_comisiones": "0.00",
    }


# Una entrada por operación con sesión. Si se agrega una ruta, esta tabla debe crecer.
EJEMPLOS: dict[tuple[str, str], Ejemplo] = {
    ("GET", "/api/cuenta"): Ejemplo(),
    ("POST", "/api/cuenta/revocacion"): Ejemplo(lambda d: {"confirmo": True}),
    ("GET", "/api/instrumentos"): Ejemplo(),
    ("GET", "/api/intermediarios"): Ejemplo(),
    ("POST", "/api/intermediarios"): Ejemplo(lambda d: {"nombre": "Casa nueva"}),
    ("GET", "/api/portafolios"): Ejemplo(),
    ("POST", "/api/portafolios"): Ejemplo(lambda d: {"nombre": "Portafolio nuevo"}),
    ("GET", "/api/portafolios/{portafolio_id}"): Ejemplo(),
    ("PATCH", "/api/portafolios/{portafolio_id}"): Ejemplo(lambda d: {"nombre": "Renombrado"}),
    ("DELETE", "/api/portafolios/{portafolio_id}"): Ejemplo(lambda d: {"confirmacion": d.nombre_portafolio}),
    ("GET", "/api/portafolios/{portafolio_id}/transacciones"): Ejemplo(),
    ("POST", "/api/portafolios/{portafolio_id}/transacciones"): Ejemplo(_transaccion, ("intermediario_id",)),
    ("GET", "/api/intervalo-datos"): Ejemplo(),
    ("GET", "/api/portafolios/{portafolio_id}/posiciones"): Ejemplo(),
    ("GET", "/api/portafolios/{portafolio_id}/tablero"): Ejemplo(),
}


def _huella(dueno: psycopg.Connection[Any]) -> dict[str, tuple[int, str]]:
    resultado: dict[str, tuple[int, str]] = {}
    for tabla in TABLAS_DE_CUENTA:
        fila = dueno.execute(
            sql.SQL("SELECT count(*), md5(coalesce(string_agg(t::text, E'\\n' ORDER BY t.id), '')) FROM {} t").format(
                sql.Identifier(tabla)
            )
        ).fetchone()
        assert fila is not None
        resultado[tabla] = (int(fila[0]), str(fila[1]))
    return resultado


def _operaciones(app: FastAPI) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (metodo.upper(), ruta): operacion
        for ruta, operaciones in app.openapi()["paths"].items()
        for metodo, operacion in operaciones.items()
    }


def _preparar(cuenta: CuentaPrueba, nombre: str) -> Datos:
    c = cuenta.cliente
    portafolio = c.post("/api/portafolios", json={"nombre": nombre})
    intermediario = c.post("/api/intermediarios", json={"nombre": "Casa A"})
    assert (portafolio.status_code, intermediario.status_code) == (201, 201)
    instrumento = next(i["id"] for i in c.get("/api/instrumentos").json() if i["clave"] == "DEMOACC")
    datos = Datos(portafolio.json()["id"], nombre, intermediario.json()["id"], instrumento)
    registro = c.post(f"/api/portafolios/{datos.portafolio}/transacciones", json=_transaccion(datos))
    assert registro.status_code == 201, registro.json()
    return datos


def _ruta(plantilla: str, portafolio: int) -> str:
    return plantilla.replace(PARAMETRO_PORTAFOLIO, str(portafolio))


def test_rutas_publicas_y_ejemplos_cubren_toda_la_api(app_pruebas: FastAPI) -> None:
    operaciones = _operaciones(app_pruebas)
    assert RUTAS_PUBLICAS <= set(operaciones)
    for clave, operacion in operaciones.items():
        if clave in RUTAS_PUBLICAS:
            assert "security" not in operacion, clave
        else:
            assert operacion.get("security") == SEGURIDAD, clave
    con_sesion = set(operaciones) - RUTAS_PUBLICAS
    sin_ejemplo = sorted(con_sesion - set(EJEMPLOS))
    assert not sin_ejemplo, f"Operaciones con sesión sin cuerpo de ejemplo en EJEMPLOS: {sin_ejemplo}"
    assert not sorted(set(EJEMPLOS) - con_sesion), "EJEMPLOS tiene operaciones que ya no existen"
    # Los únicos parámetros de ruta son ids de portafolio: si aparece otro, hay que ampliar la prueba.
    for _, ruta in con_sesion:
        assert set(re.findall(r"\{[^}]+\}", ruta)) <= {PARAMETRO_PORTAFOLIO}, ruta


def test_sin_cookie_401_y_lo_ajeno_404_como_lo_inexistente(
    app_pruebas: FastAPI,
    nueva_cuenta: Callable[..., CuentaPrueba],
    cliente: ClientePrueba,
    dueno: psycopg.Connection[Any],
    reloj: Any,
) -> None:
    reloj.fijar_hoy(HOY)
    cuenta_a, cuenta_b = nueva_cuenta(), nueva_cuenta()
    a, b = _preparar(cuenta_a, "Principal A"), _preparar(cuenta_b, "Principal B")
    c = cuenta_a.cliente
    operaciones = sorted(set(_operaciones(app_pruebas)) - RUTAS_PUBLICAS)
    assert len(operaciones) == len(EJEMPLOS)
    antes = _huella(dueno)

    revisadas_404 = 0
    for metodo, plantilla in operaciones:
        ejemplo = EJEMPLOS[(metodo, plantilla)]

        # Sin cookie (el cliente sí manda Origin): 401, sin tocar nada.
        sin_cookie = cliente.request(metodo, _ruta(plantilla, b.portafolio), json=ejemplo.cuerpo(b))
        assert sin_cookie.status_code == 401, (metodo, plantilla, sin_cookie.status_code)
        assert sin_cookie.json()["codigo"] == "sesion_requerida", (metodo, plantilla)

        # Con la cookie de A, el portafolio de B en la ruta y los ids de B en el cuerpo.
        if PARAMETRO_PORTAFOLIO in plantilla:
            ajeno = c.request(metodo, _ruta(plantilla, b.portafolio), json=ejemplo.cuerpo(b))
            inexistente = c.request(metodo, _ruta(plantilla, INEXISTENTE), json=ejemplo.cuerpo(b))
            assert ajeno.status_code == 404, (metodo, plantilla, ajeno.status_code)
            assert ajeno.content == inexistente.content, (metodo, plantilla)
            revisadas_404 += 1

        # Con la cookie de A, su propio portafolio y los ids de B en el cuerpo.
        if ejemplo.ids_cuerpo:
            cuerpo_b = {**ejemplo.cuerpo(a), **{k: getattr(b, k.removesuffix("_id")) for k in ejemplo.ids_cuerpo}}
            cuerpo_x = {**ejemplo.cuerpo(a), **dict.fromkeys(ejemplo.ids_cuerpo, INEXISTENTE)}
            ajeno = c.request(metodo, _ruta(plantilla, a.portafolio), json=cuerpo_b)
            inexistente = c.request(metodo, _ruta(plantilla, a.portafolio), json=cuerpo_x)
            assert ajeno.status_code == 404, (metodo, plantilla, ajeno.status_code)
            assert ajeno.content == inexistente.content, (metodo, plantilla)
            revisadas_404 += 1

    assert revisadas_404 == 8  # 7 operaciones con portafolio en la ruta y 1 con intermediario en el cuerpo
    assert _huella(dueno) == antes
    # A y B siguen con lo suyo.
    for cuenta, datos in ((cuenta_a, a), (cuenta_b, b)):
        respuesta: httpx.Response = cuenta.cliente.get(f"/api/portafolios/{datos.portafolio}")
        assert (respuesta.status_code, respuesta.json()["nombre"]) == (200, datos.nombre_portafolio)
