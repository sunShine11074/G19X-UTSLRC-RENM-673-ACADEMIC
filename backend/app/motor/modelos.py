"""Entradas y salidas del motor único (§5.3 y §5.7 del diseño; columnas de 4.4).

Las entradas validan sus tipos al construirse: ninguna cifra entra como float ni bool
(RD-12). Las salidas llevan `Decimal` sin redondear, salvo el precio P de los CETES (RD-16).
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import StrEnum
from typing import Literal

from .errores import HistorialInvalido

ClaseActivo = Literal["accion", "etf", "fibra", "cetes"]
TipoTx = Literal["compra", "venta"]

CLASES_ACTIVO: frozenset[str] = frozenset({"accion", "etf", "fibra", "cetes"})
TIPOS_TRANSACCION: frozenset[str] = frozenset({"compra", "venta"})


# --- Validación de tipos (privada) -------------------------------------------------


def _nombre_tipo(valor: object) -> str:
    return type(valor).__name__


def _exigir_entero(valor: object, campo: str, *, positivo: bool = False) -> None:
    # `type(...) is int` rechaza bool, que es subclase de int.
    if type(valor) is not int:
        raise TypeError(f"{campo} debe ser int, no {_nombre_tipo(valor)}.")
    if positivo and valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")


def _exigir_decimal(valor: object, campo: str, *, positivo: bool = False, no_negativo: bool = False) -> None:
    if not isinstance(valor, Decimal):
        raise TypeError(f"{campo} debe ser Decimal, no {_nombre_tipo(valor)}.")
    if not valor.is_finite():
        raise ValueError(f"{campo} debe ser un número finito.")
    if positivo and valor <= 0:
        raise ValueError(f"{campo} debe ser mayor que cero.")
    if no_negativo and valor < 0:
        raise ValueError(f"{campo} no puede ser negativo.")


def _exigir_fecha(valor: object, campo: str) -> None:
    # datetime es subclase de date: se rechaza, las fechas van sin hora (RD-15).
    if type(valor) is not date:
        raise TypeError(f"{campo} debe ser date, no {_nombre_tipo(valor)}.")


def _exigir_texto(valor: object, campo: str) -> None:
    if not isinstance(valor, str):
        raise TypeError(f"{campo} debe ser str, no {_nombre_tipo(valor)}.")
    if valor == "":
        raise ValueError(f"{campo} no puede estar vacío.")


# --- Entradas -----------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Instrumento:
    """Instrumento del catálogo; vencimiento y valor nominal solo en CETES (RF-04)."""

    id: int
    clave: str
    clase_activo: ClaseActivo
    vencimiento: date | None = None
    valor_nominal: Decimal | None = None

    def __post_init__(self) -> None:
        _exigir_entero(self.id, "id")
        _exigir_texto(self.clave, "clave")
        _exigir_texto(self.clase_activo, "clase_activo")
        if self.clase_activo not in CLASES_ACTIVO:
            raise ValueError("clase_activo debe ser accion, etf, fibra o cetes.")
        if self.vencimiento is not None:
            _exigir_fecha(self.vencimiento, "vencimiento")
        if self.valor_nominal is not None:
            _exigir_decimal(self.valor_nominal, "valor_nominal", positivo=True)

    @property
    def es_cetes(self) -> bool:
        return self.clase_activo == "cetes"


@dataclass(frozen=True, slots=True)
class Transaccion:
    """Compra o venta registrada; `id` es None en una candidata de CU-12."""

    id: int | None
    portafolio_id: int
    intermediario_id: int
    instrumento_id: int
    tipo: TipoTx
    fecha_concertacion: date
    cantidad: int
    precio: Decimal
    importe_comisiones: Decimal

    def __post_init__(self) -> None:
        if self.id is not None:
            _exigir_entero(self.id, "id")
        _exigir_entero(self.portafolio_id, "portafolio_id")
        _exigir_entero(self.intermediario_id, "intermediario_id")
        _exigir_entero(self.instrumento_id, "instrumento_id")
        _exigir_texto(self.tipo, "tipo")
        if self.tipo not in TIPOS_TRANSACCION:
            raise ValueError("tipo debe ser compra o venta.")
        _exigir_fecha(self.fecha_concertacion, "fecha_concertacion")
        _exigir_entero(self.cantidad, "cantidad", positivo=True)  # RD-06
        _exigir_decimal(self.precio, "precio", positivo=True)  # RD-06
        _exigir_decimal(self.importe_comisiones, "importe_comisiones", no_negativo=True)  # RF-05 crit. 2

    @property
    def par(self) -> tuple[int, int]:
        """Par (instrumento, intermediario) dentro del portafolio (RF-28; X-06)."""
        return (self.instrumento_id, self.intermediario_id)


@dataclass(frozen=True, slots=True)
class Cierre:
    """Precio de cierre publicado por una fuente (RF-07; RF-31)."""

    instrumento_id: int
    fecha: date
    precio: Decimal
    fuente_id: int

    def __post_init__(self) -> None:
        _exigir_entero(self.instrumento_id, "instrumento_id")
        _exigir_fecha(self.fecha, "fecha")
        _exigir_decimal(self.precio, "precio", positivo=True)
        _exigir_entero(self.fuente_id, "fuente_id")


@dataclass(frozen=True, slots=True)
class Colocacion:
    """Tasa de una colocación primaria de CETES, en por ciento anual (RF-30; RF-26b)."""

    plazo_nominal: int
    fecha_colocacion: date
    valor: Decimal
    plazo_efectivo: int
    fuente_id: int

    def __post_init__(self) -> None:
        _exigir_entero(self.plazo_nominal, "plazo_nominal", positivo=True)
        _exigir_fecha(self.fecha_colocacion, "fecha_colocacion")
        _exigir_decimal(self.valor, "valor")
        _exigir_entero(self.plazo_efectivo, "plazo_efectivo", positivo=True)
        _exigir_entero(self.fuente_id, "fuente_id")


@dataclass(frozen=True, slots=True)
class Intervalo:
    """Intervalo cerrado de fechas que cubren los datos de mercado (RD-07)."""

    inicio: date
    fin: date

    def __post_init__(self) -> None:
        _exigir_fecha(self.inicio, "inicio")
        _exigir_fecha(self.fin, "fin")


@dataclass(frozen=True, slots=True)
class SaldoNegativo:
    """Primera fecha en que el saldo de un par quedaría negativo, con ese saldo (RF-28)."""

    fecha: date
    saldo: int


def _saldo_negativo_del_par(transacciones: Iterable[Transaccion]) -> SaldoNegativo | None:
    """Saldo al cierre de cada fecha (compras − ventas del día); la primera fecha negativa.

    Recibe las transacciones de un solo par. Las compras del día cuentan antes que las
    ventas porque se usa el neto del día (RF-08 crit. 3; C1).
    """
    neto_por_fecha: dict[date, int] = {}
    for t in transacciones:
        signo = 1 if t.tipo == "compra" else -1
        neto_por_fecha[t.fecha_concertacion] = neto_por_fecha.get(t.fecha_concertacion, 0) + signo * t.cantidad
    saldo = 0
    for fecha in sorted(neto_por_fecha):
        saldo += neto_por_fecha[fecha]
        if saldo < 0:
            return SaldoNegativo(fecha=fecha, saldo=saldo)
    return None


@dataclass(frozen=True, slots=True)
class Historial:
    """Todas las transacciones de un portafolio y los instrumentos que usan.

    Al construirse rechaza con `HistorialInvalido` lo que la base y la API ya impiden:
    transacciones de otro portafolio (X-06), CETES fechados en su vencimiento o después
    (RF-26a crit. 2), saldos por par negativos (RF-28) y CETES sin vencimiento o valor
    nominal, o instrumentos que no son CETES y los tienen.
    """

    portafolio_id: int
    transacciones: tuple[Transaccion, ...]
    instrumentos: Mapping[int, Instrumento]

    def __post_init__(self) -> None:
        _exigir_entero(self.portafolio_id, "portafolio_id")
        transacciones = tuple(self.transacciones)
        for t in transacciones:
            if not isinstance(t, Transaccion):
                raise TypeError(f"transacciones solo admite Transaccion, no {_nombre_tipo(t)}.")
        if not isinstance(self.instrumentos, Mapping):
            raise TypeError("instrumentos debe ser un Mapping[int, Instrumento].")
        instrumentos = dict(self.instrumentos)
        for llave, instrumento in instrumentos.items():
            if not isinstance(instrumento, Instrumento):
                raise TypeError(f"instrumentos solo admite Instrumento, no {_nombre_tipo(instrumento)}.")
            if llave != instrumento.id:
                raise HistorialInvalido(f"La llave {llave!r} no coincide con el id del instrumento {instrumento.id}.")
            self._validar_instrumento(instrumento)
        object.__setattr__(self, "transacciones", transacciones)
        object.__setattr__(self, "instrumentos", instrumentos)
        self._validar_transacciones()

    @staticmethod
    def _validar_instrumento(instrumento: Instrumento) -> None:
        tiene_datos = instrumento.vencimiento is not None or instrumento.valor_nominal is not None
        if instrumento.es_cetes:
            if instrumento.vencimiento is None or instrumento.valor_nominal is None:
                raise HistorialInvalido(f"La emisión {instrumento.clave} no tiene vencimiento o valor nominal.")
        elif tiene_datos:
            raise HistorialInvalido(f"El instrumento {instrumento.clave} no es CETES y tiene vencimiento o valor nominal.")

    def _validar_transacciones(self) -> None:
        ids_vistos: set[int] = set()
        por_par: dict[tuple[int, int], list[Transaccion]] = {}
        for t in self.transacciones:
            if t.portafolio_id != self.portafolio_id:
                raise HistorialInvalido("El historial contiene transacciones de otro portafolio (X-06).")
            instrumento = self.instrumentos.get(t.instrumento_id)
            if instrumento is None:
                raise HistorialInvalido(f"Falta el instrumento {t.instrumento_id} de una transacción.")
            if instrumento.es_cetes and instrumento.vencimiento is not None and t.fecha_concertacion >= instrumento.vencimiento:
                raise HistorialInvalido(
                    f"Una transacción de {instrumento.clave} está fechada en su vencimiento o después (RF-26a crit. 2)."
                )
            if t.id is not None:
                if t.id in ids_vistos:
                    raise HistorialInvalido(f"La transacción {t.id} está repetida.")
                ids_vistos.add(t.id)
            por_par.setdefault(t.par, []).append(t)
        for (instrumento_id, intermediario_id), transacciones in por_par.items():
            negativo = _saldo_negativo_del_par(transacciones)
            if negativo is not None:
                clave = self.instrumentos[instrumento_id].clave
                raise HistorialInvalido(
                    f"El saldo de {clave} con el intermediario {intermediario_id} queda en {negativo.saldo} "
                    f"el {negativo.fecha.isoformat()} (RF-28)."
                )


# --- Salidas ------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ImportesTransaccion:
    """Importes de una transacción (RF-05 crit. 1; RF-09 crit. 2)."""

    transaccion_id: int | None
    monto: Decimal
    costo_por_titulo: Decimal | None
    ingreso_por_titulo: Decimal | None
    aportacion: Decimal
    retiro: Decimal


@dataclass(frozen=True, slots=True)
class PrecioUsado:
    """Cierre vigente a una fecha de valuación, con la fecha del dato (RF-08 crit. 4; RF-31 crit. 3)."""

    instrumento_id: int
    fecha_valuacion: date
    fecha_cierre: date
    precio: Decimal
    fuente_id: int
    sin_cierre_ese_dia: bool


class CasoTasa(StrEnum):
    """Cómo se obtuvo la tasa r de un CETES (RF-26b crit. 1 y 2)."""

    NODO = "nodo"
    EXTREMO_INFERIOR = "extremo inferior"
    EXTREMO_SUPERIOR = "extremo superior"
    INTERPOLACION = "interpolación"


@dataclass(frozen=True, slots=True)
class NodoTasa:
    """Colocación vigente de un plazo, usada como nodo de la curva (RF-26b; RF-31 crit. 2)."""

    plazo_nominal: int
    plazo_efectivo: int
    tasa: Decimal
    fecha_colocacion: date
    fuente_id: int


@dataclass(frozen=True, slots=True)
class ValuacionCetes:
    """Valuación de una emisión de CETES a una fecha (RF-26b); `p` es el único valor redondeado."""

    instrumento_id: int
    fecha: date
    vencimiento: date
    d: int
    caso: CasoTasa
    inf: NodoTasa
    sup: NodoTasa
    r: Decimal
    p_sin_redondear: Decimal
    p: Decimal


@dataclass(frozen=True, slots=True)
class PosicionPar:
    """Posición de un instrumento con un intermediario dentro del portafolio (RF-06; RF-08)."""

    instrumento_id: int
    intermediario_id: int
    tiene_transacciones: bool
    titulos: int
    costo_unitario: Decimal
    costo_total: Decimal
    precio: Decimal | None
    fecha_precio: date | None
    fuente_id: int | None
    cetes: ValuacionCetes | None
    valor: Decimal
    resultado_no_realizado: Decimal


@dataclass(frozen=True, slots=True)
class PosicionInstrumento:
    """Suma de los pares de un instrumento (RF-06 crit. 1)."""

    instrumento_id: int
    tiene_transacciones: bool
    vencida: bool
    titulos: int
    costo_total: Decimal
    valor: Decimal
    resultado_no_realizado: Decimal
    precio: Decimal | None
    fecha_precio: date | None
    fuente_id: int | None
    cetes: ValuacionCetes | None


@dataclass(frozen=True, slots=True)
class Corte:
    """Valuación del portafolio a una fecha de corte; sus totales son la suma de los pares (RNF-02)."""

    portafolio_id: int
    fecha_corte: date
    pares: tuple[PosicionPar, ...]
    instrumentos: tuple[PosicionInstrumento, ...]
    costo_total: Decimal
    valor: Decimal
    resultado_no_realizado: Decimal
    sin_transacciones: bool
    fuentes_usadas: frozenset[int]


@dataclass(frozen=True, slots=True)
class DiaSerie:
    """Un día natural de la serie de RF-09; el día base lleva `r = None`."""

    fecha: date
    valor: Decimal
    aportaciones: Decimal
    retiros_ventas: Decimal
    retiros_vencimientos: Decimal
    retiros: Decimal
    r: Decimal | None
    indice: Decimal
    maximo: Decimal
    caida: Decimal


@dataclass(frozen=True, slots=True)
class CaidaMaxima:
    """Máxima caída del índice con su pico y su valle (RF-10)."""

    maxima_caida: Decimal
    fecha_pico: date | None
    fecha_valle: date | None


@dataclass(frozen=True, slots=True)
class Indicadores:
    """Indicadores de un periodo (RF-09 a RF-11); las cifras finales vienen de `corte_fin`."""

    portafolio_id: int
    inicio: date
    fin: date
    fecha_base: date
    dias: int
    valor_base: Decimal
    valor_fin: Decimal
    costo_total_fin: Decimal
    resultado_no_realizado_fin: Decimal
    twr: Decimal
    maxima_caida: Decimal
    fecha_pico: date | None
    fecha_valle: date | None
    serie: tuple[DiaSerie, ...]
    corte_fin: Corte
    fuentes_usadas: frozenset[int]
