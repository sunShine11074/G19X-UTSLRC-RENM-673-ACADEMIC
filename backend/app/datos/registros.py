"""Registros de lectura inmutables que devuelven los servicios (§3.7).

Las cifras capturadas o cargadas viajan como `Decimal` sin alterar (RD-14); las rutas las
convierten a texto con `app.api.tipos.como_texto`.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class PortafolioRegistro:
    id: int
    nombre: str
    divisa_base: str


@dataclass(frozen=True, slots=True)
class IntermediarioRegistro:
    id: int
    nombre: str


@dataclass(frozen=True, slots=True)
class InstrumentoRegistro:
    id: int
    clave: str
    nombre: str
    clase_activo: str
    divisa: str
    de_demostracion: bool
    vencimiento: date | None  # solo CETES
    valor_nominal: Decimal | None  # solo CETES


@dataclass(frozen=True, slots=True)
class FuenteRegistro:
    id: int
    nombre: str
    direccion: str | None
    de_demostracion: bool
    atribucion: str | None
    fecha_carga: datetime  # max(carga_datos.incorporada_en) de las cargas exitosas de la fuente (D-47)


@dataclass(frozen=True, slots=True)
class TransaccionRegistro:
    id: int
    portafolio_id: int
    intermediario: IntermediarioRegistro
    instrumento: InstrumentoRegistro
    tipo: str
    fecha_concertacion: date
    cantidad: int
    precio: Decimal
    importe_comisiones: Decimal
    registrada_en: datetime
