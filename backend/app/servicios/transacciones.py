"""Listado y registro de transacciones (CU-05 y CU-12; RF-05; RF-26a crit. 2 y 3; RF-28; §4.3 E18).

El registro corre en la transacción de la base que abrió la ruta: la dependencia
`portafolio_propio_bloqueado` ya tomó `FOR UPDATE OF portafolio`, así que dos ventas
concurrentes en el mismo portafolio se serializan y la segunda ve la primera al revisar
el saldo (RF-28; READ COMMITTED). Ningún rechazo registra nada, y el sistema no crea
otras transacciones (RF-26a crit. 3).
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import insert, select
from sqlalchemy.orm import Session

from app import motor
from app.datos.consultas import cargar_historial, intervalo_semillas, leer_instrumentos, leer_transacciones
from app.datos.modelos import Intermediario, Transaccion
from app.datos.registros import IntermediarioRegistro, PortafolioRegistro, TransaccionRegistro
from app.errores import (
    DatosInvalidos,
    DivisaDistinta,
    ErrorCampo,
    FechaEnODespuesDelVencimiento,
    FechaFueraDeIntervalo,
    FechaPosteriorAlRegistro,
    NoEncontrado,
    PlazoCetesExcedido,
    SaldoNegativo,
)

LIMITE_DIAS_CETES = 730  # RD-05 (D-17): 728 días más los 2 de la subasta a la colocación

MENSAJE_IMPORTE_VENTA = "En una venta, el importe de las comisiones debe ser menor que títulos × precio."


@dataclass(frozen=True)
class TransaccionNueva:
    """Datos de una transacción ya validados en su forma (pasos 1 y 2 de E18)."""

    intermediario_id: int
    instrumento_id: int
    tipo: str
    fecha_concertacion: date
    cantidad: int
    precio: Decimal
    importe_comisiones: Decimal


def listar_transacciones(sesion: Session, usuario_id: int, portafolio_id: int) -> list[TransaccionRegistro]:
    """Transacciones del portafolio, por fecha de concertación y luego por id (RF-05, consulta)."""
    return leer_transacciones(sesion, usuario_id, portafolio_id)


def _intermediario_propio(sesion: Session, usuario_id: int, intermediario_id: int) -> IntermediarioRegistro:
    """Paso 4 (RD-02): el intermediario debe ser del usuario; lo ajeno da el mismo 404."""
    fila = sesion.execute(
        select(Intermediario.id, Intermediario.nombre).where(
            Intermediario.id == intermediario_id, Intermediario.usuario_id == usuario_id
        )
    ).one_or_none()
    if fila is None:
        raise NoEncontrado("intermediario")
    return IntermediarioRegistro(id=fila.id, nombre=fila.nombre)


def registrar_transaccion(
    sesion: Session, usuario_id: int, portafolio: PortafolioRegistro, nueva: TransaccionNueva, hoy: date
) -> TransaccionRegistro:
    """Registra una compra o venta si cumple, en este orden, los pasos 3 a 10 de E18 (§4.3).

    3. Venta con importe ≥ títulos × precio → 422 (RF-05 crit. 2).
    4. Intermediario propio → 404 (RD-02).  5. Instrumento existente → 404.
    6. Divisa del instrumento = divisa base → 422 (RD-08).
    7. Fecha ≤ hoy en la Ciudad de México → 422 (RD-07; RD-15).
    8. Fecha dentro del intervalo de las semillas → 422 (RD-07; RF-05 crit. 3).
    9. CETES: fecha anterior al vencimiento (RF-26a crit. 2) y a lo más LIMITE_DIAS_CETES días (RD-05).
    10. CU-12: ningún saldo del par queda negativo en ninguna fecha → 409 (RF-28).
    Después, INSERT … RETURNING y commit.
    """
    candidata = motor.Transaccion(
        id=None,
        portafolio_id=portafolio.id,
        intermediario_id=nueva.intermediario_id,
        instrumento_id=nueva.instrumento_id,
        tipo=nueva.tipo,  # type: ignore[arg-type]  # ya validado: compra o venta
        fecha_concertacion=nueva.fecha_concertacion,
        cantidad=nueva.cantidad,
        precio=nueva.precio,
        importe_comisiones=nueva.importe_comisiones,
    )

    # 3. RF-05 crit. 2: en una venta, el importe debe ser menor que el monto.
    if nueva.tipo == "venta" and nueva.importe_comisiones >= motor.importes(candidata).monto:
        raise DatosInvalidos([ErrorCampo("importe_comisiones", "RF-05", MENSAJE_IMPORTE_VENTA)])

    # 4 y 5. Referencias del cuerpo.
    intermediario = _intermediario_propio(sesion, usuario_id, nueva.intermediario_id)
    instrumento = leer_instrumentos(sesion, [nueva.instrumento_id]).get(nueva.instrumento_id)
    if instrumento is None:
        raise NoEncontrado("instrumento")

    # 6. RD-08.
    if instrumento.divisa != portafolio.divisa_base:
        raise DivisaDistinta()

    # 7 y 8. RD-07: ni posterior a hoy ni fuera del intervalo de los datos de mercado.
    fecha = nueva.fecha_concertacion
    if fecha > hoy:
        raise FechaPosteriorAlRegistro()
    intervalo = intervalo_semillas(sesion)
    if not intervalo.inicio <= fecha <= intervalo.fin:
        raise FechaFueraDeIntervalo(intervalo)

    # 9. CETES: RF-26a crit. 2 y RD-05.
    if instrumento.clase_activo == "cetes" and instrumento.vencimiento is not None:
        if fecha >= instrumento.vencimiento:
            raise FechaEnODespuesDelVencimiento(instrumento.clave, instrumento.vencimiento)
        if (instrumento.vencimiento - fecha).days > LIMITE_DIAS_CETES:
            raise PlazoCetesExcedido(LIMITE_DIAS_CETES)

    # 10. CU-12 (RF-28): con todas las transacciones del portafolio, de cualquier fecha.
    negativo = motor.primer_saldo_negativo(cargar_historial(sesion, usuario_id, portafolio.id), candidata)
    if negativo is not None:
        raise SaldoNegativo(instrumento.clave, intermediario.nombre, negativo.fecha, negativo.saldo)

    # 11. Registro; `id` y `registrada_en` los fija la base.
    fila = sesion.execute(
        insert(Transaccion)
        .values(
            usuario_id=usuario_id,
            portafolio_id=portafolio.id,
            intermediario_id=intermediario.id,
            instrumento_id=instrumento.id,
            tipo=nueva.tipo,
            fecha_concertacion=fecha,
            cantidad=nueva.cantidad,
            precio=nueva.precio,
            importe_comisiones=nueva.importe_comisiones,
        )
        .returning(Transaccion.id, Transaccion.registrada_en)
    ).one()
    sesion.commit()
    return TransaccionRegistro(
        id=fila.id,
        portafolio_id=portafolio.id,
        intermediario=intermediario,
        instrumento=instrumento,
        tipo=nueva.tipo,
        fecha_concertacion=fecha,
        cantidad=nueva.cantidad,
        precio=nueva.precio,
        importe_comisiones=nueva.importe_comisiones,
        registrada_en=fila.registrada_en,
    )
