"""CPNF-02: una cifra, el mismo texto en todas las vistas (RNF-02; RF-11 crit. 2; §8.4).

Para cada corte y cada periodo de 5.2:
- el valor de mercado de E20, el último punto de su serie y su valor al corte son la misma
  cadena que el total de E19 al mismo corte y que `presentar_importe` del motor;
- el resultado no realizado también coincide entre E19, E20 y el motor;
- dos llamadas seguidas dan el mismo texto;
- ninguna respuesta lleva números JSON con decimales, y los únicos enteros JSON son ids (D-37).

5.2 se carga una sola vez por módulo (§8.1), con la limpieza y las guardias de `bd_limpia`.
"""

from __future__ import annotations

import json
import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI

from app import motor
from app.datos.consultas import cargar_historial
from app.datos.mercado_sql import cargar_mercado
from app.reloj import hoy_cdmx
from tests.comparacion_5_2 import leer_csv
from tests.conftest import BASE_PRUEBAS, PUERTOS_PROHIBIDOS, TABLAS_DE_CUENTA, ClientePrueba, ClusterPg, _misma_ruta
from tests.referencia.cargador import CORREO_ORACULO, Escenario52, abrir_cuenta, cargar_5_2

pytestmark = [pytest.mark.bd, pytest.mark.referencia]

HOY = date(2026, 10, 16)
PRIMER_INICIO = "2026-09-11"
_AUSENTE = object()


@dataclass(frozen=True)
class Cargado:
    escenario: Escenario52
    usuario_id: int


def _limpiar_cuentas(cluster: ClusterPg) -> None:
    """Las mismas guardias y el mismo TRUNCATE que `bd_limpia`, una vez por módulo."""
    with psycopg.connect(cluster.conninfo_dueno, autocommit=True) as dueno:
        fila = dueno.execute(
            "SELECT current_database(), inet_server_port(), current_setting('data_directory')"
        ).fetchone()
        assert fila is not None
        base, puerto, directorio = fila
        if (
            base != BASE_PRUEBAS
            or puerto != cluster.puerto
            or puerto in PUERTOS_PROHIBIDOS
            or not _misma_ruta(directorio, cluster.directorio)
        ):
            pytest.exit("CPNF-02: la conexión no es la del clúster temporal; no se limpió nada.", returncode=3)
        dueno.execute("SET lock_timeout = '15s'")
        dueno.execute(f"TRUNCATE {', '.join(TABLAS_DE_CUENTA)} RESTART IDENTITY")


@pytest.fixture(scope="module")
def cargado(cluster_pg: ClusterPg, app_pruebas: FastAPI) -> Iterator[Cargado]:
    _limpiar_cuentas(cluster_pg)
    previo = app_pruebas.dependency_overrides.get(hoy_cdmx, _AUSENTE)
    app_pruebas.dependency_overrides[hoy_cdmx] = lambda: HOY
    try:
        with ClientePrueba(app_pruebas) as c:
            abrir_cuenta(c, CORREO_ORACULO, secrets.token_urlsafe(18))
            with psycopg.connect(cluster_pg.conninfo_dueno, autocommit=True) as dueno:
                fila = dueno.execute("SELECT id FROM usuario WHERE correo = %s", (CORREO_ORACULO,)).fetchone()
            assert fila is not None
            yield Cargado(cargar_5_2(c), int(fila[0]))
    finally:
        if previo is _AUSENTE:
            app_pruebas.dependency_overrides.pop(hoy_cdmx, None)
        else:
            app_pruebas.dependency_overrides[hoy_cdmx] = previo  # type: ignore[assignment]


def _casos() -> list[tuple[str, str, str]]:
    """(portafolio, inicio, fin): cada periodo de 5.2 y cada corte de 5.2 en cada portafolio."""
    casos = [(f["portafolio_nombre"], f["inicio"], f["fin"]) for f in leer_csv("periodos", "entradas")]
    portafolios = [f["nombre"] for f in leer_csv("portafolios", "entradas")]
    for f in leer_csv("cortes", "entradas"):
        casos.extend((nombre, PRIMER_INICIO, f["fecha_corte"]) for nombre in portafolios)
    return casos


def _sin_flotantes(texto: str) -> Any:
    def prohibido(valor: str) -> Any:
        raise AssertionError(f"Número JSON con decimales en la respuesta: {valor}")

    return json.loads(texto, parse_float=prohibido)


def _solo_ids_enteros(valor: Any, llave: str = "") -> None:
    """Toda cifra es cadena; los únicos enteros JSON son ids (D-37)."""
    if isinstance(valor, dict):
        for k, v in valor.items():
            _solo_ids_enteros(v, k)
    elif isinstance(valor, list):
        for v in valor:
            _solo_ids_enteros(v, llave)
    elif isinstance(valor, int) and not isinstance(valor, bool):
        assert llave == "id" or llave.endswith("_id"), f"Entero JSON en «{llave}»: {valor}"


