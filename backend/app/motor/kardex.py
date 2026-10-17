"""Kardex por par instrumento-intermediario y regla de saldo de CU-12.

Reglas (RF-06; RF-08; RF-26a; RF-28; P-09; P-10; reglas de 3.2):
- el par es (instrumento, intermediario) dentro del portafolio;
- se procesan, en orden, las fechas de transacción y de vencimiento; el corte es inclusivo;
- cada día: vencimientos, luego compras (agregadas por par) y luego ventas;
- una venta no cambia el costo unitario; con saldo 0, el costo se reinicia.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from .contexto import CERO, calculo
from .errores import HistorialInvalido
from .modelos import Historial, Instrumento, SaldoNegativo, Transaccion, _saldo_negativo_del_par

Par = tuple[int, int]
"""(instrumento_id, intermediario_id)."""


@dataclass(frozen=True, slots=True)
class Flujos:
    """Flujos de un día: aportaciones A(t) y retiros por ventas y por vencimientos (RF-09 crit. 2)."""

    aportaciones: Decimal
    retiros_ventas: Decimal
    retiros_vencimientos: Decimal


FLUJOS_CERO = Flujos(aportaciones=CERO, retiros_ventas=CERO, retiros_vencimientos=CERO)


class Kardex:
    """Saldo y costo unitario de cada par, avanzando en el tiempo sin retroceder.

    Los pares se recorren por clave del instrumento y luego por intermediario (D-48).
    """

    def __init__(self, h: Historial) -> None:
        if not isinstance(h, Historial):
            raise TypeError("Kardex recibe un Historial.")
        self.historial = h
        claves = {iid: instrumento.clave for iid, instrumento in h.instrumentos.items()}

        self._por_fecha: dict[date, list[Transaccion]] = {}
        primera_fecha: dict[Par, date] = {}
        for t in h.transacciones:
            self._por_fecha.setdefault(t.fecha_concertacion, []).append(t)
            anterior = primera_fecha.get(t.par)
            if anterior is None or t.fecha_concertacion < anterior:
                primera_fecha[t.par] = t.fecha_concertacion
        self._primera_fecha = primera_fecha

        self.pares: tuple[Par, ...] = tuple(sorted(primera_fecha, key=lambda par: (claves[par[0]], par[1])))
        usados = sorted({par[0] for par in self.pares}, key=lambda iid: claves[iid])
        self.instrumentos: tuple[Instrumento, ...] = tuple(h.instrumentos[iid] for iid in usados)
        self._pares_por_instrumento: dict[int, tuple[Par, ...]] = {
            iid: tuple(par for par in self.pares if par[0] == iid) for iid in usados
        }

        self._vencimientos: dict[date, list[Instrumento]] = {}
        for instrumento in self.instrumentos:
            if instrumento.es_cetes and instrumento.vencimiento is not None:
                self._vencimientos.setdefault(instrumento.vencimiento, []).append(instrumento)

        self._eventos: tuple[date, ...] = tuple(sorted(set(self._por_fecha) | set(self._vencimientos)))
        self._siguiente = 0
        self.fecha: date | None = None
        self._saldo: dict[Par, int] = {par: 0 for par in self.pares}
        self._costo: dict[Par, Decimal] = {par: CERO for par in self.pares}

    @calculo
    def avanzar_hasta(self, fecha: date) -> dict[date, Flujos]:
        """Procesa los eventos con fecha ≤ fecha y devuelve los flujos de cada día procesado."""
        if self.fecha is not None and fecha < self.fecha:
            raise ValueError("El kardex no puede retroceder en el tiempo.")
        flujos: dict[date, Flujos] = {}
        while self._siguiente < len(self._eventos) and self._eventos[self._siguiente] <= fecha:
            dia = self._eventos[self._siguiente]
            flujos[dia] = self._procesar(dia)
            self._siguiente += 1
        self.fecha = fecha
        return flujos

    @calculo
    def pares_de(self, instrumento_id: int) -> tuple[Par, ...]:
        """Pares de un instrumento, en el orden fijo del kardex."""
        return self._pares_por_instrumento.get(instrumento_id, ())

    @calculo
    def saldo(self, par: Par) -> int:
        """Títulos del par a la fecha procesada."""
        return self._saldo[par]

    @calculo
    def costo_unitario(self, par: Par) -> Decimal:
        """Costo promedio ponderado del par (0 con saldo 0)."""
        return self._costo[par]

    @calculo
    def tiene_transacciones(self, par: Par) -> bool:
        """Si existe una transacción del par con fecha ≤ la fecha procesada."""
        return self.fecha is not None and self._primera_fecha[par] <= self.fecha

    def _procesar(self, dia: date) -> Flujos:
        # 1. Vencimientos (RF-26a crit. 1): retiro de saldo × VN, sin ISR.
        retiros_vencimientos = CERO
        for instrumento in self._vencimientos.get(dia, ()):
            valor_nominal = instrumento.valor_nominal
            if valor_nominal is None:  # Historial ya lo impide
                raise HistorialInvalido(f"La emisión {instrumento.clave} no tiene valor nominal.")
            for par in self._pares_por_instrumento[instrumento.id]:
                retiros_vencimientos += Decimal(self._saldo[par]) * valor_nominal
                self._saldo[par] = 0
                self._costo[par] = CERO

        # Agregación por par: Q = Σ cantidad; K = Σ importe de efectivo.
        compras: dict[Par, tuple[int, Decimal]] = {}
        ventas: dict[Par, tuple[int, Decimal]] = {}
        for t in self._por_fecha.get(dia, ()):
            monto = Decimal(t.cantidad) * t.precio
            if t.tipo == "compra":
                q, k = compras.get(t.par, (0, CERO))
                compras[t.par] = (q + t.cantidad, k + monto + t.importe_comisiones)
            else:
                q, k = ventas.get(t.par, (0, CERO))
                ventas[t.par] = (q + t.cantidad, k + monto - t.importe_comisiones)

        # 2. Compras antes que ventas (RF-08 crit. 3).
        aportaciones = CERO
        for par in self.pares:
            if par not in compras:
                continue
            q, k = compras[par]
            saldo = self._saldo[par]
            self._costo[par] = (Decimal(saldo) * self._costo[par] + k) / Decimal(saldo + q)
            self._saldo[par] = saldo + q
            aportaciones += k

        # 3. Ventas: el costo unitario no cambia (P-10); con saldo 0 se reinicia.
        retiros_ventas = CERO
        for par in self.pares:
            if par not in ventas:
                continue
            q, ingreso = ventas[par]
            saldo = self._saldo[par] - q
            if saldo < 0:  # Historial ya lo impide (RF-28)
                raise HistorialInvalido(f"El saldo del par {par} queda negativo el {dia.isoformat()}.")
            self._saldo[par] = saldo
            if saldo == 0:
                self._costo[par] = CERO
            retiros_ventas += ingreso

        return Flujos(
            aportaciones=aportaciones,
            retiros_ventas=retiros_ventas,
            retiros_vencimientos=retiros_vencimientos,
        )


@calculo
def primer_saldo_negativo(h: Historial, candidata: Transaccion) -> SaldoNegativo | None:
    """Regla de CU-12 (RF-28 crit. 1 a 3).

    Toma las transacciones del par de la candidata dentro del portafolio, más la candidata,
    y devuelve la primera fecha cuyo saldo al cierre queda negativo, con ese saldo. Los
    títulos del mismo instrumento con otro intermediario o en otro portafolio no cuentan.
    """
    if not isinstance(h, Historial):
        raise TypeError("primer_saldo_negativo recibe un Historial.")
    if not isinstance(candidata, Transaccion):
        raise TypeError("La candidata debe ser una Transaccion.")
    if candidata.portafolio_id != h.portafolio_id:
        raise ValueError("La candidata es de otro portafolio que el historial.")
    del_par = [t for t in h.transacciones if t.par == candidata.par]
    del_par.append(candidata)
    return _saldo_negativo_del_par(del_par)
