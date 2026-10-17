"""Aritmética decimal del motor único (RD-12; RD-16; P-13; 4.2 «Aritmética decimal»).

Cada función pública del motor corre dentro de un contexto local con 28 dígitos y la
mitad alejándose de cero. El contexto global del hilo nunca se lee ni se modifica.
"""

from collections.abc import Callable
from decimal import (
    ROUND_HALF_UP,
    Context,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    Overflow,
    localcontext,
)
from functools import wraps
from typing import ParamSpec, TypeVar

CONTEXTO = Context(
    prec=28,
    rounding=ROUND_HALF_UP,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)
"""Contexto de todo cálculo: 28 dígitos significativos y mitad alejándose de cero."""

SIETE = Decimal("0.0000001")
"""Cuantización del precio de CETES (7 decimales; RD-16)."""

CERO = Decimal(0)
UNO = Decimal(1)

_P = ParamSpec("_P")
_R = TypeVar("_R")


def calculo(funcion: Callable[_P, _R]) -> Callable[_P, _R]:
    """Envuelve una función pública para que calcule en una copia local de CONTEXTO.

    El contexto es propio de cada llamada; FastAPI ejecuta las rutas síncronas en hilos.
    """

    @wraps(funcion)
    def envoltura(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        with localcontext(CONTEXTO):
            return funcion(*args, **kwargs)

    return envoltura


_COMPARACION = Context(
    prec=20,
    rounding=ROUND_HALF_UP,
    traps=[InvalidOperation, DivisionByZero, Overflow],
)


@calculo
def para_comparar(valor: Decimal) -> Decimal:
    """`valor` a 20 dígitos significativos, solo para comparar I(t) y caídas (D-20).

    El índice se encadena a 28 dígitos, así que un empate exacto (el valor vuelve a un nivel
    anterior) puede diferir en el último dígito. Comparar a 20 dígitos conserva el empate. El
    resultado nunca se guarda ni se presenta: las cifras siguen sin redondear (RD-16).
    """
    return _COMPARACION.plus(valor)
