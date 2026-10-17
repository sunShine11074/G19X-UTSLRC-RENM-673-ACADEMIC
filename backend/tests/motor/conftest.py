"""Datos de 5.2 para las pruebas del motor, sin base de datos (§8.2 del diseño).

Lee `entradas/` del oráculo con `Decimal`, asigna ids por llave natural y arma un
`Historial` por portafolio (T01 a T16 en el orden de `ref`) y un `MercadoEnMemoria` con
`precios.csv` y `tasas.csv`. Los ids no siguen el orden alfabético a propósito: así una
dependencia accidental del orden de los ids salta en la comparación.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from decimal import Decimal

import pytest

from app.motor import (
    Cierre,
    Colocacion,
    Historial,
    Instrumento,
    Intervalo,
    MercadoEnMemoria,
    Transaccion,
)
from tests.comparacion_5_2 import fecha_iso, leer_csv


def pytest_configure(config: pytest.Config) -> None:
    # Registra la marca por si la sección de pytest de pyproject.toml aún no la declara.
    config.addinivalue_line("markers", "motor: sin base de datos")


@dataclass(frozen=True)
class Datos52:
    """Escenario de 5.2 armado en memoria."""

    historiales: dict[str, Historial]  # por nombre de portafolio
    mercado: MercadoEnMemoria
    claves: dict[int, str]  # instrumento_id → clave
    intermediarios: dict[int, str]  # intermediario_id → nombre
    refs: dict[str, int]  # ref → transaccion_id
    instrumentos: dict[str, Instrumento]  # por clave
    portafolios: dict[str, int]  # nombre → portafolio_id
    ids_intermediario: dict[str, int]  # nombre → intermediario_id
    transacciones: dict[str, Transaccion]  # por ref
    intervalo: Intervalo  # intervalo de las semillas (parametros.csv)

    def historial_sin(self, portafolio: str, *refs: str) -> Historial:
        """Historial del portafolio sin las transacciones indicadas."""
        h = self.historiales[portafolio]
        excluidas = {self.refs[r] for r in refs}
        return Historial(h.portafolio_id, tuple(t for t in h.transacciones if t.id not in excluidas), h.instrumentos)


def _armar() -> Datos52:
    filas_instrumentos = leer_csv("instrumentos", "entradas")
    # Ids por llave natural, en orden inverso al del CSV (DEMOACC = 70, …, BI270318 = 10).
    instrumentos: dict[str, Instrumento] = {}
    for posicion, fila in enumerate(filas_instrumentos):
        es_cetes = fila["clase_activo"] == "cetes"
        instrumentos[fila["clave"]] = Instrumento(
            id=10 * (len(filas_instrumentos) - posicion),
            clave=fila["clave"],
            clase_activo=fila["clase_activo"],  # type: ignore[arg-type]
            vencimiento=fecha_iso(fila["vencimiento"]) if es_cetes else None,
            valor_nominal=Decimal(fila["valor_nominal"]) if es_cetes else None,
        )

    filas_intermediarios = leer_csv("intermediarios", "entradas")
    ids_intermediario = {
        fila["nombre"]: len(filas_intermediarios) - posicion for posicion, fila in enumerate(filas_intermediarios)
    }  # Casa A = 2, Casa B = 1
    portafolios = {fila["nombre"]: posicion + 1 for posicion, fila in enumerate(leer_csv("portafolios", "entradas"))}
    fuentes = {fila["nombre"]: posicion + 1 for posicion, fila in enumerate(leer_csv("fuentes_datos", "entradas"))}

    transacciones: dict[str, Transaccion] = {}
    for posicion, fila in enumerate(sorted(leer_csv("transacciones", "entradas"), key=lambda f: f["ref"])):
        transacciones[fila["ref"]] = Transaccion(
            id=101 + posicion,
            portafolio_id=portafolios[fila["portafolio_nombre"]],
            intermediario_id=ids_intermediario[fila["intermediario_nombre"]],
            instrumento_id=instrumentos[fila["instrumento_clave"]].id,
            tipo=fila["tipo"],  # type: ignore[arg-type]
            fecha_concertacion=fecha_iso(fila["fecha_concertacion"]),
            cantidad=int(fila["cantidad"]),
            precio=Decimal(fila["precio"]),
            importe_comisiones=Decimal(fila["importe_comisiones"]),
        )

    por_id = {i.id: i for i in instrumentos.values()}
    historiales: dict[str, Historial] = {}
    for nombre, portafolio_id in portafolios.items():
        propias = tuple(t for t in transacciones.values() if t.portafolio_id == portafolio_id)
        usados = {t.instrumento_id: por_id[t.instrumento_id] for t in propias}
        historiales[nombre] = Historial(portafolio_id, propias, usados)

    cierres = [
        Cierre(
            instrumento_id=instrumentos[fila["instrumento_clave"]].id,
            fecha=fecha_iso(fila["fecha"]),
            precio=Decimal(fila["precio"]),
            fuente_id=fuentes[fila["fuente_nombre"]],
        )
        for fila in leer_csv("precios", "entradas")
    ]
    colocaciones = [
        Colocacion(
            plazo_nominal=int(fila["plazo_nominal"]),
            fecha_colocacion=fecha_iso(fila["fecha_colocacion"]),
            valor=Decimal(fila["valor"]),
            plazo_efectivo=int(fila["plazo_efectivo"]),
            fuente_id=fuentes[fila["fuente_nombre"]],
        )
        for fila in leer_csv("tasas", "entradas")
    ]

    parametros = {fila["parametro"]: fila["valor"] for fila in leer_csv("parametros", "entradas")}
    return Datos52(
        historiales=historiales,
        mercado=MercadoEnMemoria(cierres, colocaciones),
        claves={i.id: clave for clave, i in instrumentos.items()},
        intermediarios={i: nombre for nombre, i in ids_intermediario.items()},
        refs={ref: t.id for ref, t in transacciones.items() if t.id is not None},
        instrumentos=instrumentos,
        portafolios=portafolios,
        ids_intermediario=ids_intermediario,
        transacciones=transacciones,
        intervalo=Intervalo(
            fecha_iso(parametros["intervalo_semillas_inicio"]),
            fecha_iso(parametros["intervalo_semillas_fin"]),
        ),
    )


@pytest.fixture(scope="session")
def datos_5_2() -> Iterator[Datos52]:
    """Escenario de 5.2 en memoria (entradas congeladas en 11097f8)."""
    yield _armar()
