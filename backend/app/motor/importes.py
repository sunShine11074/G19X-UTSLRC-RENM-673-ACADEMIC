"""Importes de una transacción (RF-05 crit. 1; RF-09 crit. 2; P-16)."""

from decimal import Decimal

from .contexto import CERO, calculo
from .modelos import ImportesTransaccion, Transaccion


@calculo
def importes(t: Transaccion) -> ImportesTransaccion:
    """Monto, costo o ingreso por título, aportación y retiro, sin redondear.

    Compra: costo por título = (monto + importe) / títulos; aportación = monto + importe.
    Venta: ingreso por título = (monto − importe) / títulos; retiro = monto − importe.
    """
    if not isinstance(t, Transaccion):
        raise TypeError("importes recibe una Transaccion.")
    cantidad = Decimal(t.cantidad)
    monto = cantidad * t.precio
    if t.tipo == "compra":
        aportacion = monto + t.importe_comisiones
        return ImportesTransaccion(
            transaccion_id=t.id,
            monto=monto,
            costo_por_titulo=aportacion / cantidad,
            ingreso_por_titulo=None,
            aportacion=aportacion,
            retiro=CERO,
        )
    retiro = monto - t.importe_comisiones
    return ImportesTransaccion(
        transaccion_id=t.id,
        monto=monto,
        costo_por_titulo=None,
        ingreso_por_titulo=retiro / cantidad,
        aportacion=CERO,
        retiro=retiro,
    )
