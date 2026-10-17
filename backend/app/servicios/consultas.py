"""Intervalo de los datos, posiciones al corte y tablero (CU-06 y CU-07; RF-06 a RF-11; RF-26a; RF-26b; RF-31; §3.9).

Toda cifra la calcula el motor único, con el historial y los datos de mercado de la base
(4.2 «Motor único»). Las rutas solo presentan. El historial se lee con el predicado del
propietario (RD-01): la ruta ya comprobó que el portafolio es del usuario (RF-02).

- Fin efectivo = min(fin del intervalo, hoy en la Ciudad de México) (RD-07; RD-15).
- Por omisión: inicio = intervalo.inicio + 1 día y fin = corte = fin efectivo (D-21).
- El corte del tablero es siempre `fin` (D-21).
"""

from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app import motor
from app.datos.consultas import cargar_historial, intervalo_semillas, leer_instrumentos
from app.datos.mercado_sql import cargar_mercado, leer_fuentes
from app.datos.registros import FuenteRegistro, InstrumentoRegistro, PortafolioRegistro

_UN_DIA = timedelta(days=1)


@dataclass(frozen=True)
class IntervaloDatos:
    """Intervalo de las semillas, hoy y los valores por omisión de E09, E19 y E20 (D-16; D-21)."""

    inicio: date
    fin: date
    hoy: date
    fin_efectivo: date
    defecto_inicio: date
    defecto_fin: date

    @property
    def efectivo(self) -> motor.Intervalo:
        """El intervalo con el que valida el motor: [inicio, min(fin, hoy)] (§5.6)."""
        return motor.Intervalo(inicio=self.inicio, fin=self.fin_efectivo)


@dataclass(frozen=True)
class ResultadoPosiciones:
    portafolio: PortafolioRegistro
    corte: motor.Corte
    instrumentos: dict[int, InstrumentoRegistro]
    fuentes: dict[int, FuenteRegistro]


@dataclass(frozen=True)
class ResultadoTablero:
    portafolio: PortafolioRegistro
    inicio: date
    fin: date
    indicadores: motor.Indicadores
    instrumentos: dict[int, InstrumentoRegistro]
    fuentes: dict[int, FuenteRegistro]


def intervalo_datos(sesion: Session, hoy: date) -> IntervaloDatos:
    """E09: intervalo de las semillas y valores por omisión; sin cargas → SinDatosDeMercado (503)."""
    intervalo = intervalo_semillas(sesion)
    fin_efectivo = min(intervalo.fin, hoy)
    return IntervaloDatos(
        inicio=intervalo.inicio,
        fin=intervalo.fin,
        hoy=hoy,
        fin_efectivo=fin_efectivo,
        defecto_inicio=intervalo.inicio + _UN_DIA,
        defecto_fin=fin_efectivo,
    )


def posiciones_al_corte(
    sesion: Session, usuario_id: int, portafolio: PortafolioRegistro, fecha_corte: date | None, hoy: date
) -> ResultadoPosiciones:
    """E19: posiciones, valor y resultado no realizado a la fecha de corte (RF-06; RF-08; RF-26a; RF-26b).

    Un corte fuera de [intervalo.inicio, fin efectivo] → PeriodoInvalido del motor, que se
    responde como 422 `fecha_fuera_de_intervalo` (D-25).
    """
    intervalo = intervalo_datos(sesion, hoy)
    corte = intervalo.defecto_fin if fecha_corte is None else fecha_corte
    motor.validar_corte(corte, intervalo.efectivo)
    historial = cargar_historial(sesion, usuario_id, portafolio.id)
    ids = list(historial.instrumentos)
    resultado = motor.posiciones(historial, cargar_mercado(sesion, ids, corte), corte)
    return ResultadoPosiciones(
        portafolio=portafolio,
        corte=resultado,
        instrumentos=leer_instrumentos(sesion, ids),
        fuentes=leer_fuentes(sesion),
    )


def tablero(
    sesion: Session,
    usuario_id: int,
    portafolio: PortafolioRegistro,
    inicio: date | None,
    fin: date | None,
    hoy: date,
) -> ResultadoTablero:
    """E20: serie diaria, TWR, máxima caída, valor y resultado del periodo (RF-09 a RF-11; RNF-02).

    Valida con `motor.validar_periodo` (N7: periodo invertido; N8: fuera del intervalo). Sin
    transacciones con fecha ≤ fin, el motor devuelve ceros y `corte_fin.sin_transacciones`
    (D-22); la ruta lo presenta como `sin_datos`.
    """
    intervalo = intervalo_datos(sesion, hoy)
    inicio = intervalo.defecto_inicio if inicio is None else inicio
    fin = intervalo.defecto_fin if fin is None else fin
    motor.validar_periodo(inicio, fin, intervalo.efectivo)
    historial = cargar_historial(sesion, usuario_id, portafolio.id)
    ids = list(historial.instrumentos)
    resultado = motor.indicadores(historial, cargar_mercado(sesion, ids, fin), inicio, fin)
    return ResultadoTablero(
        portafolio=portafolio,
        inicio=inicio,
        fin=fin,
        indicadores=resultado,
        instrumentos=leer_instrumentos(sesion, ids),
        fuentes=leer_fuentes(sesion),
    )
