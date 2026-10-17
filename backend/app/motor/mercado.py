"""Datos de mercado que lee el motor (4.2 «Adaptadores de datos»; 3.4.8; §5.4 del diseño).

El motor solo lee precios y tasas por la interfaz `DatosMercado`. Las reglas «último
cierre igual o anterior» y «última colocación de cada plazo igual o anterior» viven aquí,
en `IndiceMercado`, que el motor construye una vez por llamada pública.
"""

from bisect import bisect_right
from collections.abc import Iterable, Sequence
from datetime import date
from typing import Protocol

from .contexto import calculo
from .modelos import Cierre, Colocacion, Instrumento


class DatosMercado(Protocol):
    """Interfaz «Datos de mercado» que ofrece Acceso a datos."""

    def cierres(self, instrumento_id: int, hasta: date) -> Sequence[Cierre]:
        """Cierres del instrumento con fecha ≤ hasta, en orden ascendente y uno por fecha."""
        ...

    def colocaciones(self, hasta: date) -> Sequence[Colocacion]:
        """Colocaciones con fecha_colocacion ≤ hasta."""
        ...


class MercadoEnMemoria:
    """`DatosMercado` en memoria; lo usan las pruebas y Acceso a datos (`cargar_mercado`)."""

    def __init__(self, cierres: Iterable[Cierre], colocaciones: Iterable[Colocacion]) -> None:
        por_instrumento: dict[int, dict[date, Cierre]] = {}
        for cierre in cierres:
            if not isinstance(cierre, Cierre):
                raise TypeError("cierres solo admite Cierre.")
            del_instrumento = por_instrumento.setdefault(cierre.instrumento_id, {})
            if cierre.fecha in del_instrumento:
                raise ValueError(
                    f"Hay más de un cierre del instrumento {cierre.instrumento_id} el {cierre.fecha.isoformat()} (RD-19)."
                )
            del_instrumento[cierre.fecha] = cierre
        self._cierres: dict[int, tuple[Cierre, ...]] = {}
        self._fechas_cierre: dict[int, tuple[date, ...]] = {}
        for instrumento_id, del_instrumento in por_instrumento.items():
            ordenados = tuple(del_instrumento[f] for f in sorted(del_instrumento))
            self._cierres[instrumento_id] = ordenados
            self._fechas_cierre[instrumento_id] = tuple(c.fecha for c in ordenados)

        vistas: set[tuple[int, date]] = set()
        lista: list[Colocacion] = []
        for colocacion in colocaciones:
            if not isinstance(colocacion, Colocacion):
                raise TypeError("colocaciones solo admite Colocacion.")
            llave = (colocacion.plazo_nominal, colocacion.fecha_colocacion)
            if llave in vistas:
                raise ValueError(
                    f"Hay más de una colocación a {colocacion.plazo_nominal} días "
                    f"el {colocacion.fecha_colocacion.isoformat()} (RF-30 crit. 3)."
                )
            vistas.add(llave)
            lista.append(colocacion)
        lista.sort(key=lambda c: (c.fecha_colocacion, c.plazo_nominal))
        self._colocaciones: tuple[Colocacion, ...] = tuple(lista)
        self._fechas_colocacion: tuple[date, ...] = tuple(c.fecha_colocacion for c in lista)

    @calculo
    def cierres(self, instrumento_id: int, hasta: date) -> Sequence[Cierre]:
        """Cierres del instrumento con fecha ≤ hasta, ascendentes."""
        fechas = self._fechas_cierre.get(instrumento_id, ())
        return self._cierres.get(instrumento_id, ())[: bisect_right(fechas, hasta)]

    @calculo
    def colocaciones(self, hasta: date) -> Sequence[Colocacion]:
        """Colocaciones con fecha_colocacion ≤ hasta."""
        return self._colocaciones[: bisect_right(self._fechas_colocacion, hasta)]


