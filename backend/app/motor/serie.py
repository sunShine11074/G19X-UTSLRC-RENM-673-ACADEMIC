"""Serie diaria, TWR, índice y máxima caída; validación de periodos y cortes (RF-09; RF-10; RF-11).

- Serie: días naturales de fecha_base = inicio − 1 a fin, inclusive (D-19).
- r(t) = [V(t) + R(t)] / [V(t−1) + A(t)] − 1; con denominador 0 exacto, r(t) = 0 (factor 1).
- I(base) = 1 es el primer máximo; I(t) = I(t−1) × (1 + r(t)); TWR = I(fin) − 1, sin anualizar.
- Máxima caída = min(0, min I(t)/M(t) − 1), medida sobre el índice (RF-10 crit. 2).
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from .contexto import CERO, UNO, calculo, para_comparar
from .errores import PeriodoInvalido
from .kardex import FLUJOS_CERO, Kardex
from .mercado import DatosMercado, IndiceMercado
from .modelos import CaidaMaxima, Corte, DiaSerie, Historial, Indicadores, Intervalo
from .valuacion import valuar

_UN_DIA = timedelta(days=1)


@dataclass(frozen=True, slots=True)
class _Recorrido:
    serie: tuple[DiaSerie, ...]
    corte_fin: Corte
    fuentes_usadas: frozenset[int]


@calculo
def rendimiento_diario(v_anterior: Decimal, v: Decimal, aportaciones: Decimal, retiros: Decimal) -> Decimal:
    """r(t) = (V(t) + R(t)) / (V(t−1) + A(t)) − 1; 0 si el denominador es 0 exacto (RF-09)."""
    denominador = v_anterior + aportaciones
    if denominador == 0:
        return CERO
    return (v + retiros) / denominador - UNO


@calculo
def caida_maxima(fecha_base: date, indices: Sequence[tuple[date, Decimal]]) -> CaidaMaxima:
    """Máxima caída del índice, con pico y valle, en un solo recorrido (RF-10 crit. 1; D-20).

    Empieza con M = 1 en la fecha base. Las comparaciones son estrictas: con un empate se
    conserva el pico más antiguo, y el valle es la primera fecha con la caída mínima. Con
    caída 0, pico y valle quedan en None. Se compara con `para_comparar`, para que el ruido
    del dígito 28 del índice encadenado no rompa un empate exacto.
    """
    maximo = UNO
    fecha_maximo = fecha_base
    minima = CERO
    pico: date | None = None
    valle: date | None = None
    for fecha, indice in indices:
        if para_comparar(indice) > para_comparar(maximo):
            maximo = indice
            fecha_maximo = fecha
        caida = indice / maximo - UNO
        if para_comparar(caida) < para_comparar(minima):
            minima = caida
            valle = fecha
            pico = fecha_maximo
    return CaidaMaxima(maxima_caida=minima, fecha_pico=pico, fecha_valle=valle)


def _recorrer(h: Historial, m: DatosMercado, fecha_base: date, fin: date) -> _Recorrido:
    """Valúa cada día natural de fecha_base a fin y encadena el índice; se llama con @calculo."""
    if not isinstance(h, Historial):
        raise TypeError("Se esperaba un Historial.")
    if fin < fecha_base:
        raise ValueError("La fecha final de la serie es anterior a su fecha base.")
    kardex = Kardex(h)
    indice_mercado = IndiceMercado(m, kardex.instrumentos, fin)
    kardex.avanzar_hasta(fecha_base - _UN_DIA)  # descarta los flujos anteriores a la base

    dias: list[DiaSerie] = []
    fuentes: set[int] = set()
    indice = UNO
    maximo = UNO
    v_anterior = CERO
    corte: Corte | None = None
    fecha = fecha_base
    while fecha <= fin:
        flujos = kardex.avanzar_hasta(fecha).get(fecha, FLUJOS_CERO)
        corte = valuar(kardex, fecha, indice_mercado)
        fuentes |= corte.fuentes_usadas
        retiros = flujos.retiros_ventas + flujos.retiros_vencimientos
        if fecha == fecha_base:
            r: Decimal | None = None  # su A no entra en ningún r
            caida = CERO
        else:
            r = rendimiento_diario(v_anterior, corte.valor, flujos.aportaciones, retiros)
            indice = indice * (UNO + r)
            if para_comparar(indice) > para_comparar(maximo):  # como en caida_maxima (D-20)
                maximo = indice
            caida = indice / maximo - UNO
        dias.append(
            DiaSerie(
                fecha=fecha,
                valor=corte.valor,
                aportaciones=flujos.aportaciones,
                retiros_ventas=flujos.retiros_ventas,
                retiros_vencimientos=flujos.retiros_vencimientos,
                retiros=retiros,
                r=r,
                indice=indice,
                maximo=maximo,
                caida=caida,
            )
        )
        v_anterior = corte.valor
        fecha += _UN_DIA
    if corte is None:  # no ocurre: fin ≥ fecha_base
        raise ValueError("La serie quedó vacía.")
    return _Recorrido(serie=tuple(dias), corte_fin=corte, fuentes_usadas=frozenset(fuentes))


@calculo
def serie_diaria(h: Historial, m: DatosMercado, fecha_base: date, fin: date) -> tuple[DiaSerie, ...]:
    """Serie diaria de RF-09 de fecha_base (I = 1) a fin, un punto por día natural."""
    return _recorrer(h, m, fecha_base, fin).serie


@calculo
def indicadores(h: Historial, m: DatosMercado, inicio: date, fin: date) -> Indicadores:
    """TWR, máxima caída, valor y resultado del periodo [inicio, fin] (RF-09 a RF-11).

    El periodo ya debe estar validado con `validar_periodo`. Sin transacciones devuelve
    ceros, TWR 0 y caída 0, con `corte_fin.sin_transacciones` en True (D-22).
    """
    if fin < inicio:
        raise ValueError("Valida el periodo con validar_periodo antes de calcular.")
    fecha_base = inicio - _UN_DIA
    recorrido = _recorrer(h, m, fecha_base, fin)
    serie = recorrido.serie
    caida = caida_maxima(fecha_base, [(dia.fecha, dia.indice) for dia in serie[1:]])
    corte_fin = recorrido.corte_fin
    return Indicadores(
        portafolio_id=h.portafolio_id,
        inicio=inicio,
        fin=fin,
        fecha_base=fecha_base,
        dias=(fin - inicio).days + 1,
        valor_base=serie[0].valor,
        valor_fin=corte_fin.valor,
        costo_total_fin=corte_fin.costo_total,
        resultado_no_realizado_fin=corte_fin.resultado_no_realizado,
        twr=serie[-1].indice - UNO,
        maxima_caida=caida.maxima_caida,
        fecha_pico=caida.fecha_pico,
        fecha_valle=caida.fecha_valle,
        serie=serie,
        corte_fin=corte_fin,
        fuentes_usadas=recorrido.fuentes_usadas,
    )


@calculo
def validar_periodo(inicio: date, fin: date, intervalo: Intervalo) -> None:
    """Rechaza un periodo invertido o fuera del intervalo efectivo (RF-09 crit. 3; N7 y N8).

    El primer inicio válido es el día siguiente a `intervalo.inicio`, porque la serie parte
    del cierre previo. Un periodo de un solo día es válido.
    """
    if fin < inicio:
        raise PeriodoInvalido("periodo_invertido", "RF-09", intervalo)
    # inicio − 1 < intervalo.inicio, escrito sin restar para no salir del rango de date.
    if inicio <= intervalo.inicio or fin > intervalo.fin:
        raise PeriodoInvalido("periodo_fuera_de_intervalo", "RF-09", intervalo)


@calculo
def validar_corte(corte: date, intervalo: Intervalo) -> None:
    """Rechaza una fecha de corte fuera de [inicio, fin] del intervalo efectivo (RD-07; D-25)."""
    if corte < intervalo.inicio or corte > intervalo.fin:
        raise PeriodoInvalido("fecha_fuera_de_intervalo", "RD-07", intervalo)
