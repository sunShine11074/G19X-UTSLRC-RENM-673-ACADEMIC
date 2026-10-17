"""Valuación de un corte: la única función que produce valores (RF-06; RF-08; RF-26a; RF-26b; RF-31).

`posiciones` y cada día de la serie usan `valuar`, así que el total de un corte es la suma
de sus pares y es el mismo V(t) de la serie (RNF-02).
"""

from datetime import date
from decimal import Decimal

from .cetes import _valuar_cetes
from .contexto import CERO, calculo
from .errores import CifraNoCalculable
from .kardex import Kardex
from .mercado import DatosMercado, IndiceMercado
from .modelos import (
    Corte,
    Historial,
    Instrumento,
    PosicionInstrumento,
    PosicionPar,
    PrecioUsado,
    ValuacionCetes,
)


@calculo
def cierre_vigente(m: DatosMercado, instrumento: Instrumento, fecha: date) -> PrecioUsado | None:
    """Cierre de mayor fecha ≤ fecha, sin límite de antigüedad (RF-08 crit. 4; RF-31 crit. 3).

    Un CETES no tiene cierres: devuelve None, o `ValueError` si los datos traen alguno (RD-04).
    """
    if not isinstance(instrumento, Instrumento):
        raise TypeError("cierre_vigente recibe un Instrumento.")
    indice = IndiceMercado(m, (instrumento,), fecha)
    cierre = indice.cierre(instrumento.id, fecha)
    if cierre is None:
        return None
    return PrecioUsado(
        instrumento_id=instrumento.id,
        fecha_valuacion=fecha,
        fecha_cierre=cierre.fecha,
        precio=cierre.precio,
        fuente_id=cierre.fuente_id,
        sin_cierre_ese_dia=cierre.fecha != fecha,
    )


@calculo
def valuar(kardex: Kardex, fecha: date, indice: IndiceMercado) -> Corte:
    """Valúa todos los pares del historial con el estado del kardex a `fecha`.

    - CETES: vencida → 0 títulos y sin precio; con títulos → P de RF-26b; sin títulos → sin precio.
    - Demás clases: el cierre vigente aunque el saldo sea 0; con títulos y sin cierre → CifraNoCalculable.
    - Por par: valor = títulos × precio, costo = títulos × costo unitario y resultado = valor − costo.
    """
    if kardex.fecha != fecha:
        raise ValueError("El kardex debe estar avanzado exactamente a la fecha de valuación.")

    pares: list[PosicionPar] = []
    por_instrumento: list[PosicionInstrumento] = []
    fuentes: set[int] = set()
    for instrumento in kardex.instrumentos:
        vencida = (
            instrumento.es_cetes and instrumento.vencimiento is not None and fecha >= instrumento.vencimiento
        )
        pares_instrumento = kardex.pares_de(instrumento.id)
        titulos_instrumento = sum(kardex.saldo(par) for par in pares_instrumento)

        # Precio del instrumento a la fecha (común a todos sus pares).
        precio: Decimal | None = None
        fecha_precio: date | None = None
        fuente_id: int | None = None
        cetes: ValuacionCetes | None = None
        fuentes_precio: set[int] = set()
        if instrumento.es_cetes:
            if not vencida and titulos_instrumento > 0:
                cetes = _valuar_cetes(indice, instrumento, fecha)
                precio, fecha_precio, fuente_id = cetes.p, fecha, cetes.inf.fuente_id
                fuentes_precio = {cetes.inf.fuente_id, cetes.sup.fuente_id}
        else:
            cierre = indice.cierre(instrumento.id, fecha)
            if cierre is not None:
                precio, fecha_precio, fuente_id = cierre.precio, cierre.fecha, cierre.fuente_id
                fuentes_precio = {cierre.fuente_id}
            elif titulos_instrumento > 0:
                raise CifraNoCalculable(
                    instrumento.id, fecha, "no hay un cierre con fecha igual o anterior", clave=instrumento.clave
                )

        costo_instrumento = CERO
        valor_instrumento = CERO
        tiene_instrumento = False
        for par in pares_instrumento:
            titulos = kardex.saldo(par)
            costo_unitario = kardex.costo_unitario(par)
            costo_total = kardex.costo_total(par)  # = títulos × costo unitario, sin su redondeo
            valor = Decimal(titulos) * precio if titulos > 0 and precio is not None else CERO
            con_precio = precio is not None and (titulos > 0 or not instrumento.es_cetes)
            tiene = kardex.tiene_transacciones(par)
            pares.append(
                PosicionPar(
                    instrumento_id=instrumento.id,
                    intermediario_id=par[1],
                    tiene_transacciones=tiene,
                    titulos=titulos,
                    costo_unitario=costo_unitario,
                    costo_total=costo_total,
                    precio=precio if con_precio else None,
                    fecha_precio=fecha_precio if con_precio else None,
                    fuente_id=fuente_id if con_precio else None,
                    cetes=cetes if titulos > 0 else None,
                    valor=valor,
                    resultado_no_realizado=valor - costo_total,
                )
            )
            if titulos > 0:
                fuentes |= fuentes_precio
            costo_instrumento += costo_total
            valor_instrumento += valor
            tiene_instrumento = tiene_instrumento or tiene

        por_instrumento.append(
            PosicionInstrumento(
                instrumento_id=instrumento.id,
                tiene_transacciones=tiene_instrumento,
                vencida=vencida,
                titulos=titulos_instrumento,
                costo_total=costo_instrumento,
                valor=valor_instrumento,
                resultado_no_realizado=valor_instrumento - costo_instrumento,
                precio=precio,
                fecha_precio=fecha_precio,
                fuente_id=fuente_id,
                cetes=cetes,
            )
        )

    # Totales: suma de los pares, nunca de cifras redondeadas (RNF-02).
    costo_total = CERO
    valor_total = CERO
    for posicion in pares:
        costo_total += posicion.costo_total
        valor_total += posicion.valor
    return Corte(
        portafolio_id=kardex.historial.portafolio_id,
        fecha_corte=fecha,
        pares=tuple(pares),
        instrumentos=tuple(por_instrumento),
        costo_total=costo_total,
        valor=valor_total,
        resultado_no_realizado=valor_total - costo_total,
        sin_transacciones=not any(p.tiene_transacciones for p in pares),
        fuentes_usadas=frozenset(fuentes),
    )


@calculo
def posiciones(h: Historial, m: DatosMercado, corte: date) -> Corte:
    """Posiciones, valor y resultado no realizado del portafolio a una fecha de corte inclusiva."""
    kardex = Kardex(h)
    indice = IndiceMercado(m, kardex.instrumentos, corte)
    kardex.avanzar_hasta(corte)
    return valuar(kardex, corte, indice)
