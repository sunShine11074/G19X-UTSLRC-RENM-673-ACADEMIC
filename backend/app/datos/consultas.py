"""Lecturas compartidas por los servicios: intervalo de las semillas, catálogo y transacciones (§3.7).

Construye además las entradas del motor (`Historial`, `Instrumento`, `Transaccion`) desde la
base. Toda consulta de transacciones filtra por `usuario_id` (RD-01; RF-02).
"""

from collections.abc import Collection
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app import motor
from app.datos.modelos import CargaDatos, EmisionCetes, Instrumento, Intermediario, Transaccion
from app.datos.registros import InstrumentoRegistro, IntermediarioRegistro, TransaccionRegistro
from app.errores import SinDatosDeMercado

_COLUMNAS_INSTRUMENTO = (
    Instrumento.id,
    Instrumento.clave,
    Instrumento.nombre,
    Instrumento.clase_activo,
    Instrumento.divisa,
    Instrumento.de_demostracion,
    EmisionCetes.vencimiento,
    EmisionCetes.valor_nominal,
)


def _con_emision(consulta: Select[Any]) -> Select[Any]:
    """Agrega la emisión de CETES (si la hay) a una consulta que ya incluye instrumento."""
    return consulta.outerjoin(EmisionCetes, EmisionCetes.instrumento_id == Instrumento.id)


def _instrumento_registro(fila: Any) -> InstrumentoRegistro:
    return InstrumentoRegistro(
        id=fila.id,
        clave=fila.clave,
        nombre=fila.nombre,
        clase_activo=fila.clase_activo,
        divisa=fila.divisa,
        de_demostracion=fila.de_demostracion,
        vencimiento=fila.vencimiento,
        valor_nominal=fila.valor_nominal,
    )


def intervalo_semillas(sesion: Session) -> motor.Intervalo:
    """Intervalo que cubren los datos de mercado: [max(fecha_inicial), min(fecha_final)] (D-16).

    Solo cuenta las cargas «semilla» exitosas. Sin cargas, o sin días en común, no hay datos
    de mercado utilizables → SinDatosDeMercado (503).
    """
    inicio, fin = sesion.execute(
        select(func.max(CargaDatos.fecha_inicial), func.min(CargaDatos.fecha_final)).where(
            CargaDatos.origen == "semilla", CargaDatos.resultado == "exitosa"
        )
    ).one()
    if inicio is None or fin is None or inicio > fin:
        raise SinDatosDeMercado()
    return motor.Intervalo(inicio=inicio, fin=fin)


def leer_instrumentos(sesion: Session, ids: Collection[int] | None = None) -> dict[int, InstrumentoRegistro]:
    """Instrumentos del catálogo con su emisión de CETES, ordenados por clave.

    Con `ids`, solo esos (los que no existan simplemente no aparecen).
    """
    consulta = _con_emision(select(*_COLUMNAS_INSTRUMENTO))
    if ids is not None:
        if not ids:
            return {}
        consulta = consulta.where(Instrumento.id.in_(list(ids)))
    consulta = consulta.order_by(Instrumento.clave, Instrumento.id)
    return {fila.id: _instrumento_registro(fila) for fila in sesion.execute(consulta)}


def leer_transacciones(sesion: Session, usuario_id: int, portafolio_id: int) -> list[TransaccionRegistro]:
    """Transacciones del portafolio del usuario, por fecha de concertación y luego por id."""
    consulta = _con_emision(
        select(
            Transaccion.id.label("transaccion_id"),
            Transaccion.portafolio_id,
            Transaccion.tipo,
            Transaccion.fecha_concertacion,
            Transaccion.cantidad,
            Transaccion.precio,
            Transaccion.importe_comisiones,
            Transaccion.registrada_en,
            Intermediario.id.label("intermediario_id"),
            Intermediario.nombre.label("intermediario_nombre"),
            *_COLUMNAS_INSTRUMENTO,
        )
        .join(
            Intermediario,
            (Intermediario.id == Transaccion.intermediario_id) & (Intermediario.usuario_id == Transaccion.usuario_id),
        )
        .join(Instrumento, Instrumento.id == Transaccion.instrumento_id)
    )
    consulta = consulta.where(
        Transaccion.usuario_id == usuario_id, Transaccion.portafolio_id == portafolio_id
    ).order_by(Transaccion.fecha_concertacion, Transaccion.id)
    return [
        TransaccionRegistro(
            id=fila.transaccion_id,
            portafolio_id=fila.portafolio_id,
            intermediario=IntermediarioRegistro(id=fila.intermediario_id, nombre=fila.intermediario_nombre),
            instrumento=_instrumento_registro(fila),
            tipo=fila.tipo,
            fecha_concertacion=fila.fecha_concertacion,
            cantidad=fila.cantidad,
            precio=fila.precio,
            importe_comisiones=fila.importe_comisiones,
            registrada_en=fila.registrada_en,
        )
        for fila in sesion.execute(consulta)
    ]


def instrumento_motor(r: InstrumentoRegistro) -> motor.Instrumento:
    """Instrumento del motor; vencimiento y valor nominal solo en CETES (RF-04)."""
    return motor.Instrumento(
        id=r.id,
        clave=r.clave,
        clase_activo=r.clase_activo,  # type: ignore[arg-type]  # 'accion', 'etf', 'fibra' o 'cetes', sin acento
        vencimiento=r.vencimiento,
        valor_nominal=r.valor_nominal,
    )


def transaccion_motor(r: TransaccionRegistro) -> motor.Transaccion:
    """Transacción registrada, como entrada del motor."""
    return motor.Transaccion(
        id=r.id,
        portafolio_id=r.portafolio_id,
        intermediario_id=r.intermediario.id,
        instrumento_id=r.instrumento.id,
        tipo=r.tipo,  # type: ignore[arg-type]  # 'compra' o 'venta' (transaccion_tipo_ck)
        fecha_concertacion=r.fecha_concertacion,
        cantidad=r.cantidad,
        precio=r.precio,
        importe_comisiones=r.importe_comisiones,
    )


def cargar_historial(sesion: Session, usuario_id: int, portafolio_id: int) -> motor.Historial:
    """Todas las transacciones del portafolio, de cualquier fecha, y los instrumentos que usan."""
    registros = leer_transacciones(sesion, usuario_id, portafolio_id)
    instrumentos = {r.instrumento.id: instrumento_motor(r.instrumento) for r in registros}
    return motor.Historial(
        portafolio_id=portafolio_id,
        transacciones=tuple(transaccion_motor(r) for r in registros),
        instrumentos=instrumentos,
    )