def _dos_veces(c: httpx.Client, ruta: str, params: dict[str, str]) -> Any:
    """Llama dos veces seguidas, exige el mismo texto y devuelve el JSON revisado."""
    primera, segunda = c.get(ruta, params=params), c.get(ruta, params=params)
    assert primera.status_code == 200, (ruta, params, primera.json())
    assert primera.content == segunda.content, (ruta, params)
    cuerpo = _sin_flotantes(primera.text)
    _solo_ids_enteros(cuerpo)
    return cuerpo


def _corte_del_motor(app: FastAPI, usuario_id: int, portafolio_id: int, corte: date) -> motor.Corte:
    with app.state.fabrica_sesiones() as sesion:
        historial = cargar_historial(sesion, usuario_id, portafolio_id)
        return motor.posiciones(historial, cargar_mercado(sesion, list(historial.instrumentos), corte), corte)


@pytest.mark.parametrize(("portafolio", "inicio", "fin"), _casos())
def test_misma_cifra_en_e19_e20_y_el_motor(
    cargado: Cargado, app_pruebas: FastAPI, portafolio: str, inicio: str, fin: str
) -> None:
    e = cargado.escenario
    pid = e.portafolios[portafolio]
    tablero = _dos_veces(e.cliente, f"/api/portafolios/{pid}/tablero", {"inicio": inicio, "fin": fin})
    posiciones = _dos_veces(e.cliente, f"/api/portafolios/{pid}/posiciones", {"fecha_corte": fin})
    corte = _corte_del_motor(app_pruebas, cargado.usuario_id, pid, date.fromisoformat(fin))
    valor, resultado = motor.presentar_importe(corte.valor), motor.presentar_importe(corte.resultado_no_realizado)

    assert tablero["fecha_corte"] == posiciones["fecha_corte"] == fin
    assert posiciones["totales"] == {
        "costo_total": motor.presentar_importe(corte.costo_total),
        "valor": valor,
        "resultado_no_realizado": resultado,
    }
    if tablero["sin_datos"]:  # Secundario antes del 14/09
        assert corte.sin_transacciones and posiciones["posiciones"] == []
        assert tablero["valor_al_corte"] is None and tablero["serie"] == []
        return
    indicadores = tablero["indicadores"]
    assert (
        indicadores["valor_mercado"]["valor"]
        == tablero["serie"][-1]["valor"]
        == tablero["valor_al_corte"]
        == posiciones["totales"]["valor"]
        == valor
    )
    assert indicadores["resultado_no_realizado"]["valor"] == resultado
    # La procedencia de E20 es la valuación de E19 de los instrumentos con títulos.
    assert tablero["procedencia"] == [
        {"instrumento": p["instrumento"], "titulos": p["titulos"], "valuacion": p["valuacion"]}
        for p in posiciones["posiciones"]
        if p["titulos"] != "0"
    ]


def test_cortes_y_periodos_iguales_a_esperados(cargado: Cargado) -> None:
    """El texto que ve el usuario es el de `esperados/` presentado a 2 decimales."""
    e = cargado.escenario
    for f in leer_csv("posiciones"):
        if f["nivel"] != "portafolio":
            continue
        pid = e.portafolios[f["portafolio"]]
        totales = e.cliente.get(f"/api/portafolios/{pid}/posiciones", params={"fecha_corte": f["fecha_corte"]}).json()[
            "totales"
        ]
        assert totales == {
            "costo_total": motor.presentar_importe(Decimal(f["costo_total"])),
            "valor": motor.presentar_importe(Decimal(f["valor"])),
            "resultado_no_realizado": motor.presentar_importe(Decimal(f["resultado_no_realizado"])),
        }, (f["portafolio"], f["fecha_corte"])
    for f in leer_csv("indicadores"):
        pid = e.portafolios[f["portafolio"]]
        t = e.cliente.get(f"/api/portafolios/{pid}/tablero", params={"inicio": f["inicio"], "fin": f["fin"]}).json()
        assert t["valor_al_corte"] == motor.presentar_importe(Decimal(f["valor_fin"])), f["periodo"]
        assert t["indicadores"]["twr"]["valor"] == motor.presentar_por_ciento(Decimal(f["twr"])), f["periodo"]


@pytest.mark.parametrize("portafolio", ["Principal", "Secundario"])
def test_cada_punto_de_la_serie_es_el_total_de_e19_ese_dia(cargado: Cargado, portafolio: str) -> None:
    e = cargado.escenario
    pid = e.portafolios[portafolio]
    serie = e.cliente.get(f"/api/portafolios/{pid}/tablero").json()["serie"]
    assert len(serie) == 35
    dia = date(2026, 9, 10)
    for punto in serie:
        assert punto["fecha"] == dia.isoformat()
        totales = e.cliente.get(f"/api/portafolios/{pid}/posiciones", params={"fecha_corte": punto["fecha"]}).json()[
            "totales"
        ]
        assert punto["valor"] == totales["valor"], (portafolio, punto["fecha"])
        dia += timedelta(days=1)
