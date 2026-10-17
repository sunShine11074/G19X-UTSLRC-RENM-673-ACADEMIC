"""CPF-05: registrar y consultar transacciones (RF-05; RD-05 a RD-08; RD-12 a RD-15; §4.3 E17 y E18; §8.3).

Incluye la prueba de humo de WP4 (§9): T01 a T16 de `entradas/transacciones.csv` se registran
por la API con 201 y su costo o ingreso por título de `esperados/`, y N1 a N6 dan los códigos
y los datos de §4.4.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from app.motor import presentar_por_titulo
from app.servicios import transacciones as servicio_transacciones
from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

MOMENTO_CDMX = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?-0[56]:00")
CAMPOS_VISTA = {
    "id", "tipo", "fecha_concertacion", "cantidad", "precio", "importe_comisiones", "costo_por_titulo",
    "ingreso_por_titulo", "intermediario", "instrumento", "registrada_en",
}
FUERA_DE_INTERVALO = {
    "codigo": "fecha_fuera_de_intervalo",
    "regla": "RD-07",
    "mensaje": "La fecha debe estar entre el 10/09/2026 y el 14/10/2026, el intervalo que cubren los datos de mercado.",
}
POSTERIOR_AL_REGISTRO = {
    "codigo": "fecha_posterior_al_registro",
    "regla": "RD-07",
    "mensaje": "La fecha de concertación no puede ser posterior a hoy.",
}
TITULOS_INVALIDOS = {
    "campo": "cantidad",
    "regla": "RD-06",
    "mensaje": "La cantidad de títulos debe ser un entero mayor que cero.",
}
CIFRA_COMO_TEXTO = 'Envía esta cifra como texto, por ejemplo "50.00".'
HOY_PRUEBAS = date(2026, 10, 16)


# ---------------------------------------------------------------------------
# Apoyo
# ---------------------------------------------------------------------------


def _id(respuesta: httpx.Response, estado: int = 201) -> int:
    assert respuesta.status_code == estado, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _instrumentos(c: ClientePrueba) -> dict[str, int]:
    return {i["clave"]: i["id"] for i in c.get("/api/instrumentos").json()}


def _registrar(c: ClientePrueba, portafolio: int, **cuerpo: Any) -> httpx.Response:
    return c.post(f"/api/portafolios/{portafolio}/transacciones", json=cuerpo)


def _conteo(dueno: psycopg.Connection[Any]) -> int:
    fila = dueno.execute("SELECT count(*) FROM transaccion").fetchone()
    assert fila is not None
    return int(fila[0])


def _errores(respuesta: httpx.Response) -> list[dict[str, str]]:
    assert respuesta.status_code == 422, (respuesta.status_code, respuesta.json())
    assert respuesta.json()["codigo"] == "datos_invalidos"
    return respuesta.json()["errores"]


def _leer_csv(ruta: Path) -> list[dict[str, str]]:
    with ruta.open(encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


class Escenario:
    """Una cuenta con el portafolio «Principal», «Casa A» y los ids del catálogo."""

    def __init__(self, cuenta: CuentaPrueba) -> None:
        self.c = cuenta.cliente
        self.portafolio = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.casa = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.ids = _instrumentos(self.c)

    def cuerpo(self, **cambios: Any) -> dict[str, Any]:
        base: dict[str, Any] = {
            "intermediario_id": self.casa,
            "instrumento_id": self.ids["DEMOACC"],
            "tipo": "compra",
            "fecha_concertacion": "2026-09-11",
            "cantidad": "100",
            "precio": "50.00",
            "importe_comisiones": "14.50",
        }
        base.update(cambios)
        return base

    def registrar(self, **cambios: Any) -> httpx.Response:
        return _registrar(self.c, self.portafolio, **self.cuerpo(**cambios))


# ---------------------------------------------------------------------------
# Criterio 1: importes y consulta
# ---------------------------------------------------------------------------


def test_crit1_costo_e_ingreso_por_titulo_y_cifras_sin_alterar(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())

    compra = e.registrar()
    assert compra.status_code == 201
    vista = compra.json()
    assert set(vista) == CAMPOS_VISTA
    assert vista["costo_por_titulo"] == "50.145" and vista["ingreso_por_titulo"] is None
    assert (vista["cantidad"], vista["precio"], vista["importe_comisiones"]) == ("100", "50.00", "14.50")
    assert vista["intermediario"] == {"id": e.casa, "nombre": "Casa A"}
    assert vista["instrumento"]["clave"] == "DEMOACC" and vista["instrumento"]["de_demostracion"] is True
    assert (vista["tipo"], vista["fecha_concertacion"]) == ("compra", "2026-09-11")
    assert MOMENTO_CDMX.fullmatch(vista["registrada_en"])

    # 100 × 54.99 − 14.95 = 5484.05 → 54.8405 por título.
    venta = e.registrar(tipo="venta", fecha_concertacion="2026-09-15", precio="54.99", importe_comisiones="14.95")
    assert venta.status_code == 201
    assert venta.json()["ingreso_por_titulo"] == "54.8405" and venta.json()["costo_por_titulo"] is None
    # Una compra anterior registrada después: E17 ordena por fecha y luego por id.
    previa = e.registrar(fecha_concertacion="2026-09-10", precio="49.9500000", importe_comisiones="0")
    assert previa.status_code == 201
    assert (previa.json()["precio"], previa.json()["importe_comisiones"]) == ("49.9500000", "0")

    listado = e.c.get(f"/api/portafolios/{e.portafolio}/transacciones")
    assert listado.status_code == 200
    filas = listado.json()
    assert [f["id"] for f in filas] == [previa.json()["id"], compra.json()["id"], venta.json()["id"]]
    assert filas[1] == vista  # E17 devuelve lo mismo que E18: «50.00» y «14.50» sin alterar
    assert filas[2] == venta.json()
    assert dueno.execute(
        "SELECT precio::text, importe_comisiones::text FROM transaccion WHERE id = %s", (vista["id"],)
    ).fetchone() == ("50.00", "14.50")
    assert _conteo(dueno) == 3


# ---------------------------------------------------------------------------
# Criterio 2: rechazos sin registrar
# ---------------------------------------------------------------------------


def test_crit2_rechazos_de_forma_sin_registrar(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())

    for cantidad in ("1.5", "0", "-1", "", "01", "2147483648", " 5"):
        assert _errores(e.registrar(cantidad=cantidad)) == [TITULOS_INVALIDOS], cantidad
    assert _errores(e.registrar(precio="0")) == [
        {"campo": "precio", "regla": "RD-06", "mensaje": "El precio debe ser mayor que cero."}
    ]
    assert _errores(e.registrar(precio="1.12345678")) == [
        {"campo": "precio", "regla": "RD-13", "mensaje": "El precio admite a lo más 7 decimales; no se redondea."}
    ]
    assert _errores(e.registrar(importe_comisiones="-0.01")) == [
        {"campo": "importe_comisiones", "regla": "RF-05", "mensaje": "El importe no puede ser negativo."}
    ]
    assert _errores(e.registrar(importe_comisiones="1.234")) == [
        {
            "campo": "importe_comisiones",
            "regla": "RD-13",
            "mensaje": "El importe admite a lo más 2 decimales; no se redondea.",
        }
    ]
    for fecha in ("2026-11-31", "2026-9-11", "11/09/2026", 20260911):
        assert _errores(e.registrar(fecha_concertacion=fecha)) == [
            {
                "campo": "fecha_concertacion",
                "regla": "RD-14",
                "mensaje": "Escribe una fecha válida con el formato AAAA-MM-DD.",
            }
        ], fecha
    assert _errores(e.registrar(tipo="regalo")) == [
        {"campo": "tipo", "regla": "RF-05", "mensaje": "El tipo debe ser compra o venta."}
    ]
    # Números JSON en lugar de cadenas (RD-12); todos los errores de forma juntos.
    assert _errores(e.registrar(cantidad=100, precio=50.0, importe_comisiones=14.5)) == [
        {"campo": campo, "regla": "RD-12", "mensaje": CIFRA_COMO_TEXTO}
        for campo in ("cantidad", "precio", "importe_comisiones")
    ]
    assert [x["campo"] for x in _errores(e.registrar(cantidad="0", precio="1e2", fecha_concertacion="x"))] == [
        "fecha_concertacion",
        "cantidad",
        "precio",
    ]
    assert _errores(e.registrar(intermediario_id=str(e.casa))) == [
        {"campo": "intermediario_id", "regla": "—", "mensaje": "Identificador inválido."}
    ]
    assert _errores(e.registrar(usuario_id=1)) == [
        {"campo": "usuario_id", "regla": "—", "mensaje": "Este dato no se puede enviar."}
    ]
    sin_campos = _errores(_registrar(e.c, e.portafolio))
    assert {x["campo"] for x in sin_campos} == {
        "intermediario_id", "instrumento_id", "tipo", "fecha_concertacion", "cantidad", "precio", "importe_comisiones",
    }
    assert _conteo(dueno) == 0


def test_crit2_venta_con_importe_mayor_o_igual_al_monto(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    e = Escenario(nueva_cuenta())
    _id(e.registrar(cantidad="10", precio="10.00", importe_comisiones="0"))
    error = {
        "campo": "importe_comisiones",
        "regla": "RF-05",
        "mensaje": "En una venta, el importe de las comisiones debe ser menor que títulos × precio.",
    }
    for importe in ("100.00", "100.01", "5000"):
        respuesta = e.registrar(tipo="venta", cantidad="10", precio="10.00", importe_comisiones=importe)
        assert _errores(respuesta) == [error], importe
        assert respuesta.json()["regla"] == "RF-05"
    # Va antes que las referencias del cuerpo (paso 3 de E18).
    assert _errores(
        e.registrar(tipo="venta", cantidad="10", precio="10.00", importe_comisiones="100", intermediario_id=2**62)
    ) == [error]
    # Con 99.99 sí pasa; en una compra el importe puede ser mayor que el monto.
    _id(e.registrar(tipo="venta", cantidad="10", precio="10.00", importe_comisiones="99.99"))
    _id(e.registrar(cantidad="1", precio="1", importe_comisiones="5.00"))
    assert _conteo(dueno) == 3


def test_crit2_referencias_del_cuerpo(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], cliente: ClientePrueba
) -> None:
    e = Escenario(nueva_cuenta())
    otra = nueva_cuenta().cliente
    casa_ajena = _id(otra.post("/api/intermediarios", json={"nombre": "Casa A"}))

    ajeno = e.registrar(intermediario_id=casa_ajena)
    inexistente = e.registrar(intermediario_id=2**62)
    assert ajeno.status_code == inexistente.status_code == 404
    assert ajeno.content == inexistente.content
    assert ajeno.json() == {"codigo": "no_encontrado", "regla": "RF-02", "mensaje": "No existe el intermediario."}
    sin_instrumento = e.registrar(instrumento_id=2**62)
    assert sin_instrumento.status_code == 404
    assert sin_instrumento.json() == {
        "codigo": "no_encontrado",
        "regla": "RF-02",
        "mensaje": "No existe el instrumento.",
    }

    # Sin sesión, 401; sin Origin, 403.
    sin_sesion = _registrar(cliente, e.portafolio, **e.cuerpo())
    assert sin_sesion.status_code == 401 and sin_sesion.json()["codigo"] == "sesion_requerida"
    assert cliente.get(f"/api/portafolios/{e.portafolio}/transacciones").status_code == 401
    sin_origen = e.c.post(
        f"/api/portafolios/{e.portafolio}/transacciones", json=e.cuerpo(), headers={"Origin": "http://otro.example.com"}
    )
    assert sin_origen.status_code == 403
    assert _conteo(dueno) == 0


# ---------------------------------------------------------------------------
# Criterio 3: fechas (RD-07; RD-15) y CETES (RF-26a crit. 2; RD-05)
# ---------------------------------------------------------------------------


def test_crit3_fecha_posterior_a_hoy_y_fuera_del_intervalo(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], reloj: Any
) -> None:
    e = Escenario(nueva_cuenta())

    reloj.fijar_hoy(date(2026, 10, 1))
    posterior = e.registrar(fecha_concertacion="2026-10-05")
    assert posterior.status_code == 422 and posterior.json() == POSTERIOR_AL_REGISTRO
    _id(e.registrar(fecha_concertacion="2026-10-01"))  # hoy sí se admite

    reloj.fijar_hoy(HOY_PRUEBAS)
    for fecha in ("2026-09-09", "2026-10-15", "2025-12-31"):  # N5, N6 y otra anterior
        fuera = e.registrar(fecha_concertacion=fecha)
        assert fuera.status_code == 422 and fuera.json() == FUERA_DE_INTERVALO, fecha
    futura = e.registrar(fecha_concertacion="2026-10-17")
    assert futura.status_code == 422 and futura.json() == POSTERIOR_AL_REGISTRO
    # Los extremos del intervalo se incluyen.
    _id(e.registrar(fecha_concertacion="2026-09-10"))
    _id(e.registrar(fecha_concertacion="2026-10-14"))
    assert _conteo(dueno) == 3


def test_crit3_plazo_de_cetes(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    e = Escenario(nueva_cuenta())
    cetes = {
        "instrumento_id": e.ids["BI270318"],
        "fecha_concertacion": "2026-09-10",
        "precio": "9.6629250",
        "importe_comisiones": "0.00",
    }

    # Con el catálogo semilla no ocurre (189 días ≤ 730): se baja el límite para probar la regla.
    monkeypatch.setattr(servicio_transacciones, "LIMITE_DIAS_CETES", 188)
    excedido = e.registrar(**cetes)
    assert excedido.status_code == 422
    assert excedido.json() == {
        "codigo": "plazo_cetes_excedido",
        "regla": "RD-05",
        "mensaje": "La emisión vence en más de 188 días desde la fecha de concertación.",
    }
    monkeypatch.setattr(servicio_transacciones, "LIMITE_DIAS_CETES", 189)
    _id(e.registrar(**cetes))
    assert servicio_transacciones.LIMITE_DIAS_CETES == 189
    monkeypatch.undo()
    assert servicio_transacciones.LIMITE_DIAS_CETES == 730
    assert _conteo(dueno) == 1


def test_sin_put_patch_ni_delete_de_transacciones(
    app_pruebas: FastAPI, nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    rutas = app_pruebas.openapi()["paths"]
    assert set(rutas["/api/portafolios/{portafolio_id}/transacciones"]) == {"get", "post"}
    for ruta, operaciones in rutas.items():
        if "transacciones" in ruta:
            assert not {"put", "patch", "delete"} & set(operaciones), ruta

    e = Escenario(nueva_cuenta())
    transaccion = _id(e.registrar())
    ruta = f"/api/portafolios/{e.portafolio}/transacciones"
    for metodo in ("PUT", "PATCH", "DELETE"):
        respuesta = e.c.request(metodo, ruta, json=e.cuerpo(cantidad="1"))
        assert respuesta.status_code == 405 and respuesta.json()["codigo"] == "metodo_no_permitido", metodo
        assert e.c.request(metodo, f"{ruta}/{transaccion}", json=e.cuerpo()).status_code == 404
    assert dueno.execute("SELECT count(*), min(cantidad) FROM transaccion").fetchone() == (1, 100)


# ---------------------------------------------------------------------------
# Prueba de humo de WP4: T01 a T16 y N1 a N6 por la API (5.2; §4.4)
# ---------------------------------------------------------------------------


def test_humo_5_2_t01_a_t16_y_n1_a_n6(
    nueva_cuenta: Callable[..., CuentaPrueba],
    dueno: psycopg.Connection[Any],
    reloj: Any,
    ruta_oraculo: Path,
) -> None:
    reloj.fijar_hoy(HOY_PRUEBAS)
    entradas = ruta_oraculo / "entradas"
    c = nueva_cuenta("oraculo@example.com").cliente
    portafolios = {
        f["nombre"]: _id(c.post("/api/portafolios", json={"nombre": f["nombre"], "divisa_base": f["divisa_base"]}))
        for f in _leer_csv(entradas / "portafolios.csv")
    }
    intermediarios = {
        f["nombre"]: _id(c.post("/api/intermediarios", json={"nombre": f["nombre"]}))
        for f in _leer_csv(entradas / "intermediarios.csv")
    }
    instrumentos = _instrumentos(c)
    esperados = {f["ref"]: f for f in _leer_csv(ruta_oraculo / "esperados" / "transacciones.csv")}

    def cuerpo(f: dict[str, str]) -> dict[str, Any]:
        return {
            "intermediario_id": intermediarios[f["intermediario_nombre"]],
            "instrumento_id": instrumentos[f["instrumento_clave"]],
            "tipo": f["tipo"],
            "fecha_concertacion": f["fecha_concertacion"],
            "cantidad": f["cantidad"],
            "precio": f["precio"],
            "importe_comisiones": f["importe_comisiones"],
        }

    # T01 a T16, en el orden de ref.
    ids_por_ref: dict[str, int] = {}
    for f in sorted(_leer_csv(entradas / "transacciones.csv"), key=lambda f: f["ref"]):
        respuesta = _registrar(c, portafolios[f["portafolio_nombre"]], **cuerpo(f))
        assert respuesta.status_code == 201, (f["ref"], respuesta.json())
        vista = respuesta.json()
        ids_por_ref[f["ref"]] = vista["id"]
        esperado = esperados[f["ref"]]
        por_titulo = "costo_por_titulo" if f["tipo"] == "compra" else "ingreso_por_titulo"
        otro = "ingreso_por_titulo" if f["tipo"] == "compra" else "costo_por_titulo"
        assert vista[por_titulo] == presentar_por_titulo(Decimal(esperado[por_titulo])), f["ref"]
        assert vista[otro] is None
        assert (vista["cantidad"], vista["precio"], vista["importe_comisiones"]) == (
            f["cantidad"],
            f["precio"],
            f["importe_comisiones"],
        )
    assert len(ids_por_ref) == 16
    assert _conteo(dueno) == 16
    vistas_por_id = {
        t["id"]: t
        for nombre in portafolios
        for t in c.get(f"/api/portafolios/{portafolios[nombre]}/transacciones").json()
    }
    assert vistas_por_id[ids_por_ref["T01"]]["costo_por_titulo"] == "100.23985"
    assert vistas_por_id[ids_por_ref["T11"]]["costo_por_titulo"] == "48.0388333"
    assert vistas_por_id[ids_por_ref["T10"]]["ingreso_por_titulo"] == "23.1402"
    assert len(vistas_por_id) == 16

    # N1 a N6 por E18, con el código y los datos de §4.4.
    candidatos = {f["id"]: f for f in _leer_csv(ruta_oraculo / "rechazos_rf28.csv") if f["caso"] == "transaccion"}
    assert sorted(candidatos) == ["N1", "N2", "N3", "N4", "N5", "N6"]
    for ref, f in sorted(candidatos.items()):
        respuesta = _registrar(c, portafolios[f["portafolio_nombre"]], **cuerpo(f))
        cuerpo_error = respuesta.json()
        if f["fecha_saldo_negativo"]:  # N1 a N3: RF-28
            assert respuesta.status_code == 409, ref
            assert (cuerpo_error["codigo"], cuerpo_error["regla"]) == ("saldo_negativo", "RF-28")
            assert cuerpo_error["datos"] == {
                "fecha_saldo_negativo": f["fecha_saldo_negativo"],
                "saldo_resultante": f["saldo_resultante"],
            }
            assert cuerpo_error["mensaje"].startswith(
                f"La venta dejaría el saldo de {f['instrumento_clave']} con {f['intermediario_nombre']} "
                f"en este portafolio en {f['saldo_resultante']} títulos el "
                f"{date.fromisoformat(f['fecha_saldo_negativo']).strftime('%d/%m/%Y')}."
            )
        elif "RF-26a" in f["regla"]:  # N4
            assert respuesta.status_code == 422, ref
            assert cuerpo_error == {
                "codigo": "fecha_en_o_despues_del_vencimiento",
                "regla": "RF-26a",
                "mensaje": "La emisión BI261008 vence el 08/10/2026: no se registran transacciones en esa "
                "fecha ni después.",
            }
        else:  # N5 y N6: RD-07 y criterio 3 de RF-05
            assert "RD-07" in f["regla"]
            assert respuesta.status_code == 422, ref
            assert cuerpo_error == FUERA_DE_INTERVALO
    assert _conteo(dueno) == 16
