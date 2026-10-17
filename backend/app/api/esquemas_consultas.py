"""Vistas del intervalo de datos, las posiciones y el tablero (E09, E19 y E20; §4.3; RNF-02; RNF-07; RF-31).

Solo presentan lo que calculó el motor: las cifras derivadas salen de `motor.presentar*` y
los datos cargados (cierre, tasa, valor nominal) con `como_texto`, sin alterar (RD-14). Toda
cifra es cadena (D-37). Los totales vienen del `Corte`, nunca de sumar filas redondeadas, y
el valor al corte del tablero, el último punto de su serie y su valor de mercado salen del
mismo `Decimal` (RNF-02; RF-11 crit. 2).
"""

from collections.abc import Iterable, Mapping
from datetime import date
from typing import Literal

from pydantic import BaseModel

from app import motor
from app.api.comunes import (
    FuenteVista,
    InstrumentoVista,
    PortafolioVista,
    TasaUsadaVista,
    Valuacion,
    ValuacionCetesVista,
    ValuacionCierreVista,
    fuente_vista,
    instrumento_vista,
    portafolio_vista,
)
from app.api.tipos import como_texto
from app.datos.registros import FuenteRegistro, InstrumentoRegistro
from app.servicios.consultas import IntervaloDatos, ResultadoPosiciones, ResultadoTablero

UNIDAD_POR_CIENTO: Literal["%"] = "%"

# ---------------------------------------------------------------------------
# E09
# ---------------------------------------------------------------------------


class PorOmisionVista(BaseModel):
    inicio: date
    fin: date
    fecha_corte: date


class IntervaloVista(BaseModel):
    inicio: date
    fin: date
    hoy: date
    por_omision: PorOmisionVista


def intervalo_vista(r: IntervaloDatos) -> IntervaloVista:
    return IntervaloVista(
        inicio=r.inicio,
        fin=r.fin,
        hoy=r.hoy,
        por_omision=PorOmisionVista(inicio=r.defecto_inicio, fin=r.defecto_fin, fecha_corte=r.defecto_fin),
    )


# ---------------------------------------------------------------------------
# E19
# ---------------------------------------------------------------------------


class PosicionVista(BaseModel):
    instrumento: InstrumentoVista
    titulos: str
    costo_total: str
    valor: str
    resultado_no_realizado: str
    vencida: bool
    de_demostracion: bool
    valuacion: Valuacion | None  # null con 0 títulos (D-24)


class TotalesVista(BaseModel):
    costo_total: str
    valor: str
    resultado_no_realizado: str


class PosicionesVista(BaseModel):
    portafolio: PortafolioVista
    fecha_corte: date
    contiene_datos_de_demostracion: bool
    posiciones: list[PosicionVista]
    totales: TotalesVista


# ---------------------------------------------------------------------------
# E20
# ---------------------------------------------------------------------------


class PeriodoVista(BaseModel):
    inicio: date
    fin: date
    fecha_base: date
    dias: str


class ImporteAlCorteVista(BaseModel):
    valor: str
    unidad: str  # la divisa base del portafolio (RNF-07)
    fecha_corte: date


class PorCientoDelPeriodoVista(BaseModel):
    valor: str
    unidad: Literal["%"]
    inicio: date
    fin: date


class CaidaMaximaVista(PorCientoDelPeriodoVista):
    fecha_pico: date | None  # null con caída 0 (P1-D)
    fecha_valle: date | None


class IndicadoresVista(BaseModel):
    valor_mercado: ImporteAlCorteVista
    resultado_no_realizado: ImporteAlCorteVista
    twr: PorCientoDelPeriodoVista
    maxima_caida: CaidaMaximaVista


class PuntoSerieVista(BaseModel):
    fecha: date
    valor: str


class ProcedenciaVista(BaseModel):
    instrumento: InstrumentoVista
    titulos: str
    valuacion: Valuacion


class TableroVista(BaseModel):
    portafolio: PortafolioVista
    periodo: PeriodoVista
    fecha_corte: date
    sin_datos: bool
    indicadores: IndicadoresVista | None
    serie: list[PuntoSerieVista]
    valor_al_corte: str | None
    contiene_datos_de_demostracion: bool
    procedencia: list[ProcedenciaVista]
    fuentes_del_periodo: list[FuenteVista]


# ---------------------------------------------------------------------------
# Conversión
# ---------------------------------------------------------------------------


def _valuacion(
    p: motor.PosicionInstrumento, fuentes: Mapping[int, FuenteRegistro]
) -> ValuacionCierreVista | ValuacionCetesVista | None:
    """Precio de cierre usado o estimación de CETES, con su fecha y su fuente (RF-26b; RF-31 crit. 2 y 3)."""
    if p.titulos == 0:
        return None
    if p.cetes is not None:
        v = p.cetes
        nodos = (v.inf,) if v.inf == v.sup else (v.inf, v.sup)
        return ValuacionCetesVista(
            tipo="estimacion_cetes",
            dias_por_vencer=str(v.d),
            caso=str(v.caso),
            tasa_aplicada=motor.presentar(v.r, 5),  # D-40
            precio_estimado=motor.presentar(v.p, 7),  # RD-16
            tasas_usadas=[
                TasaUsadaVista(
                    plazo_nominal=str(n.plazo_nominal),
                    plazo_efectivo=str(n.plazo_efectivo),
                    valor=como_texto(n.tasa),
                    fecha_colocacion=n.fecha_colocacion,
                )
                for n in nodos
            ],
            fuente=fuente_vista(fuentes[v.inf.fuente_id]),
        )
    if p.precio is None or p.fecha_precio is None or p.fuente_id is None:
        # No ocurre: con títulos y sin cierre, el motor lanza CifraNoCalculable (RD-24).
        raise ValueError(f"La posición del instrumento {p.instrumento_id} tiene títulos y no tiene precio.")
    return ValuacionCierreVista(
        tipo="precio_cierre",
        precio=como_texto(p.precio),
        fecha_dato=p.fecha_precio,
        fuente=fuente_vista(fuentes[p.fuente_id]),
    )


