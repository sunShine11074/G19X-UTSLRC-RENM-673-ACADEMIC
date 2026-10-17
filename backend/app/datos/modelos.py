"""Modelos de SQLAlchemy de las 13 tablas de 02_crear_esquema.sql (§3.6; 4.3; 4.4).

El esquema lo crean los scripts 02 a 04; estos modelos solo lo describen (nunca `create_all`).
Siguen los privilegios de app_077 (02, «Privilegios de app_077»), así que:
- la identidad es `Identity(always=True)` y nunca se asigna `id`;
- `momento`, `registrada_en`, `incorporada_en` y `valores_sustituidos` los fija la base:
  llevan `server_default` y nunca se asignan;
- se escribe con `insert()`, `update()` y `delete()` explícitos, con el predicado del
  propietario y `RETURNING`; sin `relationship()` de escritura ni `merge`;
- el bloqueo del portafolio es `with_for_update(of=Portafolio)`;
- `cantidad` se pasa como `int` ya validado (03 H);
- los literales van sin acento: 'revocacion' y 'accion'.
"""

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    Date,
    ForeignKey,
    ForeignKeyConstraint,
    Identity,
    Integer,
    MetaData,
    Numeric,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    metadata = MetaData()  # sin esquema: lo resuelve el search_path (public)
    type_annotation_map = {
        int: BigInteger(),
        str: Text(),
        bool: Boolean(),
        Decimal: Numeric(asdecimal=True),  # numeric sin precisión ni escala → Decimal
        date: Date(),
        datetime: TIMESTAMP(timezone=True),
        Any: JSONB(),
    }


def _id() -> Mapped[int]:
    """Llave sustituta que asigna la base (GENERATED ALWAYS AS IDENTITY)."""
    return mapped_column(Identity(always=True), primary_key=True)


class Usuario(Base):
    """app_077: SELECT; INSERT (correo, contrasena_hash, estado); UPDATE (estado, contrasena_hash).

    Ningún UPDATE escribe 'activa' (RD-23).
    """

    __tablename__ = "usuario"

    id: Mapped[int] = _id()
    correo: Mapped[str]
    contrasena_hash: Mapped[str]
    estado: Mapped[str]


class VersionAviso(Base):
    """app_077: SELECT."""

    __tablename__ = "version_aviso"
    __table_args__ = (UniqueConstraint("vigente_desde", name="version_aviso_vigente_desde_uq"),)

    id: Mapped[int] = _id()
    texto: Mapped[str]
    vigente_desde: Mapped[datetime]


class Consentimiento(Base):
    """app_077: SELECT; INSERT (usuario_id, version_aviso_id, tipo, medio). `momento` lo fija la base."""

    __tablename__ = "consentimiento"

    id: Mapped[int] = _id()
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", name="consentimiento_usuario_fk", ondelete="CASCADE")
    )
    version_aviso_id: Mapped[int] = mapped_column(
        ForeignKey("version_aviso.id", name="consentimiento_version_aviso_fk")
    )
    tipo: Mapped[str]
    medio: Mapped[str]
    momento: Mapped[datetime] = mapped_column(server_default=func.now())


class Portafolio(Base):
    """app_077: SELECT; INSERT (usuario_id, nombre, divisa_base); UPDATE (nombre); DELETE.

    Admite `FOR UPDATE OF portafolio` (RF-28).
    """

    __tablename__ = "portafolio"
    __table_args__ = (UniqueConstraint("usuario_id", "id", name="portafolio_usuario_id_uq"),)

    id: Mapped[int] = _id()
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", name="portafolio_usuario_fk", ondelete="CASCADE")
    )
    nombre: Mapped[str]
    divisa_base: Mapped[str]


class Intermediario(Base):
    """app_077: SELECT; INSERT (usuario_id, nombre). Nunca FOR UPDATE ni FOR SHARE."""

    __tablename__ = "intermediario"
    __table_args__ = (UniqueConstraint("usuario_id", "id", name="intermediario_usuario_id_uq"),)

    id: Mapped[int] = _id()
    usuario_id: Mapped[int] = mapped_column(
        ForeignKey("usuario.id", name="intermediario_usuario_fk", ondelete="CASCADE")
    )
    nombre: Mapped[str]


class Instrumento(Base):
    """app_077: SELECT."""

    __tablename__ = "instrumento"
    __table_args__ = (
        UniqueConstraint("clave", name="instrumento_clave_uq"),
        UniqueConstraint("id", "clave", "clase_activo", name="instrumento_id_clave_clase_uq"),
    )

    id: Mapped[int] = _id()
    clave: Mapped[str]
    nombre: Mapped[str]
    divisa: Mapped[str]
    clase_activo: Mapped[str]
    de_demostracion: Mapped[bool]


class EmisionCetes(Base):
    """app_077: SELECT. La llave es el instrumento (sin Identity); FK compuesta del subtipo."""

    __tablename__ = "emision_cetes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["instrumento_id", "clave", "clase_activo"],
            ["instrumento.id", "instrumento.clave", "instrumento.clase_activo"],
            name="emision_cetes_instrumento_fk",
        ),
        UniqueConstraint("vencimiento", name="emision_cetes_vencimiento_uq"),
    )

    instrumento_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    clave: Mapped[str]
    clase_activo: Mapped[str]
    vencimiento: Mapped[date]
    valor_nominal: Mapped[Decimal]