class IndiceMercado:
    """Índice de los datos de mercado de una llamada pública, hasta una fecha.

    Pide a `DatosMercado` los cierres de cada instrumento y las colocaciones una sola vez,
    los valida y resuelve cada consulta con `bisect`.
    """

    def __init__(self, m: DatosMercado, instrumentos: Iterable[Instrumento], hasta: date) -> None:
        self.hasta = hasta
        self._cierres: dict[int, tuple[Cierre, ...]] = {}
        self._fechas_cierre: dict[int, tuple[date, ...]] = {}
        hay_cetes = False
        for instrumento in instrumentos:
            cierres = tuple(m.cierres(instrumento.id, hasta))
            if instrumento.es_cetes:
                hay_cetes = True
                if cierres:
                    raise ValueError(f"La emisión {instrumento.clave} tiene precios de cierre (RD-04).")
                continue
            anterior: date | None = None
            for cierre in cierres:
                if not isinstance(cierre, Cierre) or cierre.instrumento_id != instrumento.id:
                    raise ValueError(f"Los datos de mercado entregaron un cierre ajeno a {instrumento.clave}.")
                if cierre.fecha > hasta:
                    raise ValueError(f"Los datos de mercado entregaron un cierre de {instrumento.clave} posterior a la fecha pedida.")
                if anterior is not None and cierre.fecha <= anterior:
                    raise ValueError(f"Los cierres de {instrumento.clave} no son ascendentes ni únicos por fecha (RD-19).")
                anterior = cierre.fecha
            self._cierres[instrumento.id] = cierres
            self._fechas_cierre[instrumento.id] = tuple(c.fecha for c in cierres)

        # Colocaciones por plazo nominal, ordenadas por fecha de colocación.
        self._por_plazo: dict[int, tuple[Colocacion, ...]] = {}
        self._fechas_plazo: dict[int, tuple[date, ...]] = {}
        if hay_cetes:
            por_plazo: dict[int, list[Colocacion]] = {}
            for colocacion in m.colocaciones(hasta):
                if not isinstance(colocacion, Colocacion):
                    raise ValueError("Los datos de mercado entregaron algo que no es una colocación.")
                if colocacion.fecha_colocacion > hasta:
                    raise ValueError("Los datos de mercado entregaron una colocación posterior a la fecha pedida.")
                por_plazo.setdefault(colocacion.plazo_nominal, []).append(colocacion)
            for plazo, lista in por_plazo.items():
                lista.sort(key=lambda c: c.fecha_colocacion)
                fechas = tuple(c.fecha_colocacion for c in lista)
                if len(set(fechas)) != len(fechas):
                    raise ValueError(f"Hay dos colocaciones a {plazo} días con la misma fecha (RF-30 crit. 3).")
                self._por_plazo[plazo] = tuple(lista)
                self._fechas_plazo[plazo] = fechas

    def _comprobar_fecha(self, fecha: date) -> None:
        if fecha > self.hasta:
            raise ValueError("El índice de mercado no cubre la fecha pedida.")

    @calculo
    def cierre(self, instrumento_id: int, fecha: date) -> Cierre | None:
        """Cierre de mayor fecha ≤ fecha, sin límite de antigüedad (RF-08 crit. 4)."""
        self._comprobar_fecha(fecha)
        fechas = self._fechas_cierre.get(instrumento_id, ())
        posicion = bisect_right(fechas, fecha)
        if posicion == 0:
            return None
        return self._cierres[instrumento_id][posicion - 1]

    @calculo
    def curva(self, fecha: date) -> tuple[Colocacion, ...]:
        """Por cada plazo nominal, la colocación con mayor fecha ≤ fecha (RF-26b crit. 3; R-14)."""
        self._comprobar_fecha(fecha)
        vigentes: list[Colocacion] = []
        for plazo in sorted(self._por_plazo):
            posicion = bisect_right(self._fechas_plazo[plazo], fecha)
            if posicion > 0:
                vigentes.append(self._por_plazo[plazo][posicion - 1])
        return tuple(vigentes)
