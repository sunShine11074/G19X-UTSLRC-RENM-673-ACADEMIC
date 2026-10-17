"""CPF-07, CPF-30 y CPF-31: semillas de precios y tasas, y procedencia de cada dato (RF-07; RF-30; RF-31; §8.3).

Con el dueño (sin la API):
- 71 precios sintéticos y 32 tasas, cada uno ligado a una carga exitosa con fuente y licencia.
- Ningún precio de una emisión de CETES (RD-04), ≤ 0, con más de 7 decimales, en un día sin
  operaciones de 2026 ni fuera del 10/09 al 14/10.
- Volver a ejecutar 04 no cambia los conteos ni la huella (RF-07 crit. 1; RD-19).
- Los cinco plazos tienen una colocación anterior al 10/09 y ningún plazo efectivo es nulo (RF-30).

Por la API:
- Marcas de demostración en E19 y E20 (RF-07 crit. 3; D-23).
- Atribución del Banco de México y fechas de colocación en los CETES (RF-31 crit. 1 y 2).
- El corte del 13/09 (domingo) usa el cierre del 11/09 (RF-31 crit. 3).
"""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date
from typing import Any

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict

from tests.comparacion_5_2 import leer_csv
from tests.conftest import RUTA_BACKEND, ClientePrueba, ClusterPg, CuentaPrueba, _ejecutar_script

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

HOY = date(2026, 10, 16)
INICIO_SEMILLAS, FIN_SEMILLAS = date(2026, 9, 10), date(2026, 10, 14)
TABLAS_SEMILLA = (
    "version_aviso", "fuente_datos", "version_licencia", "carga_datos", "instrumento", "emision_cetes",
    "precio_cierre", "tasa_referencia",
)
PLAZOS = {28, 91, 182, 364, 728}
MOMENTO_CDMX = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?-0[56]:00")
BANXICO = {
    "nombre": "Banco de México",
    "direccion": "https://www.banxico.org.mx",
    "de_demostracion": False,
    "atribucion": "Fuente: Banco de México, https://www.banxico.org.mx",
}
SEMILLA = {
    "nombre": "Semilla sintetica de demostracion 077",
    "direccion": None,
    "de_demostracion": True,
    "atribucion": "Datos de demostración: precios sintéticos, no son precios reales",
}


def _uno(dueno: psycopg.Connection[Any], consulta: str, *parametros: Any) -> Any:
    fila = dueno.execute(consulta, parametros or None).fetchone()
    assert fila is not None
    return fila[0]


def _huella_semillas(dueno: psycopg.Connection[Any]) -> dict[str, tuple[int, str]]:
    """Conteo y md5 de todas las filas (con sus ids) de cada tabla que carga 04."""
    huella: dict[str, tuple[int, str]] = {}
    for tabla in TABLAS_SEMILLA:
        consulta = sql.SQL("SELECT count(*), md5(coalesce(string_agg(t::text, E'\\n' ORDER BY t::text), '')) FROM {} t")
        fila = dueno.execute(consulta.format(sql.Identifier(tabla))).fetchone()
        assert fila is not None
        huella[tabla] = (int(fila[0]), str(fila[1]))
    return huella


# ---------------------------------------------------------------------------
# Con el dueño
# ---------------------------------------------------------------------------


def test_cpf07_precios_sinteticos(dueno: psycopg.Connection[Any]) -> None:
    assert _uno(dueno, "SELECT count(*) FROM precio_cierre") == 71
    # Ninguno de una emisión de CETES (RD-04).
    assert _uno(dueno, "SELECT count(*) FROM precio_cierre p JOIN emision_cetes e USING (instrumento_id)") == 0
    assert (
        _uno(
            dueno,
            "SELECT count(*) FROM precio_cierre p JOIN instrumento i ON i.id = p.instrumento_id "
            "WHERE i.clase_activo = 'cetes' OR NOT i.de_demostracion",
        )
        == 0
    )
    assert _uno(dueno, "SELECT count(*) FROM precio_cierre WHERE precio <= 0") == 0
    assert _uno(dueno, "SELECT count(*) FROM precio_cierre WHERE min_scale(precio) > 7") == 0
    fechas = {f[0] for f in dueno.execute("SELECT DISTINCT fecha FROM precio_cierre").fetchall()}
    assert min(fechas) >= INICIO_SEMILLAS and max(fechas) <= FIN_SEMILLAS
    sin_operaciones = {date.fromisoformat(f["fecha"]) for f in leer_csv("dias_sin_operaciones_2026", "entradas")}
    assert len(sin_operaciones) == 114
    assert fechas.isdisjoint(sin_operaciones)
    assert date(2026, 9, 16) not in fechas  # festivo


