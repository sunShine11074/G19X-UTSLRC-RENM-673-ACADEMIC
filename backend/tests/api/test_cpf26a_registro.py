"""CPF-26a, criterios 2 y 3: registro de CETES frente a su vencimiento (RF-26a; §4.3 E18 paso 9; §4.4 N4; §8.3).

- Crit. 2: una transacción fechada en el vencimiento o después se rechaza con 422 (N4).
- Crit. 3: el sistema no crea transacciones: ni al registrar ni al consultar posiciones o el
  tablero del 08/10, el día del vencimiento de BI261008.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
import psycopg
import pytest

from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

VENCIDA = {
    "codigo": "fecha_en_o_despues_del_vencimiento",
    "regla": "RF-26a",
    "mensaje": "La emisión BI261008 vence el 08/10/2026: no se registran transacciones en esa fecha ni después.",
}


def _id(respuesta: httpx.Response, estado: int = 201) -> int:
    assert respuesta.status_code == estado, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _huella(dueno: psycopg.Connection[Any]) -> list[tuple[Any, ...]]:
    """Todas las transacciones, como las ve el dueño."""
    return [
        tuple(f)
        for f in dueno.execute(
            "SELECT id, portafolio_id, intermediario_id, instrumento_id, tipo, fecha_concertacion, cantidad, "
            "precio::text, importe_comisiones::text, registrada_en FROM transaccion ORDER BY id"
        ).fetchall()
    ]


class Cetes:
    """«Principal» con 1000 títulos de BI261008 en «Casa A» y 500 en «Casa B», comprados el 10/09."""

    def __init__(self, cuenta: CuentaPrueba) -> None:
        self.c: ClientePrueba = cuenta.cliente
        self.portafolio = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.casa_a = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.casa_b = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa B"}))
        self.bi261008 = next(i["id"] for i in self.c.get("/api/instrumentos").json() if i["clave"] == "BI261008")
        _id(self.registrar("compra", "2026-09-10", "1000", self.casa_a))
        _id(self.registrar("compra", "2026-09-10", "500", self.casa_b))

    def registrar(self, tipo: str, fecha: str, cantidad: str, casa: int | None = None) -> httpx.Response:
        return self.c.post(
            f"/api/portafolios/{self.portafolio}/transacciones",
            json={
                "intermediario_id": casa or self.casa_a,
                "instrumento_id": self.bi261008,
                "tipo": tipo,
                "fecha_concertacion": fecha,
                "cantidad": cantidad,
                "precio": "10.0000000",
                "importe_comisiones": "0.00",
            },
        )


def test_crit2_en_el_vencimiento_o_despues_se_rechaza(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], reloj: Any
) -> None:
    reloj.fijar_hoy(date(2026, 10, 16))
    e = Cetes(nueva_cuenta())
    antes = _huella(dueno)
    assert len(antes) == 2

    # N4: venta el día del vencimiento; también compras y ventas posteriores.
    for tipo, fecha, casa in (
        ("venta", "2026-10-08", e.casa_b),
        ("compra", "2026-10-08", e.casa_a),
        ("compra", "2026-10-09", e.casa_a),
        ("venta", "2026-10-14", e.casa_a),
    ):
        respuesta = e.registrar(tipo, fecha, "100", casa)
        assert respuesta.status_code == 422, (tipo, fecha)
        assert respuesta.json() == VENCIDA
    assert _huella(dueno) == antes

    # Un día antes (d = 1) sí se registra, y solo se agrega esa fila.
    venta = e.registrar("venta", "2026-10-07", "100", e.casa_b)
    assert venta.status_code == 201
    despues = _huella(dueno)
    assert despues[:2] == antes and len(despues) == 3
    assert despues[2][4:7] == ("venta", date(2026, 10, 7), 100)


def test_crit3_consultar_el_08_10_no_crea_transacciones(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], reloj: Any
) -> None:
    reloj.fijar_hoy(date(2026, 10, 16))
    e = Cetes(nueva_cuenta())
    antes = _huella(dueno)
    listado = e.c.get(f"/api/portafolios/{e.portafolio}/transacciones").json()

    posiciones = e.c.get(f"/api/portafolios/{e.portafolio}/posiciones", params={"fecha_corte": "2026-10-08"})
    assert posiciones.status_code == 200, posiciones.json()
    tablero = e.c.get(
        f"/api/portafolios/{e.portafolio}/tablero", params={"inicio": "2026-09-11", "fin": "2026-10-08"}
    )
    assert tablero.status_code == 200, tablero.json()

    assert _huella(dueno) == antes
    assert e.c.get(f"/api/portafolios/{e.portafolio}/transacciones").json() == listado


def test_crit3_registrar_no_crea_otras_transacciones(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], reloj: Any
) -> None:
    reloj.fijar_hoy(date(2026, 10, 16))
    e = Cetes(nueva_cuenta())
    # Ni la liquidación del 08/10 ni la reinversión se registran solas (RF-26a crit. 3; S-14).
    listado = e.c.get(f"/api/portafolios/{e.portafolio}/transacciones").json()
    assert [(t["tipo"], t["fecha_concertacion"], t["cantidad"]) for t in listado] == [
        ("compra", "2026-09-10", "1000"),
        ("compra", "2026-09-10", "500"),
    ]
    assert len(_huella(dueno)) == 2
