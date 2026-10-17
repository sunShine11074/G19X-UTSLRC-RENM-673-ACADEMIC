"""Valuación de CETES antes de su vencimiento (RF-26b; P-11; R-14; RD-16).

P = VN / (1 + r × d / 36000), con d días naturales por vencer y r la tasa vigente en por
ciento anual, interpolada linealmente por plazo efectivo y sin redondear. Solo P se
redondea, a 7 decimales con la mitad alejándose de cero.
"""

from bisect import bisect_left
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from .contexto import SIETE, UNO, calculo
from .errores import CifraNoCalculable
from .mercado import DatosMercado, IndiceMercado
from .modelos import CasoTasa, Colocacion, Instrumento, NodoTasa, ValuacionCetes

_DIAS_POR_CIEN = Decimal(36000)  # 100 (por ciento) × 360 (año comercial)


def _nodo(colocacion: Colocacion) -> NodoTasa:
    return NodoTasa(
        plazo_nominal=colocacion.plazo_nominal,
        plazo_efectivo=colocacion.plazo_efectivo,
        tasa=colocacion.valor,
        fecha_colocacion=colocacion.fecha_colocacion,
        fuente_id=colocacion.fuente_id,
    )


def _nodos(curva: tuple[Colocacion, ...]) -> list[NodoTasa]:
    """Nodos ordenados por plazo efectivo.

    Con dos plazos efectivos iguales rige la colocación más reciente y, si persiste el
    empate, el menor plazo nominal (D-38).
    """
    por_efectivo: dict[int, Colocacion] = {}
    for colocacion in curva:
        actual = por_efectivo.get(colocacion.plazo_efectivo)
        if actual is None or (colocacion.fecha_colocacion, -colocacion.plazo_nominal) > (
            actual.fecha_colocacion,
            -actual.plazo_nominal,
        ):
            por_efectivo[colocacion.plazo_efectivo] = colocacion
    return [_nodo(por_efectivo[e]) for e in sorted(por_efectivo)]


def _exigir_emision(emision: Instrumento) -> tuple[date, Decimal]:
    if not isinstance(emision, Instrumento):
        raise TypeError("Se esperaba un Instrumento.")
    if not emision.es_cetes or emision.vencimiento is None or emision.valor_nominal is None:
        raise ValueError(f"{emision.clave} no es una emisión de CETES con vencimiento y valor nominal.")
    return emision.vencimiento, emision.valor_nominal


def _valuar_cetes(indice: IndiceMercado, emision: Instrumento, fecha: date) -> ValuacionCetes:
    """Valuación con un índice ya construido; se llama dentro de una función con @calculo."""
    vencimiento, valor_nominal = _exigir_emision(emision)
    d = (vencimiento - fecha).days
    if d < 1:
        raise ValueError(f"La emisión {emision.clave} ya se liquidó: vence el {vencimiento.isoformat()} (RF-26a).")

    nodos = _nodos(indice.curva(fecha))
    if not nodos:
        raise CifraNoCalculable(
            emision.id, fecha, "no hay una colocación con fecha igual o anterior", clave=emision.clave
        )

    efectivos = [n.plazo_efectivo for n in nodos]
    posicion = bisect_left(efectivos, d)
    if posicion < len(nodos) and efectivos[posicion] == d:
        caso = CasoTasa.NODO
        inf = sup = nodos[posicion]
        r = inf.tasa
    elif posicion == 0:
        caso = CasoTasa.EXTREMO_INFERIOR
        inf = sup = nodos[0]
        r = inf.tasa
    elif posicion == len(nodos):
        caso = CasoTasa.EXTREMO_SUPERIOR
        inf = sup = nodos[-1]
        r = inf.tasa
    else:
        caso = CasoTasa.INTERPOLACION
        inf, sup = nodos[posicion - 1], nodos[posicion]
        # Se multiplica antes de dividir; r no se redondea.
        r = inf.tasa + (sup.tasa - inf.tasa) * Decimal(d - inf.plazo_efectivo) / Decimal(
            sup.plazo_efectivo - inf.plazo_efectivo
        )

    p_sin_redondear = valor_nominal / (UNO + r * Decimal(d) / _DIAS_POR_CIEN)
    p = p_sin_redondear.quantize(SIETE, rounding=ROUND_HALF_UP)  # RD-16
    return ValuacionCetes(
        instrumento_id=emision.id,
        fecha=fecha,
        vencimiento=vencimiento,
        d=d,
        caso=caso,
        inf=inf,
        sup=sup,
        r=r,
        p_sin_redondear=p_sin_redondear,
        p=p,
    )


@calculo
def valuar_cetes(m: DatosMercado, emision: Instrumento, fecha: date) -> ValuacionCetes:
    """Valuación de una emisión a una fecha anterior a su vencimiento (RF-26b).

    Rige, en cada plazo nominal, la última colocación con fecha igual o anterior. Lanza
    `CifraNoCalculable` si no hay ninguna y `ValueError` si la emisión ya venció.
    """
    _exigir_emision(emision)
    indice = IndiceMercado(m, (emision,), fecha)
    return _valuar_cetes(indice, emision, fecha)
