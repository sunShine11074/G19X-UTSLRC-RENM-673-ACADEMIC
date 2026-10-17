"""CPF-02: cada usuario ve y opera solo lo suyo (RF-02; RD-01; RD-02; RNF-03; §4.1 «Orden de validación»; §8.3).

- A y B tienen un portafolio y un intermediario con el mismo nombre (homónimos).
- Las listas, las posiciones y el tablero de A solo muestran lo de A.
- Toda operación de A sobre los ids de B (también una transacción con el intermediario de B)
  da 404 con un cuerpo idéntico, byte a byte, al de un id inexistente (2**62), y la huella de
  la base no cambia.
- Sin sesión: 401.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
import psycopg
import pytest
from psycopg import sql

from tests.conftest import TABLAS_DE_CUENTA, ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
INEXISTENTE = 2**62


def _id(respuesta: httpx.Response) -> int:
    assert respuesta.status_code == 201, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _ok(respuesta: httpx.Response) -> Any:
    assert respuesta.status_code == 200, (respuesta.status_code, respuesta.json())
    return respuesta.json()


def huella(dueno: psycopg.Connection[Any]) -> dict[str, tuple[int, str]]:
    """Conteo y md5 de las filas de las 5 tablas de cuenta, tomados por el dueño."""
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


class Usuario:
    """Cuenta con «Principal», «Casa A» y una compra de DEMOACC el 15/09."""

    def __init__(self, cuenta: CuentaPrueba, titulos: str) -> None:
        self.c: ClientePrueba = cuenta.cliente
        self.portafolio = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.casa = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.demoacc = next(i["id"] for i in self.c.get("/api/instrumentos").json() if i["clave"] == "DEMOACC")
        self.transaccion = _id(
            self.c.post(f"/api/portafolios/{self.portafolio}/transacciones", json=self.cuerpo(self.casa, titulos))
        )

    def cuerpo(self, intermediario: int, titulos: str = "1") -> dict[str, Any]:
        return {
            "intermediario_id": intermediario,
            "instrumento_id": self.demoacc,
            "tipo": "compra",
            "fecha_concertacion": "2026-09-15",
            "cantidad": titulos,
            "precio": "104.00",
            "importe_comisiones": "0.00",
        }


@pytest.fixture
def a_y_b(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> tuple[Usuario, Usuario]:
    reloj.fijar_hoy(HOY)
    return Usuario(nueva_cuenta(), "10"), Usuario(nueva_cuenta(), "100")


def test_listas_posiciones_y_tablero_solo_con_lo_propio(a_y_b: tuple[Usuario, Usuario]) -> None:
    a, b = a_y_b
    assert [p["id"] for p in _ok(a.c.get("/api/portafolios"))] == [a.portafolio]
    assert [i["id"] for i in _ok(a.c.get("/api/intermediarios"))] == [a.casa]
    assert [t["id"] for t in _ok(a.c.get(f"/api/portafolios/{a.portafolio}/transacciones"))] == [a.transaccion]

    posiciones = _ok(a.c.get(f"/api/portafolios/{a.portafolio}/posiciones"))
    assert [(p["instrumento"]["clave"], p["titulos"]) for p in posiciones["posiciones"]] == [("DEMOACC", "10")]
    tablero = _ok(a.c.get(f"/api/portafolios/{a.portafolio}/tablero"))
    assert [(p["instrumento"]["clave"], p["titulos"]) for p in tablero["procedencia"]] == [("DEMOACC", "10")]
    assert tablero["valor_al_corte"] == posiciones["totales"]["valor"]

    # B ve lo suyo, con los mismos nombres.
    assert [(p["id"], p["nombre"]) for p in _ok(b.c.get("/api/portafolios"))] == [(b.portafolio, "Principal")]
    assert _ok(b.c.get(f"/api/portafolios/{b.portafolio}/posiciones"))["posiciones"][0]["titulos"] == "100"


def test_operar_sobre_lo_ajeno_da_el_mismo_404_que_lo_inexistente(
    a_y_b: tuple[Usuario, Usuario], dueno: psycopg.Connection[Any]
) -> None:
    a, b = a_y_b
    antes = huella(dueno)

    def comparar(metodo: str, plantilla: str, cuerpo: dict[str, Any] | None = None, **params: str) -> None:
        ajeno = a.c.request(metodo, plantilla.format(b.portafolio), json=cuerpo, params=params or None)
        inexistente = a.c.request(metodo, plantilla.format(INEXISTENTE), json=cuerpo, params=params or None)
        assert ajeno.status_code == 404, (metodo, plantilla, ajeno.status_code)
        assert ajeno.content == inexistente.content, (metodo, plantilla)
        assert ajeno.json()["codigo"] == "no_encontrado"

    comparar("GET", "/api/portafolios/{}")
    comparar("PATCH", "/api/portafolios/{}", {"nombre": "Ajeno"})
    comparar("PATCH", "/api/portafolios/{}", {"nombre": ""})  # 404 antes que la forma del cuerpo
    comparar("DELETE", "/api/portafolios/{}", {"confirmacion": "Principal"})
    comparar("GET", "/api/portafolios/{}/transacciones")
    comparar("POST", "/api/portafolios/{}/transacciones", a.cuerpo(a.casa))
    comparar("POST", "/api/portafolios/{}/transacciones", {"cantidad": 1})
    comparar("GET", "/api/portafolios/{}/posiciones")
    comparar("GET", "/api/portafolios/{}/posiciones", fecha_corte="2026-09-15")
    comparar("GET", "/api/portafolios/{}/posiciones", fecha_corte="no es fecha")
    comparar("GET", "/api/portafolios/{}/tablero")
    comparar("GET", "/api/portafolios/{}/tablero", inicio="2026-10-14", fin="2026-09-11")

    # Una transacción en el portafolio propio con el intermediario de B (RD-02).
    con_ajeno = a.c.post(f"/api/portafolios/{a.portafolio}/transacciones", json=a.cuerpo(b.casa))
    con_inexistente = a.c.post(f"/api/portafolios/{a.portafolio}/transacciones", json=a.cuerpo(INEXISTENTE))
    assert con_ajeno.status_code == 404
    assert con_ajeno.content == con_inexistente.content
    assert con_ajeno.json()["mensaje"] == "No existe el intermediario."

    assert huella(dueno) == antes
    # B sigue intacto.
    assert _ok(b.c.get(f"/api/portafolios/{b.portafolio}"))["nombre"] == "Principal"


def test_sin_sesion_401(a_y_b: tuple[Usuario, Usuario], cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    a, b = a_y_b
    antes = huella(dueno)
    for metodo, ruta, cuerpo in (
        ("GET", "/api/portafolios", None),
        ("GET", "/api/intermediarios", None),
        ("GET", f"/api/portafolios/{b.portafolio}", None),
        ("PATCH", f"/api/portafolios/{b.portafolio}", {"nombre": "Ajeno"}),
        ("DELETE", f"/api/portafolios/{b.portafolio}", {"confirmacion": "Principal"}),
        ("GET", f"/api/portafolios/{b.portafolio}/transacciones", None),
        ("POST", f"/api/portafolios/{b.portafolio}/transacciones", a.cuerpo(b.casa)),
        ("GET", f"/api/portafolios/{b.portafolio}/posiciones", None),
        ("GET", f"/api/portafolios/{b.portafolio}/tablero", None),
        ("GET", "/api/intervalo-datos", None),
    ):
        respuesta = cliente.request(metodo, ruta, json=cuerpo)
        assert respuesta.status_code == 401, (metodo, ruta)
        assert respuesta.json()["codigo"] == "sesion_requerida"
    assert huella(dueno) == antes
