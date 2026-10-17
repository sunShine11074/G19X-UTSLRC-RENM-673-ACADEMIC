"""Errores del motor único (§5.7 del diseño).

`app.errores` los traduce a respuestas HTTP; aquí solo se describe la causa, sin datos
del usuario.
"""

from datetime import date
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .modelos import Intervalo


class ErrorMotor(Exception):
    """Base de los errores del motor."""


class CifraNoCalculable(ErrorMotor):
    """Falta un precio o una tasa para valuar una posición con títulos (RD-24)."""

    def __init__(
        self,
        instrumento_id: int,
        fecha: date,
        motivo: str,
        *,
        clave: str | None = None,
    ) -> None:
        self.instrumento_id = instrumento_id
        self.fecha = fecha
        self.motivo = motivo
        self.clave = clave
        super().__init__(f"No se puede valuar el instrumento {instrumento_id} al {fecha.isoformat()}: {motivo}")


class PeriodoInvalido(ErrorMotor):
    """Periodo o fecha de corte fuera de lo que admiten los datos (RF-09 crit. 3; RD-07).

    `codigo` es "periodo_invertido", "periodo_fuera_de_intervalo" o "fecha_fuera_de_intervalo".
    `intervalo` es el intervalo efectivo con el que se validó.
    """

    def __init__(self, codigo: str, regla: str, intervalo: "Intervalo") -> None:
        self.codigo = codigo
        self.regla = regla
        self.intervalo = intervalo
        super().__init__(f"{codigo} ({regla})")


class HistorialInvalido(ErrorMotor):
    """El historial viola una regla que la base y la API ya debieron impedir (defensa de RNF-01)."""

    def __init__(self, motivo: str) -> None:
        self.motivo = motivo
        super().__init__(motivo)
