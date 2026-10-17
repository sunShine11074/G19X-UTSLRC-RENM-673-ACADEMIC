"""Cuerpo y vista de las transacciones (E17 y E18; §4.3; RD-12 a RD-15; D-14; D-37).

Toda cifra viaja como cadena. Precio e importe vuelven tal como se guardaron (`como_texto`);
el costo o ingreso por título sale del motor y se presenta con `presentar_por_titulo`.
"""

from datetime import date

from pydantic import BaseModel

from app import motor
from app.api.comunes import InstrumentoVista, IntermediarioVista, instrumento_vista, intermediario_vista
from app.api.tipos import (
    FechaEstricta,
    Identificador,
    Importe,
    ModeloEntrada,
    Precio,
    TipoTransaccion,
    Titulos,
    como_texto,
)
from app.datos.consultas import transaccion_motor
from app.datos.registros import TransaccionRegistro
from app.reloj import momento_iso
from app.servicios.transacciones import TransaccionNueva


class CuerpoTransaccion(ModeloEntrada):
    """E18: compra o venta; cifras como texto, sin redondear (RF-05 crit. 2)."""

    intermediario_id: Identificador
    instrumento_id: Identificador
    tipo: TipoTransaccion
    fecha_concertacion: FechaEstricta
    cantidad: Titulos
    precio: Precio
    importe_comisiones: Importe

    def como_nueva(self) -> TransaccionNueva:
        return TransaccionNueva(
            intermediario_id=self.intermediario_id,
            instrumento_id=self.instrumento_id,
            tipo=self.tipo,
            fecha_concertacion=self.fecha_concertacion,
            cantidad=self.cantidad,
            precio=self.precio,
            importe_comisiones=self.importe_comisiones,
        )


class TransaccionVista(BaseModel):
    id: int
    tipo: str
    fecha_concertacion: date
    cantidad: str
    precio: str
    importe_comisiones: str
    costo_por_titulo: str | None  # solo en compras (RF-05 crit. 1; D-14)
    ingreso_por_titulo: str | None  # solo en ventas
    intermediario: IntermediarioVista
    instrumento: InstrumentoVista
    registrada_en: str  # ISO 8601 con el desfase de la Ciudad de México (RD-15)


def transaccion_vista(r: TransaccionRegistro) -> TransaccionVista:
    """Convierte el registro; el costo o ingreso por título lo calcula el motor (4.2 «Motor único»)."""
    importes = motor.importes(transaccion_motor(r))
    return TransaccionVista(
        id=r.id,
        tipo=r.tipo,
        fecha_concertacion=r.fecha_concertacion,
        cantidad=str(r.cantidad),
        precio=como_texto(r.precio),
        importe_comisiones=como_texto(r.importe_comisiones),
        costo_por_titulo=(
            None if importes.costo_por_titulo is None else motor.presentar_por_titulo(importes.costo_por_titulo)
        ),
        ingreso_por_titulo=(
            None if importes.ingreso_por_titulo is None else motor.presentar_por_titulo(importes.ingreso_por_titulo)
        ),
        intermediario=intermediario_vista(r.intermediario),
        instrumento=instrumento_vista(r.instrumento),
        registrada_en=momento_iso(r.registrada_en),
    )
