"""CPF-04: catálogo de instrumentos (RF-04; RD-04; RD-09; D-08; §4.3 E08; §8.3)."""

from __future__ import annotations

import csv
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

import psycopg
import pytest
from fastapi import FastAPI

from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

CLASES = {"accion", "etf", "fibra", "cetes"}
CAMPOS = {"id", "clave", "nombre", "clase_activo", "divisa", "de_demostracion", "vencimiento", "valor_nominal"}
METODO_NO_PERMITIDO = {
    "codigo": "metodo_no_permitido",
    "regla": "RD-09",
    "mensaje": "Esta operación no está disponible.",
}
# Rutas del catálogo o de los datos de mercado: solo se leen (RD-09; CU-11 es 04).
PALABRAS_DE_MERCADO = ("instrumento", "precio", "tasa", "carga", "fuente", "mercado", "intervalo")


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


def test_sin_sesion_da_401(cliente: ClientePrueba) -> None:
    respuesta = cliente.get("/api/instrumentos")
    assert respuesta.status_code == 401
    assert respuesta.json() == {
        "codigo": "sesion_requerida",
        "regla": "RNF-03",
        "mensaje": "Inicia sesión para continuar.",
    }


def test_catalogo_con_las_semillas(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], ruta_oraculo: Path
) -> None:
    respuesta = nueva_cuenta().cliente.get("/api/instrumentos")
    assert respuesta.status_code == 200
    catalogo = respuesta.json()

    assert len(catalogo) == 7
    claves = [i["clave"] for i in catalogo]
    assert len(set(claves)) == 7
    assert claves == sorted(claves)
    ids_bd = dict(dueno.execute("SELECT clave, id FROM instrumento").fetchall())
    assert {i["clave"]: i["id"] for i in catalogo} == ids_bd

    for instrumento in catalogo:
        assert set(instrumento) == CAMPOS
        assert instrumento["clase_activo"] in CLASES
        assert instrumento["divisa"] == "MXN"
        if instrumento["clase_activo"] == "cetes":
            vencimiento = date.fromisoformat(instrumento["vencimiento"])
            assert instrumento["clave"] == "BI" + vencimiento.strftime("%y%m%d")
            assert instrumento["valor_nominal"] == "10.00"  # tal como se cargó (RD-14)
            assert instrumento["de_demostracion"] is False
        else:
            assert instrumento["clave"].startswith("DEMO")
            assert instrumento["de_demostracion"] is True  # RF-07 crit. 3; D-23
            assert instrumento["vencimiento"] is None and instrumento["valor_nominal"] is None

    # Las semillas son las entradas del oráculo (5.2).
    esperados = {
        f["clave"]: {
            "clave": f["clave"],
            "nombre": f["nombre"],
            "clase_activo": f["clase_activo"],
            "divisa": f["divisa"],
            "de_demostracion": f["de_demostracion"] == "true",
            "vencimiento": f["vencimiento"] or None,
            "valor_nominal": f["valor_nominal"] or None,
        }
        for f in _leer_csv(ruta_oraculo / "entradas" / "instrumentos.csv")
    }
    assert {i["clave"]: {k: v for k, v in i.items() if k != "id"} for i in catalogo} == esperados


def test_sin_escrituras_del_catalogo(
    app_pruebas: FastAPI, nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    rutas = app_pruebas.openapi()["paths"]
    assert set(rutas["/api/instrumentos"]) == {"get"}
    for ruta, operaciones in rutas.items():
        if any(palabra in ruta for palabra in PALABRAS_DE_MERCADO):
            assert set(operaciones) == {"get"}, ruta

    c = nueva_cuenta().cliente
    cuerpo = {"clave": "DEMONEW", "nombre": "Nuevo", "clase_activo": "accion", "divisa": "MXN"}
    for metodo in ("POST", "PUT", "PATCH", "DELETE"):
        respuesta = c.request(metodo, "/api/instrumentos", json=cuerpo)
        assert respuesta.status_code == 405, metodo
        assert respuesta.json() == METODO_NO_PERMITIDO
        assert respuesta.headers["allow"] == "GET"
    primero = c.get("/api/instrumentos").json()[0]["id"]
    assert c.request("DELETE", f"/api/instrumentos/{primero}").status_code == 404
    fila = dueno.execute("SELECT count(*) FROM instrumento").fetchone()
    assert fila == (7,)
