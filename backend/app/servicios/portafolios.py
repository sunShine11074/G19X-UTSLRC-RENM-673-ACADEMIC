"""Portafolios, intermediarios y catálogo (CU-03, CU-04 y CU-08; RF-02 a RF-04; RF-25; §3.9).

Toda consulta o escritura de portafolios e intermediarios lleva el predicado del propietario
(RD-01; RF-02): lo ajeno da el mismo 404 que lo inexistente. La unicidad de los nombres la
decide la base con `lower(btrim(nombre))` (RD-03); el 23505 lo traduce `app.datos.integridad`.
"""

from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.orm import Session

from app.datos.consultas import leer_instrumentos
from app.datos.modelos import Intermediario, Portafolio
from app.datos.registros import InstrumentoRegistro, IntermediarioRegistro, PortafolioRegistro
from app.errores import MENSAJE_CONFIRMAR_PORTAFOLIO, ConfirmacionInvalida, NoEncontrado

DIVISA_BASE = "MXN"  # RD-08: la única divisa base del MVP

_COLUMNAS_PORTAFOLIO = (Portafolio.id, Portafolio.nombre, Portafolio.divisa_base)
_COLUMNAS_INTERMEDIARIO = (Intermediario.id, Intermediario.nombre)


def _portafolio(fila: Any) -> PortafolioRegistro:
    return PortafolioRegistro(id=fila.id, nombre=fila.nombre, divisa_base=fila.divisa_base)


def _intermediario(fila: Any) -> IntermediarioRegistro:
    return IntermediarioRegistro(id=fila.id, nombre=fila.nombre)


def _comparable(texto: str) -> bool:
    """True si el texto se puede enviar a PostgreSQL: sin NUL y codificable en UTF-8."""
    if "\x00" in texto:
        return False
    try:
        texto.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


# ---------------------------------------------------------------------------
# Portafolios (CU-03; RF-03)
# ---------------------------------------------------------------------------


def listar_portafolios(sesion: Session, usuario_id: int) -> list[PortafolioRegistro]:
    """Portafolios del usuario, por nombre sin distinguir mayúsculas y luego por id."""
    consulta = (
        select(*_COLUMNAS_PORTAFOLIO)
        .where(Portafolio.usuario_id == usuario_id)
        .order_by(func.lower(Portafolio.nombre), Portafolio.id)
    )
    return [_portafolio(fila) for fila in sesion.execute(consulta)]


def crear_portafolio(sesion: Session, usuario_id: int, nombre: str) -> PortafolioRegistro:
    """Crea el portafolio en MXN con el nombre tal como se capturó (RF-03 crit. 1 y 2; RD-08; RD-14)."""
    fila = sesion.execute(
        insert(Portafolio)
        .values(usuario_id=usuario_id, nombre=nombre, divisa_base=DIVISA_BASE)
        .returning(*_COLUMNAS_PORTAFOLIO)
    ).one()
    sesion.commit()
    return _portafolio(fila)


def obtener_portafolio(
    sesion: Session, usuario_id: int, portafolio_id: int, *, bloquear: bool = False
) -> PortafolioRegistro:
    """El portafolio del usuario; con `bloquear`, `FOR UPDATE OF portafolio` hasta el commit (RF-28).

    Si no existe o es ajeno → NoEncontrado("portafolio"), idéntico en ambos casos (RNF-03).
    """
    consulta = select(*_COLUMNAS_PORTAFOLIO).where(
        Portafolio.id == portafolio_id, Portafolio.usuario_id == usuario_id
    )
    if bloquear:
        consulta = consulta.with_for_update(of=Portafolio)
    fila = sesion.execute(consulta).one_or_none()
    if fila is None:
        raise NoEncontrado("portafolio")
    return _portafolio(fila)


def renombrar_portafolio(sesion: Session, usuario_id: int, portafolio_id: int, nombre: str) -> PortafolioRegistro:
    """Cambia solo el nombre (RF-03 crit. 1); la divisa base no se modifica."""
    fila = sesion.execute(
        update(Portafolio)
        .where(Portafolio.id == portafolio_id, Portafolio.usuario_id == usuario_id)
        .values(nombre=nombre)
        .returning(*_COLUMNAS_PORTAFOLIO)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if fila is None:
        raise NoEncontrado("portafolio")
    sesion.commit()
    return _portafolio(fila)


def eliminar_portafolio(sesion: Session, usuario_id: int, portafolio_id: int, confirmacion: str) -> None:
    """Elimina el portafolio si la confirmación es su nombre, con la regla de RD-03 (RF-03 crit. 3; D-10).

    La comparación es de la base: `lower(btrim(nombre)) = lower(btrim(:confirmacion))`. Si no
    coincide → ConfirmacionInvalida, sin cambios. La cascada borra sus transacciones y se
    conservan los intermediarios (RD-10). La propiedad ya la comprobó la dependencia de la ruta.
    """
    if not _comparable(confirmacion):
        raise ConfirmacionInvalida(MENSAJE_CONFIRMAR_PORTAFOLIO)
    eliminado = sesion.execute(
        delete(Portafolio)
        .where(
            Portafolio.id == portafolio_id,
            Portafolio.usuario_id == usuario_id,
            func.lower(func.btrim(Portafolio.nombre)) == func.lower(func.btrim(confirmacion)),
        )
        .returning(Portafolio.id)
        .execution_options(synchronize_session=False)
    ).one_or_none()
    if eliminado is None:
        raise ConfirmacionInvalida(MENSAJE_CONFIRMAR_PORTAFOLIO)
    sesion.commit()


# ---------------------------------------------------------------------------
# Intermediarios (CU-04; RF-25; RD-09: se registran y no se modifican ni se eliminan)
# ---------------------------------------------------------------------------


def listar_intermediarios(sesion: Session, usuario_id: int) -> list[IntermediarioRegistro]:
    """Intermediarios del usuario, por nombre sin distinguir mayúsculas y luego por id."""
    consulta = (
        select(*_COLUMNAS_INTERMEDIARIO)
        .where(Intermediario.usuario_id == usuario_id)
        .order_by(func.lower(Intermediario.nombre), Intermediario.id)
    )
    return [_intermediario(fila) for fila in sesion.execute(consulta)]


def crear_intermediario(sesion: Session, usuario_id: int, nombre: str) -> IntermediarioRegistro:
    """Registra el intermediario con el nombre tal como se capturó (RF-25 crit. 1 y 2; RD-14)."""
    fila = sesion.execute(
        insert(Intermediario).values(usuario_id=usuario_id, nombre=nombre).returning(*_COLUMNAS_INTERMEDIARIO)
    ).one()
    sesion.commit()
    return _intermediario(fila)


# ---------------------------------------------------------------------------
# Catálogo (CU-08; RF-04; RD-04; RD-09: solo lectura)
# ---------------------------------------------------------------------------


def listar_instrumentos(sesion: Session) -> list[InstrumentoRegistro]:
    """Catálogo completo, ordenado por clave."""
    return list(leer_instrumentos(sesion).values())
