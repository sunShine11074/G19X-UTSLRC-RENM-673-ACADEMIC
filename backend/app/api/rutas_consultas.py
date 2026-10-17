"""Rutas de consulta: E09, E19 y E20 (CU-05 a CU-07; §4.2; §4.3).

Todas exigen sesión y solo leen (L = `usuario_vigente`). Las de un portafolio usan
`portafolio_propio`, que se resuelve antes que la consulta: lo ajeno da el mismo 404 que lo
inexistente, con cualquier parámetro (§4.1; RNF-03). Las fechas de la consulta son
AAAA-MM-DD estrictas (RD-14); las cifras las presenta `esquemas_consultas` sin recalcular.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencias import portafolio_propio
from app.api.esquemas_consultas import (
    IntervaloVista,
    PosicionesVista,
    TableroVista,
    intervalo_vista,
    posiciones_vista,
    tablero_vista,
)
from app.api.tipos import FechaEstricta
from app.cuentas.dependencias import UsuarioVigente, usuario_vigente
from app.datos.registros import PortafolioRegistro
from app.db import obtener_sesion
from app.reloj import hoy_cdmx
from app.servicios import consultas

router = APIRouter(prefix="/api", tags=["consultas"])

SesionBd = Annotated[Session, Depends(obtener_sesion)]
Lector = Annotated[UsuarioVigente, Depends(usuario_vigente)]
Hoy = Annotated[date, Depends(hoy_cdmx)]
PortafolioPropio = Annotated[PortafolioRegistro, Depends(portafolio_propio)]


@router.get("/intervalo-datos", dependencies=[Depends(usuario_vigente)])
def ver_intervalo_datos(sesion: SesionBd, hoy: Hoy) -> IntervaloVista:
    """E09 (RD-07; RF-09 crit. 3; S-09; D-16; D-21): intervalo de las semillas, hoy y los valores por omisión."""
    return intervalo_vista(consultas.intervalo_datos(sesion, hoy))


@router.get("/portafolios/{portafolio_id}/posiciones")
def ver_posiciones(
    portafolio: PortafolioPropio,
    usuario: Lector,
    sesion: SesionBd,
    hoy: Hoy,
    fecha_corte: Annotated[FechaEstricta | None, Query(description="AAAA-MM-DD; por omisión, el fin efectivo")] = None,
) -> PosicionesVista:
    """E19 (RF-06; RF-08; RF-26a; RF-26b; RF-31 crit. 2 y 3; RNF-02): posiciones al corte.

    Un corte fuera de [intervalo.inicio, fin efectivo] da 422 `fecha_fuera_de_intervalo` (D-25).
    """
    return posiciones_vista(consultas.posiciones_al_corte(sesion, usuario.id, portafolio, fecha_corte, hoy))


@router.get("/portafolios/{portafolio_id}/tablero")
def ver_tablero(
    portafolio: PortafolioPropio,
    usuario: Lector,
    sesion: SesionBd,
    hoy: Hoy,
    inicio: Annotated[
        FechaEstricta | None, Query(description="AAAA-MM-DD; por omisión, el día siguiente al inicio del intervalo")
    ] = None,
    fin: Annotated[FechaEstricta | None, Query(description="AAAA-MM-DD; por omisión, el fin efectivo")] = None,
) -> TableroVista:
    """E20 (RF-09 a RF-11; RF-26a; RF-26b; RF-31; RNF-02; RNF-07): indicadores del periodo; el corte es `fin`.

    Periodo invertido → 422 `periodo_invertido` (N7); fuera del intervalo → 422
    `periodo_fuera_de_intervalo` (N8). Sin transacciones con fecha ≤ fin → 200 con `sin_datos` (D-22).
    """
    return tablero_vista(consultas.tablero(sesion, usuario.id, portafolio, inicio, fin, hoy))
