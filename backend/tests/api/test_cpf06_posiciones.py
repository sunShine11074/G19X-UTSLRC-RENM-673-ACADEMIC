"""CPF-06: posiciones al corte (RF-06; RF-08; RF-07 crit. 3; RF-31 crit. 3; RNF-02; §4.3 E19; D-24; D-25; §8.3).

- 150 títulos comprados y 30 vendidos dan 120; al 15/09, 100; al 14/09, ninguna posición.
- Otro portafolio del mismo usuario no cuenta (RF-06 crit. 3).
- Una posición vendida por completo se lista con 0 títulos y sin valuación (D-24).
- Sin cierre ese día se usa el último anterior, y la vista dice de qué fecha es (RF-08 crit. 4).
- Un corte fuera de [inicio, fin efectivo] da 422 `fecha_fuera_de_intervalo` (D-25).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
import pytest

from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
CAMPOS_POSICION = {
    "instrumento", "titulos", "costo_total", "valor", "resultado_no_realizado", "vencida", "de_demostracion",
    "valuacion",
}
CEROS = {"costo_total": "0.00", "valor": "0.00", "resultado_no_realizado": "0.00"}


def _fuera(fin: str) -> dict[str, str]:
    return {
        "codigo": "fecha_fuera_de_intervalo",
        "regla": "RD-07",
        "mensaje": f"La fecha debe estar entre el 10/09/2026 y el {fin}, el intervalo que cubren los datos de mercado.",
    }


def _id(respuesta: httpx.Response) -> int:
    assert respuesta.status_code == 201, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _ok(respuesta: httpx.Response) -> Any:
    assert respuesta.status_code == 200, (respuesta.status_code, respuesta.json())
    return respuesta.json()


class Cartera:
    """«Principal» y «Otro», con «Casa A» y «Casa B», y el catálogo por clave."""

    def __init__(self, cuenta: CuentaPrueba) -> None:
        self.c: ClientePrueba = cuenta.cliente
        self.principal = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.otro = _id(self.c.post("/api/portafolios", json={"nombre": "Otro"}))
        self.casa_a = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.casa_b = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa B"}))
        self.ids = {i["clave"]: i["id"] for i in self.c.get("/api/instrumentos").json()}

    def registrar(
        self, portafolio: int, clave: str, tipo: str, fecha: str, cantidad: str, precio: str, importe: str, casa: int
    ) -> None:
        _id(
            self.c.post(
                f"/api/portafolios/{portafolio}/transacciones",
                json={
                    "intermediario_id": casa,
                    "instrumento_id": self.ids[clave],
                    "tipo": tipo,
                    "fecha_concertacion": fecha,
                    "cantidad": cantidad,
                    "precio": precio,
                    "importe_comisiones": importe,
                },
            )
        )

    def posiciones(self, portafolio: int, **params: str) -> httpx.Response:
        return self.c.get(f"/api/portafolios/{portafolio}/posiciones", params=params)


@pytest.fixture
def cartera(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> Cartera:
    reloj.fijar_hoy(HOY)
    k = Cartera(nueva_cuenta())
    # Principal: 100 + 50 − 30 de DEMOACC con Casa A; 10 − 10 de DEMOETF con Casa B.
    k.registrar(k.principal, "DEMOACC", "compra", "2026-09-15", "100", "104.00", "30.16", k.casa_a)
    k.registrar(k.principal, "DEMOETF", "compra", "2026-09-15", "10", "51.00", "1.48", k.casa_b)
    k.registrar(k.principal, "DEMOACC", "compra", "2026-09-17", "50", "102.00", "14.79", k.casa_a)
    k.registrar(k.principal, "DEMOETF", "venta", "2026-09-17", "10", "50.70", "1.47", k.casa_b)
    k.registrar(k.principal, "DEMOACC", "venta", "2026-09-18", "30", "98.00", "8.53", k.casa_a)
    # Otro portafolio, mismo usuario, mismo instrumento e intermediario.
    k.registrar(k.otro, "DEMOACC", "compra", "2026-09-15", "500", "104.00", "150.80", k.casa_a)
    return k


def _por_clave(vista: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["instrumento"]["clave"]: p for p in vista["posiciones"]}


def test_150_menos_30_da_120_y_el_corte_es_inclusivo(cartera: Cartera) -> None:
    k = cartera
    al_18 = _ok(k.posiciones(k.principal, fecha_corte="2026-09-18"))
    assert al_18["fecha_corte"] == "2026-09-18"
    assert [p["instrumento"]["clave"] for p in al_18["posiciones"]] == ["DEMOACC", "DEMOETF"]  # por clave
    assert all(set(p) == CAMPOS_POSICION for p in al_18["posiciones"])
    acc = _por_clave(al_18)["DEMOACC"]
    # Costo unitario (10400 + 30.16 + 5100 + 14.79) / 150 = 103.633; la venta no lo cambia (P-10).
    assert (acc["titulos"], acc["costo_total"], acc["valor"], acc["resultado_no_realizado"]) == (
        "120",
        "12435.96",
        "11838.00",
        "-597.96",
    )
    assert acc["vencida"] is False and acc["de_demostracion"] is True
    assert acc["valuacion"]["tipo"] == "precio_cierre"
    assert (acc["valuacion"]["precio"], acc["valuacion"]["fecha_dato"]) == ("98.65", "2026-09-18")
    # Vendida por completo: se lista con 0 títulos y sin valuación (D-24).
    etf = _por_clave(al_18)["DEMOETF"]
    assert (etf["titulos"], etf["valuacion"], etf["vencida"]) == ("0", None, False)
    assert {k_: etf[k_] for k_ in CEROS} == CEROS
    # Los totales vienen del corte (RNF-02).
    assert al_18["totales"] == {"costo_total": "12435.96", "valor": "11838.00", "resultado_no_realizado": "-597.96"}
    assert al_18["contiene_datos_de_demostracion"] is True

    # Al 15/09: 100 de DEMOACC (el corte incluye ese día) y 10 de DEMOETF.
    al_15 = _por_clave(_ok(k.posiciones(k.principal, fecha_corte="2026-09-15")))
    assert (al_15["DEMOACC"]["titulos"], al_15["DEMOACC"]["valor"], al_15["DEMOACC"]["costo_total"]) == (
        "100",
        "10475.00",
        "10430.16",
    )
    assert (al_15["DEMOETF"]["titulos"], al_15["DEMOETF"]["valor"]) == ("10", "514.80")

    # Al 14/09 todavía no hay transacciones: ninguna posición y totales en cero.
    al_14 = _ok(k.posiciones(k.principal, fecha_corte="2026-09-14"))
    assert al_14["posiciones"] == []
    assert al_14["totales"] == CEROS
    assert al_14["contiene_datos_de_demostracion"] is False


def test_otro_portafolio_no_cuenta(cartera: Cartera) -> None:
    k = cartera
    principal = _por_clave(_ok(k.posiciones(k.principal, fecha_corte="2026-09-17")))
    otro = _por_clave(_ok(k.posiciones(k.otro, fecha_corte="2026-09-17")))
    assert principal["DEMOACC"]["titulos"] == "150"
    assert otro["DEMOACC"]["titulos"] == "500"
    assert list(otro) == ["DEMOACC"]


def test_sin_cierre_ese_dia_usa_el_ultimo_anterior(cartera: Cartera) -> None:
    k = cartera
    # 16/09: festivo, sin cierres; se valúa con los del 15/09 (RF-08 crit. 4; RF-31 crit. 3).
    acc = _por_clave(_ok(k.posiciones(k.principal, fecha_corte="2026-09-16")))["DEMOACC"]
    assert (acc["valuacion"]["precio"], acc["valuacion"]["fecha_dato"]) == ("104.75", "2026-09-15")
    fuente = acc["valuacion"]["fuente"]
    assert fuente["nombre"] == "Semilla sintetica de demostracion 077"
    assert fuente["de_demostracion"] is True


def test_corte_por_omision_y_fuera_del_intervalo(cartera: Cartera, reloj: Any) -> None:
    k = cartera
    por_omision = _ok(k.posiciones(k.principal))
    assert por_omision["fecha_corte"] == "2026-10-14"
    assert _por_clave(por_omision)["DEMOACC"]["titulos"] == "120"
    assert _ok(k.posiciones(k.principal, fecha_corte="2026-09-10"))["posiciones"] == []  # primer día del intervalo

    for fecha in ("2026-09-09", "2026-10-15", "2027-01-01"):
        respuesta = k.posiciones(k.principal, fecha_corte=fecha)
        assert (respuesta.status_code, respuesta.json()) == (422, _fuera("14/10/2026")), fecha

    formato = k.posiciones(k.principal, fecha_corte="2026-9-15")
    assert formato.status_code == 422
    assert formato.json()["errores"] == [
        {"campo": "fecha_corte", "regla": "RD-14", "mensaje": "Escribe una fecha válida con el formato AAAA-MM-DD."}
    ]

    # Con hoy anterior al fin del intervalo, el fin efectivo es hoy.
    reloj.fijar_hoy(date(2026, 10, 1))
    assert _ok(k.posiciones(k.principal))["fecha_corte"] == "2026-10-01"
    respuesta = k.posiciones(k.principal, fecha_corte="2026-10-05")
    assert (respuesta.status_code, respuesta.json()) == (422, _fuera("01/10/2026"))