class Transaccion(Base):
    """app_077: SELECT; INSERT de las 9 columnas, sin id ni registrada_en."""

    __tablename__ = "transaccion"
    __table_args__ = (
        ForeignKeyConstraint(
            ["usuario_id", "portafolio_id"],
            ["portafolio.usuario_id", "portafolio.id"],
            name="transaccion_portafolio_fk",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["usuario_id", "intermediario_id"],
            ["intermediario.usuario_id", "intermediario.id"],
            name="transaccion_intermediario_fk",
        ),
    )

    id: Mapped[int] = _id()
    usuario_id: Mapped[int]
    portafolio_id: Mapped[int]
    intermediario_id: Mapped[int]
    instrumento_id: Mapped[int] = mapped_column(
        ForeignKey("instrumento.id", name="transaccion_instrumento_fk")
    )
    tipo: Mapped[str]
    fecha_concertacion: Mapped[date]
    cantidad: Mapped[int] = mapped_column(Integer)
    precio: Mapped[Decimal]
    importe_comisiones: Mapped[Decimal]
    registrada_en: Mapped[datetime] = mapped_column(server_default=func.now())


class FuenteDatos(Base):
    """app_077: SELECT."""

    __tablename__ = "fuente_datos"
    __table_args__ = (UniqueConstraint("nombre", name="fuente_datos_nombre_uq"),)

    id: Mapped[int] = _id()
    nombre: Mapped[str]
    direccion: Mapped[str | None]
    de_demostracion: Mapped[bool]


class VersionLicencia(Base):
    """app_077: SELECT."""

    __tablename__ = "version_licencia"
    __table_args__ = (
        UniqueConstraint("fuente_id", "id", name="version_licencia_fuente_id_uq"),
        UniqueConstraint("fuente_id", "version", name="version_licencia_version_uq"),
    )

    id: Mapped[int] = _id()
    fuente_id: Mapped[int] = mapped_column(ForeignKey("fuente_datos.id", name="version_licencia_fuente_fk"))
    version: Mapped[str]
    usos_permitidos: Mapped[str]
    obligacion_suprimir: Mapped[str | None]
    atribucion: Mapped[str | None]


class CargaDatos(Base):
    """app_077: SELECT. `incorporada_en` y `valores_sustituidos` los fija la base."""

    __tablename__ = "carga_datos"
    __table_args__ = (
        UniqueConstraint("id", "fuente_id", name="carga_datos_id_fuente_uq"),
        ForeignKeyConstraint(
            ["fuente_id", "version_licencia_id"],
            ["version_licencia.fuente_id", "version_licencia.id"],
            name="carga_datos_version_licencia_fk",
        ),
    )

    id: Mapped[int] = _id()
    fuente_id: Mapped[int] = mapped_column(ForeignKey("fuente_datos.id", name="carga_datos_fuente_fk"))
    version_licencia_id: Mapped[int]
    origen: Mapped[str]
    obtenida_en: Mapped[datetime]
    incorporada_en: Mapped[datetime] = mapped_column(server_default=func.now())
    fecha_inicial: Mapped[date]
    fecha_final: Mapped[date]
    resultado: Mapped[str]
    observaciones_incorporadas: Mapped[int] = mapped_column(Integer)
    observaciones_omitidas: Mapped[int] = mapped_column(Integer)
    valores_sustituidos: Mapped[Any] = mapped_column(server_default=text("'[]'::jsonb"))


class PrecioCierre(Base):
    """app_077: SELECT."""

    __tablename__ = "precio_cierre"
    __table_args__ = (
        UniqueConstraint("instrumento_id", "fecha", "fuente_id", name="precio_cierre_instrumento_fecha_fuente_uq"),
        ForeignKeyConstraint(
            ["carga_id", "fuente_id"],
            ["carga_datos.id", "carga_datos.fuente_id"],
            name="precio_cierre_carga_fk",
            ondelete="CASCADE",
        ),
    )

    id: Mapped[int] = _id()
    instrumento_id: Mapped[int] = mapped_column(
        ForeignKey("instrumento.id", name="precio_cierre_instrumento_fk")
    )
    fecha: Mapped[date]
    precio: Mapped[Decimal]
    carga_id: Mapped[int]
    fuente_id: Mapped[int]


class TasaReferencia(Base):
    """app_077: SELECT."""

    __tablename__ = "tasa_referencia"
    __table_args__ = (
        UniqueConstraint("plazo_nominal", "fecha_colocacion", name="tasa_referencia_plazo_fecha_uq"),
    )

    id: Mapped[int] = _id()
    plazo_nominal: Mapped[int] = mapped_column(Integer)
    fecha_colocacion: Mapped[date]
    valor: Mapped[Decimal]
    unidad: Mapped[str]
    plazo_efectivo: Mapped[int] = mapped_column(Integer)
    carga_id: Mapped[int] = mapped_column(
        ForeignKey("carga_datos.id", name="tasa_referencia_carga_fk", ondelete="CASCADE")
    )


MODELOS: tuple[type[Base], ...] = (
    Usuario,
    VersionAviso,
    Consentimiento,
    Portafolio,
    Intermediario,
    Instrumento,
    EmisionCetes,
    Transaccion,
    FuenteDatos,
    VersionLicencia,
    CargaDatos,
    PrecioCierre,
    TasaReferencia,
)
