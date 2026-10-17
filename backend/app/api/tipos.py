"""Tipos de entrada de la API (§3.5; RD-12 a RD-14; D-37; D-44).

Toda cifra llega como cadena y se valida sin redondear; los ids, como enteros JSON. Los
errores propios se lanzan con `PydanticCustomError(tipo, mensaje, {"regla": "RD-nn"})`: el
manejador de 422 (app.errores) copia solo el mensaje y la regla, nunca el valor recibido.
"""

import re
import unicodedata
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import Path
from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, StrictInt, WithJsonSchema
from pydantic_core import PydanticCustomError

ID_MAXIMO = 9_223_372_036_854_775_807  # bigint
TITULOS_MAXIMO = 2_147_483_647  # integer de transaccion.cantidad
LARGO_MAXIMO_NOMBRE = 120  # D-44
LARGO_MAXIMO_CIFRA = 40

MENSAJE_CIFRA_TEXTO = 'Envía esta cifra como texto, por ejemplo "50.00".'

_PATRON_FECHA = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_PATRON_CIFRA = re.compile(r"(0|[1-9][0-9]*)(\.[0-9]+)?")
_PATRON_TITULOS = re.compile(r"[1-9][0-9]*")

# Cómo se nombra cada cifra en sus mensajes.
_SUJETOS = {"precio": "El precio", "importe_comisiones": "El importe"}


def _error(mensaje: str, regla: str, tipo: str = "dato_invalido") -> PydanticCustomError:
    return PydanticCustomError(tipo, mensaje, {"regla": regla})


class ModeloEntrada(BaseModel):
    """Base de los cuerpos de entrada: un campo desconocido da 422 «Este dato no se puede enviar.»"""

    model_config = ConfigDict(extra="forbid")


def _fecha_estricta(valor: object) -> date:
    if isinstance(valor, str) and _PATRON_FECHA.fullmatch(valor):
        try:
            return date.fromisoformat(valor)
        except ValueError:
            pass
    raise _error("Escribe una fecha válida con el formato AAAA-MM-DD.", "RD-14", "fecha_invalida")


def _nombre(valor: str) -> str:
    # strip(" ") y no strip(): btrim de la base solo quita U+0020 (nota a.5 de 4.4).
    if valor.strip(" ") == "":
        raise _error("Escribe un nombre.", "RD-03")
    if len(valor) > LARGO_MAXIMO_NOMBRE:
        raise _error("El nombre admite a lo más 120 caracteres.", "RD-03")
    if any(unicodedata.category(c) == "Cc" for c in valor):
        raise _error("El nombre no puede tener caracteres de control.", "RD-03")
    return valor  # el valor original, sin recortar (RD-14)


def _titulos(valor: object) -> int:
    if not isinstance(valor, str):
        raise _error(MENSAJE_CIFRA_TEXTO, "RD-12")
    if len(valor) > len(str(TITULOS_MAXIMO)) or not _PATRON_TITULOS.fullmatch(valor) or int(valor) > TITULOS_MAXIMO:
        raise _error("La cantidad de títulos debe ser un entero mayor que cero.", "RD-06")
    return int(valor)


def cifra(campo: str, escala: int, tope: Decimal, positiva: bool) -> Callable[[object], Decimal]:
    """Validador previo de una cifra en texto, sin redondear (RD-12 a RD-14).

    Orden: texto (RD-12); patrón sin signo, separadores ni exponente (RD-14); tope (RD-12);
    mayor que cero si `positiva` (RD-06); escala sin ceros finales, como min_scale (RD-13).
    """
    sujeto = _SUJETOS.get(campo, "La cifra")

    def validar(valor: object) -> Decimal:
        if not isinstance(valor, str):
            raise _error(MENSAJE_CIFRA_TEXTO, "RD-12")
        if len(valor) > LARGO_MAXIMO_CIFRA or not _PATRON_CIFRA.fullmatch(valor):
            if campo == "importe_comisiones" and valor.startswith("-"):
                raise _error("El importe no puede ser negativo.", "RF-05")
            raise _error("Escribe una cifra sin signo, separadores ni exponente.", "RD-14")
        numero = Decimal(valor)  # exacto: no depende del contexto
        if numero >= tope:
            raise _error(f"{sujeto} es demasiado grande.", "RD-12")
        if positiva and numero == 0:
            raise _error(f"{sujeto} debe ser mayor que cero.", "RD-06")
        _, _, decimales = valor.partition(".")
        if len(decimales.rstrip("0")) > escala:
            raise _error(f"{sujeto} admite a lo más {escala} decimales; no se redondea.", "RD-13")
        return numero

    return validar


def _tipo(valor: str) -> str:
    if valor not in ("compra", "venta"):
        raise _error("El tipo debe ser compra o venta.", "RF-05")
    return valor


def _esquema_cifra(ejemplo: str) -> WithJsonSchema:
    return WithJsonSchema({"type": "string", "pattern": _PATRON_CIFRA.pattern, "examples": [ejemplo]})


Identificador = Annotated[StrictInt, Field(ge=1, le=ID_MAXIMO)]  # ids en el cuerpo: entero JSON
IdRuta = Annotated[int, Path(ge=1, le=ID_MAXIMO)]  # ids en la ruta
FechaEstricta = Annotated[date, BeforeValidator(_fecha_estricta)]
Nombre = Annotated[str, AfterValidator(_nombre), WithJsonSchema({"type": "string", "maxLength": LARGO_MAXIMO_NOMBRE})]
Titulos = Annotated[
    int,
    BeforeValidator(_titulos),
    WithJsonSchema({"type": "string", "pattern": _PATRON_TITULOS.pattern, "examples": ["100"]}),
]
Precio = Annotated[
    Decimal,
    BeforeValidator(cifra("precio", escala=7, tope=Decimal("1E+11"), positiva=True)),
    _esquema_cifra("50.00"),
]
Importe = Annotated[
    Decimal,
    BeforeValidator(cifra("importe_comisiones", escala=2, tope=Decimal("1E+16"), positiva=False)),
    _esquema_cifra("14.50"),
]
TipoTransaccion = Annotated[
    str, AfterValidator(_tipo), WithJsonSchema({"type": "string", "enum": ["compra", "venta"]})
]


def como_texto(d: Decimal) -> str:
    """Dato capturado o cargado, sin alterar (RD-14): Decimal("50.00") → "50.00"."""
    return format(d, "f")
