"""CPF-11: tablero de indicadores (RF-11; RF-09; RF-10; RNF-02; RNF-07; §4.3 E09 y E20; §8.3).

- Los 4 indicadores llevan unidad y fecha de corte o periodo (RNF-07).
- Un punto por día natural, de la fecha base al fin; el último es, como texto, el valor al
  corte y el valor de mercado, y también el total de E19 al mismo corte (RNF-02; RF-11 crit. 2).
- Un portafolio sin transacciones hasta el fin responde 200 con `sin_datos` (RF-11 crit. 3; D-22).
- N7 y N8 dan 422 con sus códigos (RF-09 crit. 3; §4.4).
- Criterio de WP5 (§9): E20 de P1-A da 4.39, -6.68, pico 16/09, valle 23/09 y 58940.88.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx
import pytest

from app.motor import presentar_importe, presentar_por_ciento
from tests.comparacion_5_2 import leer_csv
from tests.conftest import ClientePrueba, CuentaPrueba
from tests.referencia.cargador import CORREO_ORACULO, Escenario52, cargar_5_2

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
INDICADORES = {"valor_mercado", "resultado_no_realizado", "twr", "maxima_caida"}

# Valores esperados con las semillas (§4.3): TWR, máxima caída y pico, a 2 decimales.
PERIODOS_4_3 = {
    "P1-A": ("4.39", "-6.68", "2026-09-16"),
    "P1-B": ("2.50", "-6.68", "2026-09-16"),
    "P1-C": ("1.84", "-2.18", "2026-09-30"),
    "P1-D": ("1.50", "0.00", None),
    "P2-A": ("6.88", "-13.68", "2026-09-15"),
    "P2-C": ("3.69", "-5.09", "2026-09-30"),
}


def _ok(respuesta: httpx.Response) -> Any:
    assert respuesta.status_code == 200, (respuesta.status_code, respuesta.json())
    return respuesta.json()


def _tablero(c: httpx.Client, portafolio: int, **params: str) -> httpx.Response:
    return c.get(f"/api/portafolios/{portafolio}/tablero", params=params)


def _posiciones(c: httpx.Client, portafolio: int, **params: str) -> httpx.Response:
    return c.get(f"/api/portafolios/{portafolio}/posiciones", params=params)


def _cargar(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> Escenario52:
    reloj.fijar_hoy(HOY)
    return cargar_5_2(nueva_cuenta(CORREO_ORACULO).cliente)


def _id(respuesta: httpx.Response) -> int:
    assert respuesta.status_code == 201, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _cartera(c: ClientePrueba, nombre: str = "Principal") -> tuple[int, int, dict[str, int]]:
    """Portafolio, intermediario «Casa A» y catálogo (clave → id)."""
    portafolio = _id(c.post("/api/portafolios", json={"nombre": nombre}))
    casa = _id(c.post("/api/intermediarios", json={"nombre": "Casa A"}))
    instrumentos = {i["clave"]: i["id"] for i in c.get("/api/instrumentos").json()}
    return portafolio, casa, instrumentos


def _dias_seguidos(serie: list[dict[str, str]], base: str, fin: str) -> None:
    fechas = [date.fromisoformat(p["fecha"]) for p in serie]
    assert fechas[0] == date.fromisoformat(base) and fechas[-1] == date.fromisoformat(fin)
    assert all(b - a == timedelta(days=1) for a, b in zip(fechas, fechas[1:], strict=False))


def test_p1a_por_omision_igual_a_posiciones_al_14_10(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> None:
    e = _cargar(nueva_cuenta, reloj)
    c, principal = e.cliente, e.portafolios["Principal"]

    # E09: intervalo de las semillas y valores por omisión (D-16; D-21).
    assert _ok(c.get("/api/intervalo-datos")) == {
        "inicio": "2026-09-10",
        "fin": "2026-10-14",
        "hoy": "2026-10-16",
        "por_omision": {"inicio": "2026-09-11", "fin": "2026-10-14", "fecha_corte": "2026-10-14"},
    }

    # E20 sin parámetros = P1-A.
    t = _ok(_tablero(c, principal))
    assert t["portafolio"] == {"id": principal, "nombre": "Principal", "divisa_base": "MXN"}
    assert t["periodo"] == {"inicio": "2026-09-11", "fin": "2026-10-14", "fecha_base": "2026-09-10", "dias": "34"}
    assert t["fecha_corte"] == "2026-10-14"
    assert t["sin_datos"] is False
    assert t["indicadores"] == {
        "valor_mercado": {"valor": "58940.88", "unidad": "MXN", "fecha_corte": "2026-10-14"},
        "resultado_no_realizado": {"valor": "2632.99", "unidad": "MXN", "fecha_corte": "2026-10-14"},
        "twr": {"valor": "4.39", "unidad": "%", "inicio": "2026-09-11", "fin": "2026-10-14"},
        "maxima_caida": {
            "valor": "-6.68",
            "unidad": "%",
            "inicio": "2026-09-11",
            "fin": "2026-10-14",
            "fecha_pico": "2026-09-16",
            "fecha_valle": "2026-09-23",
        },
    }
    assert len(t["serie"]) == 35
    _dias_seguidos(t["serie"], "2026-09-10", "2026-10-14")
    assert t["serie"][0] == {"fecha": "2026-09-10", "valor": "49929.06"}
    assert t["serie"][-1] == {"fecha": "2026-10-14", "valor": "58940.88"}
    assert t["valor_al_corte"] == "58940.88"
    assert t["contiene_datos_de_demostracion"] is True
    assert [f["nombre"] for f in t["fuentes_del_periodo"]] == [
        "Banco de México",
        "Semilla sintetica de demostracion 077",
    ]

    # E19 al mismo corte: el mismo texto (RNF-02) y la misma procedencia (RF-31).
    p = _ok(_posiciones(c, principal, fecha_corte="2026-10-14"))
    assert p["fecha_corte"] == "2026-10-14"
    assert p["totales"] == {"costo_total": "56307.89", "valor": "58940.88", "resultado_no_realizado": "2632.99"}
    assert (
        p["totales"]["valor"]
        == t["valor_al_corte"]
        == t["indicadores"]["valor_mercado"]["valor"]
        == t["serie"][-1]["valor"]
    )
    assert p["totales"]["resultado_no_realizado"] == t["indicadores"]["resultado_no_realizado"]["valor"]
    con_titulos = [
        {"instrumento": f["instrumento"], "titulos": f["titulos"], "valuacion": f["valuacion"]}
        for f in p["posiciones"]
        if f["titulos"] != "0"
    ]
    assert t["procedencia"] == con_titulos
    assert [f["instrumento"]["clave"] for f in t["procedencia"]] == [
        "BI261105", "BI261217", "BI270318", "DEMOACC", "DEMOETF", "DEMOFIB",
    ]
    assert [f["titulos"] for f in t["procedencia"]] == ["1000", "1000", "500", "220", "40", "300"]

    # Dos llamadas seguidas dan el mismo texto.
    assert _tablero(c, principal).content == _tablero(c, principal).content


def test_periodos_de_5_2(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> None:
    e = _cargar(nueva_cuenta, reloj)
    esperados = {f["periodo"]: f for f in leer_csv("indicadores")}
    assert sorted(esperados) == sorted(PERIODOS_4_3)
    for f in leer_csv("periodos", "entradas"):
        periodo, esperado = f["periodo"], esperados[f["periodo"]]
        t = _ok(_tablero(e.cliente, e.portafolios[f["portafolio_nombre"]], inicio=f["inicio"], fin=f["fin"]))
        twr, caida, pico = PERIODOS_4_3[periodo]
        ind = t["indicadores"]
        assert (ind["twr"]["valor"], ind["maxima_caida"]["valor"], ind["maxima_caida"]["fecha_pico"]) == (
            twr,
            caida,
            pico,
        ), periodo
        assert ind["twr"]["valor"] == presentar_por_ciento(Decimal(esperado["twr"])), periodo
        assert ind["maxima_caida"]["valor"] == presentar_por_ciento(Decimal(esperado["maxima_caida"])), periodo
        assert ind["maxima_caida"]["fecha_valle"] == (esperado["fecha_valle"] or None), periodo
        assert t["periodo"] == {
            "inicio": f["inicio"],
            "fin": f["fin"],
            "fecha_base": esperado["fecha_base"],
            "dias": esperado["dias"],
        }, periodo
        assert t["serie"][0]["valor"] == presentar_importe(Decimal(esperado["valor_base"])), periodo
        assert t["valor_al_corte"] == presentar_importe(Decimal(esperado["valor_fin"])), periodo
        assert ind["resultado_no_realizado"]["valor"] == presentar_importe(
            Decimal(esperado["resultado_no_realizado_fin"])
        ), periodo
        assert len(t["serie"]) == int(esperado["dias"]) + 1, periodo
        _dias_seguidos(t["serie"], esperado["fecha_base"], f["fin"])


def test_cuatro_indicadores_con_unidad_y_un_punto_por_dia(
    nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any
) -> None:
    reloj.fijar_hoy(HOY)
    c = nueva_cuenta().cliente
    portafolio, casa, instrumentos = _cartera(c)
    compra = {
        "intermediario_id": casa,
        "instrumento_id": instrumentos["DEMOACC"],
        "tipo": "compra",
        "fecha_concertacion": "2026-09-15",
        "cantidad": "10",
        "precio": "104.00",
        "importe_comisiones": "3.02",
    }
    _id(c.post(f"/api/portafolios/{portafolio}/transacciones", json=compra))

    t = _ok(_tablero(c, portafolio, inicio="2026-09-14", fin="2026-09-20"))
    assert set(t["indicadores"]) == INDICADORES
    for nombre in ("valor_mercado", "resultado_no_realizado"):
        assert t["indicadores"][nombre]["unidad"] == "MXN"
        assert t["indicadores"][nombre]["fecha_corte"] == "2026-09-20"
    for nombre in ("twr", "maxima_caida"):
        assert t["indicadores"][nombre]["unidad"] == "%"
        assert (t["indicadores"][nombre]["inicio"], t["indicadores"][nombre]["fin"]) == ("2026-09-14", "2026-09-20")
    assert t["periodo"] == {"inicio": "2026-09-14", "fin": "2026-09-20", "fecha_base": "2026-09-13", "dias": "7"}
    assert len(t["serie"]) == 8
    _dias_seguidos(t["serie"], "2026-09-13", "2026-09-20")
    # Antes de la compra el valor es 0; el 15/09 y el 16/09 (festivo) valen 10 × 104.75.
    assert [p["valor"] for p in t["serie"][:4]] == ["0.00", "0.00", "1047.50", "1047.50"]
    assert t["serie"][-1]["valor"] == t["valor_al_corte"] == t["indicadores"]["valor_mercado"]["valor"]
    assert _ok(_posiciones(c, portafolio, fecha_corte="2026-09-20"))["totales"]["valor"] == t["valor_al_corte"]
    # Ninguna cifra viaja como número JSON (D-37).
    assert all(isinstance(p["valor"], str) for p in t["serie"])


def test_sin_transacciones_hasta_el_fin_responde_sin_datos(
    nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any
) -> None:
    reloj.fijar_hoy(HOY)
    c = nueva_cuenta().cliente
    vacio, casa, instrumentos = _cartera(c, "Vacío")
    sin_datos = {
        "sin_datos": True,
        "indicadores": None,
        "serie": [],
        "valor_al_corte": None,
        "contiene_datos_de_demostracion": False,
        "procedencia": [],
        "fuentes_del_periodo": [],
    }
    t = _ok(_tablero(c, vacio))
    assert {k: t[k] for k in sin_datos} == sin_datos
    assert t["periodo"] == {"inicio": "2026-09-11", "fin": "2026-10-14", "fecha_base": "2026-09-10", "dias": "34"}
    assert t["fecha_corte"] == "2026-10-14"

    # Con una compra del 01/10, el periodo que termina el 30/09 tampoco tiene datos.
    _id(
        c.post(
            f"/api/portafolios/{vacio}/transacciones",
            json={
                "intermediario_id": casa,
                "instrumento_id": instrumentos["DEMOETF"],
                "tipo": "compra",
                "fecha_concertacion": "2026-10-01",
                "cantidad": "5",
                "precio": "50.00",
                "importe_comisiones": "0.00",
            },
        )
    )
    t = _ok(_tablero(c, vacio, inicio="2026-09-11", fin="2026-09-30"))
    assert {k: t[k] for k in sin_datos} == sin_datos
    t = _ok(_tablero(c, vacio, inicio="2026-09-11", fin="2026-10-01"))
    assert t["sin_datos"] is False and t["valor_al_corte"] is not None


def test_n7_n8_y_periodos_invalidos(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> None:
    reloj.fijar_hoy(HOY)
    c = nueva_cuenta().cliente
    portafolio, _, _ = _cartera(c)
    rechazos = {f["id"]: f for f in leer_csv("rechazos_rf28", "") if f["caso"] == "periodo"}
    assert sorted(rechazos) == ["N7", "N8"]

    invertido = {
        "codigo": "periodo_invertido",
        "regla": "RF-09",
        "mensaje": "La fecha final no puede ser anterior a la inicial.",
    }
    fuera = {
        "codigo": "periodo_fuera_de_intervalo",
        "regla": "RF-09",
        "mensaje": "El periodo debe empezar a partir del 11/09/2026 y terminar a más tardar el 14/10/2026.",
    }
    n7 = _tablero(c, portafolio, inicio=rechazos["N7"]["periodo_inicio"], fin=rechazos["N7"]["periodo_fin"])
    assert (n7.status_code, n7.json()) == (422, invertido)
    n8 = _tablero(c, portafolio, inicio=rechazos["N8"]["periodo_inicio"], fin=rechazos["N8"]["periodo_fin"])
    assert (n8.status_code, n8.json()) == (422, fuera)
    # El primer inicio válido es el 11/09 (la serie parte del cierre del 10/09).
    antes = _tablero(c, portafolio, inicio="2026-09-10", fin="2026-09-30")
    assert (antes.status_code, antes.json()) == (422, fuera)
    assert _tablero(c, portafolio, inicio="2026-09-11", fin="2026-09-11").status_code == 200  # un solo día

    # Formato inválido: 422 datos_invalidos con el campo de la consulta (RD-14).
    formato = _tablero(c, portafolio, inicio="2026-9-11", fin="2026-02-30")
    assert formato.status_code == 422
    assert formato.json()["codigo"] == "datos_invalidos"
    assert [(e["campo"], e["regla"]) for e in formato.json()["errores"]] == [("inicio", "RD-14"), ("fin", "RD-14")]

    # Con hoy anterior al fin del intervalo, el fin efectivo es hoy (RD-07; D-21).
    reloj.fijar_hoy(date(2026, 10, 1))
    assert _ok(c.get("/api/intervalo-datos"))["por_omision"] == {
        "inicio": "2026-09-11",
        "fin": "2026-10-01",
        "fecha_corte": "2026-10-01",
    }
    assert _ok(_tablero(c, portafolio))["periodo"]["fin"] == "2026-10-01"
    futuro = _tablero(c, portafolio, inicio="2026-09-11", fin="2026-10-05")
    assert futuro.status_code == 422
    assert futuro.json()["mensaje"] == (
        "El periodo debe empezar a partir del 11/09/2026 y terminar a más tardar el 01/10/2026."
    )


def test_sin_sesion_401(cliente: ClientePrueba) -> None:
    for ruta in ("/api/intervalo-datos", "/api/portafolios/1/tablero", "/api/portafolios/1/posiciones"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 401, ruta
        assert respuesta.json()["codigo"] == "sesion_requerida"
