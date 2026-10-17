"""Cuerpos de entrada de portafolios e intermediarios (E11, E13, E15 y E16; §4.3).

Las respuestas usan los modelos compartidos de `app.api.comunes` (PortafolioVista,
IntermediarioVista e InstrumentoVista).
"""

from typing import Annotated, Any

from pydantic import AfterValidator, Field, field_validator
from pydantic.json_schema import SkipJsonSchema
from pydantic_core import PydanticCustomError

from app.api.tipos import ModeloEntrada, Nombre
from app.servicios.portafolios import DIVISA_BASE


def _codificable(valor: str) -> str:
    """Rechaza un sustituto suelto (p. ej. \\ud800), que JSON admite pero PostgreSQL no puede guardar."""
    try:
        valor.encode("utf-8")
    except UnicodeEncodeError:
        raise PydanticCustomError(
            "dato_invalido", "El nombre tiene caracteres no válidos.", {"regla": "RD-03"}
        ) from None
    return valor


# Nombre de portafolio o intermediario: el de §3.5 (D-44), además codificable en UTF-8.
NombreCapturado = Annotated[Nombre, AfterValidator(_codificable)]


class CuerpoPortafolio(ModeloEntrada):
    """E13: crear un portafolio. La única divisa base del MVP es MXN (RD-08)."""

    nombre: NombreCapturado
    divisa_base: str = Field(default=DIVISA_BASE, examples=[DIVISA_BASE])

    @field_validator("divisa_base", mode="before")
    @classmethod
    def _solo_mxn(cls, valor: object) -> object:
        if valor != DIVISA_BASE:
            raise PydanticCustomError(
                "dato_invalido", "En esta versión la única divisa base es MXN.", {"regla": "RD-08"}
            )
        return valor


class CuerpoRenombrar(ModeloEntrada):
    """E15: solo se puede cambiar el nombre (RF-03 crit. 1); la divisa base no se modifica."""

    nombre: NombreCapturado
    # Se declara solo para dar un mensaje propio si alguien la envía; no aparece en OpenAPI.
    divisa_base: SkipJsonSchema[Any] = None

    @field_validator("divisa_base", mode="before")
    @classmethod
    def _rechazar_divisa(cls, valor: object) -> object:
        raise PydanticCustomError("dato_invalido", "Solo se puede cambiar el nombre.", {"regla": "RF-03"})


class CuerpoEliminar(ModeloEntrada):
    """E16: confirmación con el nombre del portafolio (RF-03 crit. 3; RD-10; D-10)."""

    confirmacion: str


class CuerpoIntermediario(ModeloEntrada):
    """E11: registrar un intermediario (RF-25)."""

    nombre: NombreCapturado