def _por_clave(
    posiciones: Iterable[motor.PosicionInstrumento], instrumentos: Mapping[int, InstrumentoRegistro]
) -> list[motor.PosicionInstrumento]:
    return sorted(posiciones, key=lambda p: (instrumentos[p.instrumento_id].clave, p.instrumento_id))


def _hay_demostracion(fuentes_usadas: Iterable[int], fuentes: Mapping[int, FuenteRegistro]) -> bool:
    return any(fuentes[f].de_demostracion for f in fuentes_usadas)


def posiciones_vista(r: ResultadoPosiciones) -> PosicionesVista:
    """E19: los instrumentos con transacciones hasta el corte, por clave, incluidos los de 0 títulos (D-24)."""
    corte = r.corte
    filas = []
    for p in _por_clave((p for p in corte.instrumentos if p.tiene_transacciones), r.instrumentos):
        instrumento = r.instrumentos[p.instrumento_id]
        filas.append(
            PosicionVista(
                instrumento=instrumento_vista(instrumento),
                titulos=str(p.titulos),
                costo_total=motor.presentar_importe(p.costo_total),
                valor=motor.presentar_importe(p.valor),
                resultado_no_realizado=motor.presentar_importe(p.resultado_no_realizado),
                vencida=p.vencida,
                de_demostracion=instrumento.de_demostracion,
                valuacion=_valuacion(p, r.fuentes),
            )
        )
    return PosicionesVista(
        portafolio=portafolio_vista(r.portafolio),
        fecha_corte=corte.fecha_corte,
        contiene_datos_de_demostracion=_hay_demostracion(corte.fuentes_usadas, r.fuentes),
        posiciones=filas,
        totales=TotalesVista(
            costo_total=motor.presentar_importe(corte.costo_total),
            valor=motor.presentar_importe(corte.valor),
            resultado_no_realizado=motor.presentar_importe(corte.resultado_no_realizado),
        ),
    )


def tablero_vista(r: ResultadoTablero) -> TableroVista:
    """E20: indicadores con unidad, fecha o periodo, serie diaria y procedencia (RF-11; RNF-07; RF-31)."""
    ind = r.indicadores
    corte = ind.corte_fin
    portafolio = portafolio_vista(r.portafolio)
    periodo = PeriodoVista(inicio=ind.inicio, fin=ind.fin, fecha_base=ind.fecha_base, dias=str(ind.dias))
    if corte.sin_transacciones:  # RF-11 crit. 3; D-22
        return TableroVista(
            portafolio=portafolio,
            periodo=periodo,
            fecha_corte=corte.fecha_corte,
            sin_datos=True,
            indicadores=None,
            serie=[],
            valor_al_corte=None,
            contiene_datos_de_demostracion=False,
            procedencia=[],
            fuentes_del_periodo=[],
        )

    divisa = r.portafolio.divisa_base
    valor_al_corte = motor.presentar_importe(corte.valor)  # el mismo Decimal que el último punto de la serie
    indicadores = IndicadoresVista(
        valor_mercado=ImporteAlCorteVista(valor=valor_al_corte, unidad=divisa, fecha_corte=corte.fecha_corte),
        resultado_no_realizado=ImporteAlCorteVista(
            valor=motor.presentar_importe(corte.resultado_no_realizado), unidad=divisa, fecha_corte=corte.fecha_corte
        ),
        twr=PorCientoDelPeriodoVista(
            valor=motor.presentar_por_ciento(ind.twr), unidad=UNIDAD_POR_CIENTO, inicio=ind.inicio, fin=ind.fin
        ),
        maxima_caida=CaidaMaximaVista(
            valor=motor.presentar_por_ciento(ind.maxima_caida),
            unidad=UNIDAD_POR_CIENTO,
            inicio=ind.inicio,
            fin=ind.fin,
            fecha_pico=ind.fecha_pico,
            fecha_valle=ind.fecha_valle,
        ),
    )
    procedencia = []
    for p in _por_clave((p for p in corte.instrumentos if p.titulos > 0), r.instrumentos):
        valuacion = _valuacion(p, r.fuentes)
        assert valuacion is not None  # títulos > 0
        procedencia.append(
            ProcedenciaVista(
                instrumento=instrumento_vista(r.instrumentos[p.instrumento_id]),
                titulos=str(p.titulos),
                valuacion=valuacion,
            )
        )
    fuentes = sorted((r.fuentes[f] for f in ind.fuentes_usadas), key=lambda f: (f.nombre, f.id))
    return TableroVista(
        portafolio=portafolio,
        periodo=periodo,
        fecha_corte=corte.fecha_corte,
        sin_datos=False,
        indicadores=indicadores,
        serie=[PuntoSerieVista(fecha=d.fecha, valor=motor.presentar_importe(d.valor)) for d in ind.serie],
        valor_al_corte=valor_al_corte,
        contiene_datos_de_demostracion=_hay_demostracion(ind.fuentes_usadas, r.fuentes),
        procedencia=procedencia,
        fuentes_del_periodo=[fuente_vista(f) for f in fuentes],
    )
