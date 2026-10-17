"""CPF-28: el saldo por intermediario no queda negativo (RF-28; CU-12; X-06; §4.3 E18 paso 10; §8.3).

Incluye la prueba de concurrencia (R-12): con `FOR UPDATE OF portafolio`, de dos ventas
simultáneas que juntas dejarían el saldo negativo, solo una pasa.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from tests.conftest import ClientePrueba, ClusterPg, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

NOMBRE_COOKIE = "sesion_077"


def _id(respuesta: httpx.Response, estado: int = 201) -> int:
    assert respuesta.status_code == estado, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _conteo(dueno: psycopg.Connection[Any]) -> int:
    fila = dueno.execute("SELECT count(*) FROM transaccion").fetchone()
    assert fila is not None
    return int(fila[0])


class Escenario:
    """Una cuenta con «Principal», «Secundario», «Casa A», «Casa B» y DEMOACC."""

    def __init__(self, cuenta: CuentaPrueba) -> None:
        self.cuenta = cuenta
        self.c = cuenta.cliente
        self.principal = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.secundario = _id(self.c.post("/api/portafolios", json={"nombre": "Secundario"}))
        self.casa_a = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.casa_b = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa B"}))
        self.demoacc = next(i["id"] for i in self.c.get("/api/instrumentos").json() if i["clave"] == "DEMOACC")

    def cuerpo(self, tipo: str, fecha: str, cantidad: int, casa: int) -> dict[str, Any]:
        return {
            "intermediario_id": casa,
            "instrumento_id": self.demoacc,
            "tipo": tipo,
            "fecha_concertacion": fecha,
            "cantidad": str(cantidad),
            "precio": "100.00",
            "importe_comisiones": "1.00",
        }

    def ruta(self, portafolio: int | None = None) -> str:
        return f"/api/portafolios/{portafolio or self.principal}/transacciones"

    def registrar(
        self, tipo: str, fecha: str, cantidad: int, casa: int, portafolio: int | None = None
    ) -> httpx.Response:
        return self.c.post(self.ruta(portafolio), json=self.cuerpo(tipo, fecha, cantidad, casa))


def _saldo_negativo(respuesta: httpx.Response, fecha: str, saldo: str, intermediario: str) -> None:
    assert respuesta.status_code == 409, (respuesta.status_code, respuesta.json())
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"codigo", "regla", "mensaje", "datos"}
    assert (cuerpo["codigo"], cuerpo["regla"]) == ("saldo_negativo", "RF-28")
    assert cuerpo["datos"] == {"fecha_saldo_negativo": fecha, "saldo_resultante": saldo}
    dia, mes, anio = fecha[8:], fecha[5:7], fecha[:4]
    assert cuerpo["mensaje"] == (
        f"La venta dejaría el saldo de DEMOACC con {intermediario} en este portafolio en {saldo} títulos el "
        f"{dia}/{mes}/{anio}. El saldo con cada intermediario no puede quedar negativo, aunque la posición "
        "total alcance."
    )


def test_crit1_el_saldo_es_por_intermediario(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())
    _id(e.registrar("compra", "2026-09-11", 100, e.casa_a))
    _id(e.registrar("compra", "2026-09-11", 50, e.casa_b))

    # La posición total (150) alcanzaría, pero con Casa A solo hay 100.
    _saldo_negativo(e.registrar("venta", "2026-09-15", 120, e.casa_a), "2026-09-15", "-20", "Casa A")
    _saldo_negativo(e.registrar("venta", "2026-09-15", 51, e.casa_b), "2026-09-15", "-1", "Casa B")
    assert _conteo(dueno) == 2
    _id(e.registrar("venta", "2026-09-15", 100, e.casa_a))
    _saldo_negativo(e.registrar("venta", "2026-09-16", 1, e.casa_a), "2026-09-16", "-1", "Casa A")
    assert _conteo(dueno) == 3


def test_crit2_una_venta_anterior_que_deja_negativa_una_fecha_posterior(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())
    _id(e.registrar("compra", "2026-09-11", 100, e.casa_a))
    _id(e.registrar("venta", "2026-09-21", 80, e.casa_a))

    # El 15/09 quedaría en 50, pero el 21/09 en -30.
    _saldo_negativo(e.registrar("venta", "2026-09-15", 50, e.casa_a), "2026-09-21", "-30", "Casa A")
    assert _conteo(dueno) == 2
    _id(e.registrar("venta", "2026-09-15", 20, e.casa_a))
    assert _conteo(dueno) == 3


def test_crit3_otro_portafolio_no_cubre_y_compra_y_venta_el_mismo_dia(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())
    _id(e.registrar("compra", "2026-09-14", 150, e.casa_a, e.secundario))
    _id(e.registrar("compra", "2026-09-10", 100, e.casa_a))

    # X-06: los 150 del Secundario con Casa A no cuentan para el Principal.
    _saldo_negativo(e.registrar("venta", "2026-10-09", 150, e.casa_a), "2026-10-09", "-50", "Casa A")
    # Otra cuenta con el mismo nombre de intermediario tampoco cuenta.
    otra = Escenario(nueva_cuenta())
    _id(otra.registrar("compra", "2026-09-10", 500, otra.casa_a))
    _saldo_negativo(e.registrar("venta", "2026-10-09", 101, e.casa_a), "2026-10-09", "-1", "Casa A")
    assert _conteo(dueno) == 3

    # C1: compras antes que ventas el mismo día; 60 + 100 alcanzan para vender 120 el 25/09.
    _id(e.registrar("compra", "2026-09-25", 60, e.casa_a))
    _id(e.registrar("venta", "2026-09-25", 120, e.casa_a))
    assert _conteo(dueno) == 5
    listado = e.c.get(e.ruta()).json()
    assert [(t["tipo"], t["fecha_concertacion"], t["cantidad"]) for t in listado] == [
        ("compra", "2026-09-10", "100"),
        ("compra", "2026-09-25", "60"),
        ("venta", "2026-09-25", "120"),
    ]


def test_ventas_concurrentes_solo_una_pasa(
    app_pruebas: FastAPI,
    cluster_pg: ClusterPg,
    dueno: psycopg.Connection[Any],
    nueva_cuenta: Callable[..., CuentaPrueba],
) -> None:
    """Dos ventas de 80 sobre un saldo de 100 esperan juntas el bloqueo del portafolio; solo una pasa."""
    e = Escenario(nueva_cuenta())
    _id(e.registrar("compra", "2026-09-11", 100, e.casa_a))
    cookie = e.c.cookies.get(NOMBRE_COOKIE)
    assert cookie
    venta = e.cuerpo("venta", "2026-09-15", 80, e.casa_a)
    resultados: dict[int, httpx.Response] = {}
    fallas: list[BaseException] = []

    def vender(cliente: ClientePrueba, indice: int) -> None:
        try:
            resultados[indice] = cliente.post(e.ruta(), json=venta, headers={"Cookie": f"{NOMBRE_COOKIE}={cookie}"})
        except BaseException as exc:  # se revisa en el hilo principal
            fallas.append(exc)

    # El dueño toma primero el bloqueo del portafolio para que las dos ventas lo esperen a la vez.
    with psycopg.connect(cluster_pg.conninfo_dueno) as bloqueo, ClientePrueba(app_pruebas) as c1, ClientePrueba(
        app_pruebas
    ) as c2:
        bloqueo.execute("SET lock_timeout = '30s'")
        bloqueo.execute("SELECT id FROM portafolio WHERE id = %s FOR UPDATE", (e.principal,))
        hilos = [threading.Thread(target=vender, args=(cliente, i), daemon=True) for i, cliente in enumerate((c1, c2))]
        try:
            for hilo in hilos:
                hilo.start()
            limite = time.monotonic() + 30
            esperando = 0
            while time.monotonic() < limite:
                fila = dueno.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE usename = 'app_077' AND wait_event_type = 'Lock'"
                ).fetchone()
                esperando = int(fila[0]) if fila else 0
                if esperando >= 2 or fallas or len(resultados) == 2:
                    break
                time.sleep(0.05)
            assert esperando == 2, f"Esperaban el bloqueo {esperando} de 2 solicitudes"
        finally:
            bloqueo.rollback()  # suelta el bloqueo
            for hilo in hilos:
                hilo.join(timeout=60)
    assert not fallas
    assert sorted(r.status_code for r in resultados.values()) == [201, 409]
    rechazada = next(r for r in resultados.values() if r.status_code == 409)
    _saldo_negativo(rechazada, "2026-09-15", "-60", "Casa A")
    assert dueno.execute(
        "SELECT count(*) FILTER (WHERE tipo = 'venta'), count(*) FROM transaccion"
    ).fetchone() == (1, 2)
