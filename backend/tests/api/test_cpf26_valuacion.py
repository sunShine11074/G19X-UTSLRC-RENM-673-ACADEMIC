"""CPF-26a crit. 1 y CPF-26b crit. 3: CETES que vencen y tasa vigente al corte (RF-26a; RF-26b; R-14; §4.3 E19 y E20).

- 1000 + 500 títulos de BI261008 quedan en 0 desde su vencimiento, el 08/10; la posición se
  lista como vencida y sin valuación (RF-26a crit. 1; D-24), y no se crea ninguna transacción.
- Al 07/10 rige la colocación del 01/10, y al 14/10 la del 08/10: la del 15/10 ya está
  publicada pero no rige (RF-26b crit. 3; R-14). Las cifras coinciden con `valuacion_cetes.csv`.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Any

import httpx
import pytest

from app.motor import presentar
from tests.comparacion_5_2 import leer_csv
from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
BANXICO = {
    "nombre": "Banco de México",
    "direccion": "https://www.banxico.org.mx",
    "de_demostracion": False,
    "atribucion": "Fuente: Banco de México, https://www.banxico.org.mx",
}


def _id(respuesta: httpx.Response) -> int:
    assert respuesta.status_code == 201, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _ok(respuesta: httpx.Response) -> Any:
    assert respuesta.status_code == 200, (respuesta.status_code, respuesta.json())
    return respuesta.json()


class CarteraCetes:
    """«Principal» con BI261008 (1000 en Casa A y 500 en Casa B), BI261217 y BI261105."""

    def __init__(self, cuenta: CuentaPrueba) -> None:
        self.c: ClientePrueba = cuenta.cliente
        self.portafolio = _id(self.c.post("/api/portafolios", json={"nombre": "Principal"}))
        self.casa_a = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa A"}))
        self.casa_b = _id(self.c.post("/api/intermediarios", json={"nombre": "Casa B"}))
        self.ids = {i["clave"]: i["id"] for i in self.c.get("/api/instrumentos").json()}
        # Precios de T03, T04, T08 y T16: el P de RF-26b del día de la compra.
        self.comprar("BI261008", "2026-09-10", "1000", "9.9516240", self.casa_a)
        self.comprar("BI261008", "2026-09-10", "500", "9.9516240", self.casa_b)
        self.comprar("BI261217", "2026-09-17", "1000", "9.8344372", self.casa_a)
        self.comprar("BI261105", "2026-10-08", "1000", "9.9528566", self.casa_b)

    def comprar(self, clave: str, fecha: str, cantidad: str, precio: str, casa: int) -> None:
        _id(
            self.c.post(
                f"/api/portafolios/{self.portafolio}/transacciones",
                json={
                    "intermediario_id": casa,
                    "instrumento_id": self.ids[clave],
                    "tipo": "compra",
                    "fecha_concertacion": fecha,
                    "cantidad": cantidad,
                    "precio": precio,
                    "importe_comisiones": "0.00",
                },
            )
        )

    def posiciones(self, corte: str) -> dict[str, dict[str, Any]]:
        vista = _ok(self.c.get(f"/api/portafolios/{self.portafolio}/posiciones", params={"fecha_corte": corte}))
        return {p["instrumento"]["clave"]: p for p in vista["posiciones"]}


@pytest.fixture
def cartera(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> CarteraCetes:
    reloj.fijar_hoy(HOY)
    return CarteraCetes(nueva_cuenta())


def _valuacion_esperada(fecha: str, clave: str) -> dict[str, Any]:
    """La valuación de E19 que corresponde al renglón de `valuacion_cetes.csv`, sin la fuente."""
    fila = next(f for f in leer_csv("valuacion_cetes") if (f["fecha"], f["instrumento_clave"]) == (fecha, clave))
    nodos = [
        {
            "plazo_nominal": fila[f"{lado}_plazo_nominal"],
            "plazo_efectivo": fila[f"{lado}_plazo_efectivo"],
            "valor": fila[f"{lado}_tasa"],
            "fecha_colocacion": fila[f"{lado}_fecha_colocacion"],
        }
        for lado in ("inf", "sup")
    ]
    return {
        "tipo": "estimacion_cetes",
        "dias_por_vencer": fila["d"],
        "caso": fila["caso"],
        "tasa_aplicada": presentar(Decimal(fila["r_por_ciento_anual"]), 5),
        "precio_estimado": fila["p"],
        "tasas_usadas": nodos[:1] if nodos[0] == nodos[1] else nodos,
    }


def _sin_fuente(valuacion: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in valuacion.items() if k != "fuente"}


def test_vencimiento_deja_la_posicion_en_cero(cartera: CarteraCetes) -> None:
    k = cartera
    al_07 = k.posiciones("2026-10-07")["BI261008"]
    assert (al_07["titulos"], al_07["vencida"], al_07["de_demostracion"]) == ("1500", False, False)
    # 1500 × 9.9983308 = 14997.4962
    assert al_07["valor"] == "14997.50"

    al_08 = k.posiciones("2026-10-08")["BI261008"]
    assert (al_08["titulos"], al_08["vencida"], al_08["valuacion"]) == ("0", True, None)
    assert (al_08["costo_total"], al_08["valor"], al_08["resultado_no_realizado"]) == ("0.00", "0.00", "0.00")
    assert k.posiciones("2026-10-14")["BI261008"]["titulos"] == "0"

    # El tablero refleja la liquidación: el 08/10 BI261008 ya no suma valor, y no aparece en la procedencia.
    t = _ok(
        k.c.get(f"/api/portafolios/{k.portafolio}/tablero", params={"inicio": "2026-09-11", "fin": "2026-10-08"})
    )
    procedencia = {p["instrumento"]["clave"]: p["titulos"] for p in t["procedencia"]}
    assert procedencia == {"BI261105": "1000", "BI261217": "1000"}
    serie = {p["fecha"]: p["valor"] for p in t["serie"]}
    totales_07 = _ok(
        k.c.get(f"/api/portafolios/{k.portafolio}/posiciones", params={"fecha_corte": "2026-10-07"})
    )["totales"]["valor"]
    assert serie["2026-10-07"] == totales_07

    # El sistema no creó transacciones: ni la liquidación ni la reinversión (RF-26a crit. 3).
    transacciones = _ok(k.c.get(f"/api/portafolios/{k.portafolio}/transacciones"))
    assert len(transacciones) == 4 and all(t_["tipo"] == "compra" for t_ in transacciones)


def test_rige_la_ultima_colocacion_igual_o_anterior(cartera: CarteraCetes) -> None:
    k = cartera
    al_07 = k.posiciones("2026-10-07")
    # 07/10, d = 1: extremo inferior con la colocación a 28 días del 01/10, no la del 08/10.
    assert _sin_fuente(al_07["BI261008"]["valuacion"]) == _valuacion_esperada("2026-10-07", "BI261008")
    assert al_07["BI261008"]["valuacion"]["tasas_usadas"] == [
        {"plazo_nominal": "28", "plazo_efectivo": "28", "valor": "6.01000", "fecha_colocacion": "2026-10-01"}
    ]
    # BI261217, d = 71: interpolación entre los nodos de 28 y 91 días del 01/10, con dos tasas usadas.
    interpolada = al_07["BI261217"]["valuacion"]
    assert _sin_fuente(interpolada) == _valuacion_esperada("2026-10-07", "BI261217")
    assert interpolada["caso"] == "interpolación"
    assert [n["plazo_nominal"] for n in interpolada["tasas_usadas"]] == ["28", "91"]

    # 14/10: rige la del 08/10; la del 15/10 no (R-14).
    al_14 = k.posiciones("2026-10-14")
    for clave in ("BI261105", "BI261217"):
        valuacion = al_14[clave]["valuacion"]
        assert _sin_fuente(valuacion) == _valuacion_esperada("2026-10-14", clave), clave
        assert {n["fecha_colocacion"] for n in valuacion["tasas_usadas"]} == {"2026-10-08"}, clave
    assert al_14["BI261105"]["valuacion"]["precio_estimado"] == "9.9629213"

    # Procedencia de la tasa (RF-31 crit. 1 y 2): Banco de México con su atribución.
    for valuacion in (al_07["BI261008"]["valuacion"], interpolada, al_14["BI261105"]["valuacion"]):
        fuente = valuacion["fuente"]
        assert {k_: fuente[k_] for k_ in BANXICO} == BANXICO
        assert fuente["fecha_carga"].endswith(("-06:00", "-05:00"))
