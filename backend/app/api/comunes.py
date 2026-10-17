"""Modelos de respuesta compartidos y conversores desde los registros (§3.5).

Todos los campos numéricos son `str`, nunca `Decimal` ni `float`: `jsonable_encoder`
convertiría un `Decimal` a `float` (RD-12). Los datos capturados o cargados salen con
`como_texto`; las cifras derivadas, solo de `app.motor.presentar*` (§5.8).
"""

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from app.api.tipos import como_texto
from app.datos.registros import FuenteRegistro, InstrumentoRegistro, IntermediarioRegistro, PortafolioRegistro
from app.reloj import momento_iso


class PortafolioVista(BaseModel):
    id: int
    nombre: str
    divisa_base: str


class IntermediarioVista(BaseModel):
    id: int
    nombre: str


class InstrumentoVista(BaseModel):
    id: int
    clave: str
    nombre: str
    clase_activo: str
    divisa: str
    de_demostracion: bool
    vencimiento: date | None
    valor_nominal: str | None  # "10.00", tal como se cargó


class FuenteVista(BaseModel):
    nombre: str
    direccion: str | None
    de_demostracion: bool
    atribucion: str | None
    fecha_carga: str  # ISO 8601 con el desfase de la Ciudad de México


class TasaUsadaVista(BaseModel):
    plazo_nominal: str
    plazo_efectivo: str
    valor: str
    fecha_colocacion: date


class ValuacionCierreVista(BaseModel):
    tipo: Literal["precio_cierre"]
    precio: str
    fecha_dato: date  # fecha del cierre usado (RF-31 crit. 3)
    fuente: FuenteVista


class ValuacionCetesVista(BaseModel):
    tipo: Literal["estimacion_cetes"]
    dias_por_vencer: str
    caso: str
    tasa_aplicada: str
    precio_estimado: str
    tasas_usadas: list[TasaUsadaVista]  # RF-26b; RF-31 crit. 2
    fuente: FuenteVista


Valuacion = Annotated[ValuacionCierreVista | ValuacionCetesVista, Field(discriminator="tipo")]


def portafolio_vista(r: PortafolioRegistro) -> PortafolioVista:
    return PortafolioVista(id=r.id, nombre=r.nombre, divisa_base=r.divisa_base)


def intermediario_vista(r: IntermediarioRegistro) -> IntermediarioVista:
    return IntermediarioVista(id=r.id, nombre=r.nombre)


def instrumento_vista(r: InstrumentoRegistro) -> InstrumentoVista:
    return InstrumentoVista(
        id=r.id,
        clave=r.clave,
        nombre=r.nombre,
        clase_activo=r.clase_activo,
        divisa=r.divisa,
        de_demostracion=r.de_demostracion,
        vencimiento=r.vencimiento,
        valor_nominal=None if r.valor_nominal is None else como_texto(r.valor_nominal),
    )


def fuente_vista(r: FuenteRegistro) -> FuenteVista:
    return FuenteVista(
        nombre=r.nombre,
        direccion=r.direccion,
        de_demostracion=r.de_demostracion,
        atribucion=r.atribucion,
        fecha_carga=momento_iso(r.fecha_carga),
    )
