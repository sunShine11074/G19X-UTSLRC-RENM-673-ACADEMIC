"""Datos de mercado de la base para el motor, y procedencia de cada dato (§3.7; 4.2 «Adaptadores de datos»; RF-31).

`cargar_mercado` arma el `MercadoEnMemoria` que el motor lee por la interfaz `DatosMercado`;
las reglas «último cierre igual o anterior» y «última colocación de cada plazo» viven solo en
el motor. Solo cuentan los datos de las cargas exitosas, las mismas que definen el intervalo
de las semillas (D-16). Ningún módulo escribe en el código el nombre de una fuente: la
procedencia sale de `fuente_datos`, `version_licencia` y `carga_datos` (RF-31).
"""

from collections.abc import Collection
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import motor
from app.datos.modelos import CargaDatos, FuenteDatos, PrecioCierre, TasaReferencia, VersionLicencia
from app.datos.registros import FuenteRegistro

CARGA_EXITOSA = "exitosa"  # carga_datos_resultado_ck: 'exitosa' o 'fallida'


def cargar_mercado(sesion: Session, instrumento_ids: Collection[int], hasta: date) -> motor.MercadoEnMemoria:
    """Cierres de esos instrumentos y colocaciones de CETES con fecha ≤ hasta, con la fuente de cada dato.

    A lo más un cierre por (instrumento, fecha): si la base trae más de uno, `MercadoEnMemoria`
    lanza ValueError (RD-19; en el MVP hay una sola fuente de precios).
    """
    ids = sorted(set(instrumento_ids))
    cierres: list[motor.Cierre] = []
    if ids:
        consulta_cierres = (
            select(PrecioCierre.instrumento_id, PrecioCierre.fecha, PrecioCierre.precio, PrecioCierre.fuente_id)
            .join(
                CargaDatos,
                (CargaDatos.id == PrecioCierre.carga_id) & (CargaDatos.fuente_id == PrecioCierre.fuente_id),
            )
            .where(
                PrecioCierre.instrumento_id.in_(ids),
                PrecioCierre.fecha <= hasta,
                CargaDatos.resultado == CARGA_EXITOSA,
            )
            .order_by(PrecioCierre.instrumento_id, PrecioCierre.fecha, PrecioCierre.fuente_id)
        )
        cierres = [
            motor.Cierre(instrumento_id=f.instrumento_id, fecha=f.fecha, precio=f.precio, fuente_id=f.fuente_id)
            for f in sesion.execute(consulta_cierres)
        ]

    consulta_colocaciones = (
        select(
            TasaReferencia.plazo_nominal,
            TasaReferencia.fecha_colocacion,
            TasaReferencia.valor,
            TasaReferencia.plazo_efectivo,
            CargaDatos.fuente_id,
        )
        .join(CargaDatos, CargaDatos.id == TasaReferencia.carga_id)
        .where(TasaReferencia.fecha_colocacion <= hasta, CargaDatos.resultado == CARGA_EXITOSA)
        .order_by(TasaReferencia.fecha_colocacion, TasaReferencia.plazo_nominal)
    )
    colocaciones = [
        motor.Colocacion(
            plazo_nominal=f.plazo_nominal,
            fecha_colocacion=f.fecha_colocacion,
            valor=f.valor,
            plazo_efectivo=f.plazo_efectivo,
            fuente_id=f.fuente_id,
        )
        for f in sesion.execute(consulta_colocaciones)
    ]
    return motor.MercadoEnMemoria(cierres, colocaciones)


def leer_fuentes(sesion: Session) -> dict[int, FuenteRegistro]:
    """Fuentes con al menos una carga exitosa, con la atribución y la fecha de su carga más reciente.

    La atribución es la de la versión de licencia de la carga exitosa más reciente (RF-31 crit. 1);
    `fecha_carga` es max(incorporada_en) de sus cargas exitosas (D-47).
    """
    consulta = (
        select(
            FuenteDatos.id,
            FuenteDatos.nombre,
            FuenteDatos.direccion,
            FuenteDatos.de_demostracion,
            VersionLicencia.atribucion,
            CargaDatos.incorporada_en,
        )
        .join(CargaDatos, CargaDatos.fuente_id == FuenteDatos.id)
        .join(
            VersionLicencia,
            (VersionLicencia.id == CargaDatos.version_licencia_id)
            & (VersionLicencia.fuente_id == CargaDatos.fuente_id),
        )
        .where(CargaDatos.resultado == CARGA_EXITOSA)
        .order_by(FuenteDatos.id, CargaDatos.incorporada_en, CargaDatos.id)
    )
    fuentes: dict[int, FuenteRegistro] = {}
    for f in sesion.execute(consulta):  # ascendente: la última fila de cada fuente es su carga más reciente
        fuentes[f.id] = FuenteRegistro(
            id=f.id,
            nombre=f.nombre,
            direccion=f.direccion,
            de_demostracion=f.de_demostracion,
            atribucion=f.atribucion,
            fecha_carga=f.incorporada_en,
        )
    return fuentes
