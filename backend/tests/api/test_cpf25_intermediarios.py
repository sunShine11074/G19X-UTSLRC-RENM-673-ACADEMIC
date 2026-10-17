"""CPF-25: intermediarios (RF-25; RF-02; RD-03; RD-09; RD-10; §4.3 E10 y E11; §8.3)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

NOMBRE_DUPLICADO = {
    "codigo": "nombre_duplicado",
    "regla": "RD-03",
    "mensaje": "Ya tienes un intermediario con ese nombre (no se distinguen mayúsculas ni espacios al inicio o "
    "al final).",
}
METODO_NO_PERMITIDO = {
    "codigo": "metodo_no_permitido",
    "regla": "RD-09",
    "mensaje": "Esta operación no está disponible.",
}


def _crear(c: ClientePrueba, nombre: Any) -> httpx.Response:
    return c.post("/api/intermediarios", json={"nombre": nombre})


def _id(respuesta: httpx.Response, estado: int = 201) -> int:
    assert respuesta.status_code == estado, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _intermediarios(dueno: psycopg.Connection[Any]) -> list[tuple[int, int, str]]:
    return [
        (int(f[0]), int(f[1]), f[2])
        for f in dueno.execute("SELECT id, usuario_id, nombre FROM intermediario ORDER BY id").fetchall()
    ]


def test_casa_a_tal_como_se_capturo_y_solo_para_su_dueno(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], cliente: ClientePrueba
) -> None:
    a = nueva_cuenta()
    b = nueva_cuenta()

    alta = _crear(a.cliente, "Casa A")
    assert alta.status_code == 201
    casa_a = alta.json()["id"]
    assert alta.json() == {"id": casa_a, "nombre": "Casa A"}

    for nombre in ("casa a", " Casa A ", "CASA A", "Casa A"):
        duplicado = _crear(a.cliente, nombre)
        assert duplicado.status_code == 409, nombre
        assert duplicado.json() == NOMBRE_DUPLICADO
    for nombre in ("", "   "):
        vacio = _crear(a.cliente, nombre)
        assert vacio.status_code == 422
        assert vacio.json()["errores"] == [{"campo": "nombre", "regla": "RD-03", "mensaje": "Escribe un nombre."}]
    extra = a.cliente.post("/api/intermediarios", json={"nombre": "Casa C", "usuario_id": b.usuario_id})
    assert extra.status_code == 422
    assert extra.json()["errores"] == [
        {"campo": "usuario_id", "regla": "—", "mensaje": "Este dato no se puede enviar."}
    ]

    # Otra cuenta sí puede usar «Casa A»; cada quien ve solo los suyos.
    casa_a_de_b = _id(_crear(b.cliente, "Casa A"))
    casa_b = _id(_crear(a.cliente, "casa b"))
    con_espacios = _crear(a.cliente, "  Casa Z ")
    assert con_espacios.status_code == 201 and con_espacios.json()["nombre"] == "  Casa Z "

    lista_a = a.cliente.get("/api/intermediarios").json()
    assert len(lista_a) == 3
    # Orden por nombre sin distinguir mayúsculas (los espacios iniciales dependen de la intercalación).
    assert [i for i in lista_a if i["nombre"] != "  Casa Z "] == [
        {"id": casa_a, "nombre": "Casa A"},
        {"id": casa_b, "nombre": "casa b"},
    ]
    assert b.cliente.get("/api/intermediarios").json() == [{"id": casa_a_de_b, "nombre": "Casa A"}]
    assert _intermediarios(dueno) == [
        (casa_a, a.usuario_id, "Casa A"),
        (casa_a_de_b, b.usuario_id, "Casa A"),
        (casa_b, a.usuario_id, "casa b"),
        (con_espacios.json()["id"], a.usuario_id, "  Casa Z "),
    ]

    for respuesta in (cliente.get("/api/intermediarios"), _crear(cliente, "Casa X")):
        assert respuesta.status_code == 401
    assert len(_intermediarios(dueno)) == 4


def test_no_se_modifican_ni_se_eliminan(
    app_pruebas: FastAPI, nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    rutas = app_pruebas.openapi()["paths"]
    assert set(rutas["/api/intermediarios"]) == {"get", "post"}
    assert not [r for r in rutas if r.startswith("/api/intermediarios/")]

    c = nueva_cuenta().cliente
    casa = _id(_crear(c, "Casa A"))
    for metodo in ("PUT", "PATCH", "DELETE"):
        respuesta = c.request(metodo, "/api/intermediarios", json={"nombre": "Casa B"})
        assert respuesta.status_code == 405, metodo
        assert respuesta.json() == METODO_NO_PERMITIDO
    for metodo in ("GET", "PUT", "PATCH", "DELETE"):
        assert c.request(metodo, f"/api/intermediarios/{casa}", json={"nombre": "Casa B"}).status_code == 404
    assert [n for _, _, n in _intermediarios(dueno)] == ["Casa A"]


def test_se_conservan_al_eliminar_el_portafolio(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    c = nueva_cuenta().cliente
    casa = _id(_crear(c, "Casa A"))
    portafolio = _id(c.post("/api/portafolios", json={"nombre": "Retiro"}))
    demoetf = next(i["id"] for i in c.get("/api/instrumentos").json() if i["clave"] == "DEMOETF")
    _id(
        c.post(
            f"/api/portafolios/{portafolio}/transacciones",
            json={
                "intermediario_id": casa,
                "instrumento_id": demoetf,
                "tipo": "compra",
                "fecha_concertacion": "2026-09-10",
                "cantidad": "100",
                "precio": "50.05",
                "importe_comisiones": "14.51",
            },
        )
    )
    borrado = c.request("DELETE", f"/api/portafolios/{portafolio}", json={"confirmacion": "Retiro"})
    assert borrado.status_code == 204
    assert c.get("/api/intermediarios").json() == [{"id": casa, "nombre": "Casa A"}]
    assert dueno.execute("SELECT count(*) FROM transaccion").fetchone() == (0,)
    assert len(_intermediarios(dueno)) == 1