def test_cpf30_tasas_y_plazos(dueno: psycopg.Connection[Any]) -> None:
    assert _uno(dueno, "SELECT count(*) FROM tasa_referencia") == 32
    primeras = dict(
        dueno.execute(
            "SELECT plazo_nominal, min(fecha_colocacion) FROM tasa_referencia GROUP BY plazo_nominal"
        ).fetchall()
    )
    assert set(primeras) == PLAZOS
    assert all(f < INICIO_SEMILLAS for f in primeras.values()), primeras  # RF-30 crit. 1
    assert _uno(dueno, "SELECT count(*) FROM tasa_referencia WHERE plazo_efectivo IS NULL OR plazo_efectivo <= 0") == 0
    assert _uno(dueno, "SELECT count(*) FROM tasa_referencia WHERE unidad <> 'por ciento anual'") == 0
    # Una colocación por plazo y fecha (RF-30 crit. 3).
    distintas = "SELECT count(*) FROM (SELECT DISTINCT plazo_nominal, fecha_colocacion FROM tasa_referencia) x"
    assert _uno(dueno, distintas) == 32


def test_cpf31_cada_dato_con_carga_fuente_y_licencia(dueno: psycopg.Connection[Any]) -> None:
    ligados_precio = _uno(
        dueno,
        "SELECT count(*) FROM precio_cierre p "
        "JOIN carga_datos c ON c.id = p.carga_id AND c.fuente_id = p.fuente_id AND c.resultado = 'exitosa' "
        "JOIN version_licencia l ON l.id = c.version_licencia_id AND l.fuente_id = c.fuente_id "
        "JOIN fuente_datos f ON f.id = c.fuente_id WHERE f.de_demostracion",
    )
    ligadas_tasa = _uno(
        dueno,
        "SELECT count(*) FROM tasa_referencia t "
        "JOIN carga_datos c ON c.id = t.carga_id AND c.resultado = 'exitosa' "
        "JOIN version_licencia l ON l.id = c.version_licencia_id AND l.fuente_id = c.fuente_id "
        "JOIN fuente_datos f ON f.id = c.fuente_id WHERE NOT f.de_demostracion AND l.atribucion = %s",
        BANXICO["atribucion"],
    )
    assert (ligados_precio, ligadas_tasa) == (71, 32)


def test_cpf07_volver_a_ejecutar_04_no_cambia_nada(
    dueno: psycopg.Connection[Any], cluster_pg: ClusterPg
) -> None:
    antes = _huella_semillas(dueno)
    assert antes["precio_cierre"][0] == 71 and antes["tasa_referencia"][0] == 32
    clave = str(conninfo_to_dict(cluster_pg.conninfo_dueno)["password"])
    salida = _ejecutar_script(cluster_pg.bin_dir, cluster_pg.puerto, clave, RUTA_BACKEND / "04_cargar_semillas.sql")
    assert "Semillas listas: 71 precios, 32 tasas" in salida
    assert _huella_semillas(dueno) == antes


# ---------------------------------------------------------------------------
# Por la API
# ---------------------------------------------------------------------------


def _id(respuesta: httpx.Response) -> int:
    assert respuesta.status_code == 201, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _ok(respuesta: httpx.Response) -> Any:
    assert respuesta.status_code == 200, (respuesta.status_code, respuesta.json())
    return respuesta.json()


