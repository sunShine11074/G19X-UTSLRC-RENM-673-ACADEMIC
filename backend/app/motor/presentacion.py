"""Presentación: la única función de redondeo del sistema (RD-13; RD-16; RF-05 crit. 1; 4.2 «Motor»).

Redondea con la mitad alejándose de cero dentro de CONTEXTO, quita el signo del cero
(«-0.00» → «0.00»; D-39) y escribe sin exponente ni separador de miles.
"""

from decimal import ROUND_HALF_UP, Decimal

from .contexto import calculo

_DECIMALES_POR_TITULO = 7
_MINIMO_POR_TITULO = 2


def _exigir_decimal(valor: object) -> Decimal:
    if not isinstance(valor, Decimal):
        raise TypeError(f"Solo se presentan Decimal, no {type(valor).__name__}.")
    if not valor.is_finite():
        raise ValueError("Solo se presentan números finitos.")
    return valor


@calculo
def presentar(valor: Decimal, decimales: int) -> str:
    """Cifra con `decimales` decimales exactos, mitad alejándose de cero y sin «-0»."""
    _exigir_decimal(valor)
    if type(decimales) is not int or decimales < 0:
        raise ValueError("decimales debe ser un entero no negativo.")
    cuanto = Decimal((0, (1,), -decimales))
    redondeado = valor.quantize(cuanto, rounding=ROUND_HALF_UP)
    if redondeado.is_zero():
        redondeado = redondeado.copy_abs()
    return format(redondeado, "f")


@calculo
def presentar_importe(valor: Decimal) -> str:
    """Importe en pesos con 2 decimales: 425.205 → "425.21"."""
    return presentar(valor, 2)


@calculo
def presentar_por_ciento(fraccion: Decimal) -> str:
    """Fracción expresada en por ciento con 2 decimales: -0.0668… → "-6.68"."""
    return presentar(_exigir_decimal(fraccion).scaleb(2), 2)


@calculo
def presentar_por_titulo(valor: Decimal) -> str:
    """Costo o ingreso por título: hasta 7 decimales, sin ceros finales y al menos 2 (D-14)."""
    texto = presentar(valor, _DECIMALES_POR_TITULO)
    entero, fraccion = texto.split(".")
    fraccion = fraccion.rstrip("0")
    if len(fraccion) < _MINIMO_POR_TITULO:
        fraccion = fraccion.ljust(_MINIMO_POR_TITULO, "0")
    return f"{entero}.{fraccion}"