def _comprar(c: ClientePrueba, portafolio: int, casa: int, instrumento: int, cantidad: str, precio: str) -> None:
    _id(
        c.post(
            f"/api/portafolios/{portafolio}/transacciones",
            json={
                "intermediario_id": casa,
                "instrumento_id": instrumento,
                "tipo": "compra",
                "fecha_concertacion": "2026-09-10",
                "cantidad": cantidad,
                "precio": precio,
                "importe_comisiones": "0.00",
            },
        )
    )


def _fuente(vista: dict[str, Any]) -> dict[str, Any]:
    assert MOMENTO_CDMX.fullmatch(vista["fecha_carga"]), vista["fecha_carga"]
    return {k: v for k, v in vista.items() if k != "fecha_carga"}


def test_marcas_de_demostracion_y_procedencia_por_la_api(
    nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any
) -> None:
    reloj.fijar_hoy(HOY)
    c = nueva_cuenta().cliente
    mixto = _id(c.post("/api/portafolios", json={"nombre": "Mixto"}))
    solo_cetes = _id(c.post("/api/portafolios", json={"nombre": "Solo CETES"}))
    casa = _id(c.post("/api/intermediarios", json={"nombre": "Casa A"}))
    ids = {i["clave"]: i["id"] for i in c.get("/api/instrumentos").json()}
    _comprar(c, mixto, casa, ids["DEMOACC"], "10", "99.95")
    _comprar(c, mixto, casa, ids["BI261008"], "100", "9.9516240")
    _comprar(c, solo_cetes, casa, ids["BI261008"], "100", "9.9516240")

    # E19 al 13/09 (domingo): el cierre usado es el del 11/09 (RF-31 crit. 3).
    e19 = _ok(c.get(f"/api/portafolios/{mixto}/posiciones", params={"fecha_corte": "2026-09-13"}))
    assert e19["contiene_datos_de_demostracion"] is True
    filas = {p["instrumento"]["clave"]: p for p in e19["posiciones"]}
    acc, cetes = filas["DEMOACC"], filas["BI261008"]
    assert (acc["de_demostracion"], acc["instrumento"]["de_demostracion"]) == (True, True)
    assert (cetes["de_demostracion"], cetes["instrumento"]["de_demostracion"]) == (False, False)
    assert acc["valuacion"]["tipo"] == "precio_cierre"
    assert (acc["valuacion"]["precio"], acc["valuacion"]["fecha_dato"]) == ("101.85", "2026-09-11")
    assert _fuente(acc["valuacion"]["fuente"]) == SEMILLA
    assert cetes["valuacion"]["tipo"] == "estimacion_cetes"
    assert cetes["valuacion"]["tasas_usadas"] == [
        {"plazo_nominal": "28", "plazo_efectivo": "28", "valor": "6.25000", "fecha_colocacion": "2026-09-10"}
    ]
    assert _fuente(cetes["valuacion"]["fuente"]) == BANXICO
    assert cetes["instrumento"]["valor_nominal"] == "10.00"

    # E20: las mismas marcas y las fuentes del periodo, por nombre.
    e20 = _ok(c.get(f"/api/portafolios/{mixto}/tablero", params={"inicio": "2026-09-11", "fin": "2026-09-13"}))
    assert e20["contiene_datos_de_demostracion"] is True
    assert [_fuente(f) for f in e20["fuentes_del_periodo"]] == [BANXICO, SEMILLA]
    procedencia = {p["instrumento"]["clave"]: p["valuacion"] for p in e20["procedencia"]}
    assert procedencia == {"BI261008": cetes["valuacion"], "DEMOACC": acc["valuacion"]}

    # Solo con CETES no hay datos de demostración (D-23).
    e19_cetes = _ok(c.get(f"/api/portafolios/{solo_cetes}/posiciones", params={"fecha_corte": "2026-09-13"}))
    assert e19_cetes["contiene_datos_de_demostracion"] is False
    periodo = {"inicio": "2026-09-11", "fin": "2026-09-13"}
    e20_cetes = _ok(c.get(f"/api/portafolios/{solo_cetes}/tablero", params=periodo))
    assert e20_cetes["contiene_datos_de_demostracion"] is False
    assert [_fuente(f) for f in e20_cetes["fuentes_del_periodo"]] == [BANXICO]
