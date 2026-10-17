"""Rutas de transacciones: E17 y E18 (CU-05, CU-06 y CU-12; §4.2; §4.3).

No existen PUT, PATCH ni DELETE de transacciones (RD-09; RF-39): un método no ofrecido da 405.
"""

from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencias import portafolio_propio, portafolio_propio_bloqueado
from app.api.esquemas_transacciones import CuerpoTransaccion, TransaccionVista, transaccion_vista
from app.cuentas.dependencias import UsuarioVigente, usuario_vigente, usuario_vigente_escritura
from app.datos.registros import PortafolioRegistro
from app.db import obtener_sesion
from app.reloj import hoy_cdmx
from app.servicios import transacciones

router = APIRouter(prefix="/api", tags=["transacciones"])

SesionBd = Annotated[Session, Depends(obtener_sesion)]


@router.get("/portafolios/{portafolio_id}/transacciones")
def listar_transacciones(
    portafolio: Annotated[PortafolioRegistro, Depends(portafolio_propio)],
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente)],
    sesion: SesionBd,
) -> list[TransaccionVista]:
    """E17 (RF-05, consulta; RF-02): por fecha de concertación y luego por id."""
    return [transaccion_vista(r) for r in transacciones.listar_transacciones(sesion, usuario.id, portafolio.id)]


@router.post("/portafolios/{portafolio_id}/transacciones", status_code=status.HTTP_201_CREATED)
def registrar_transaccion(
    portafolio: Annotated[PortafolioRegistro, Depends(portafolio_propio_bloqueado)],
    cuerpo: CuerpoTransaccion,
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente_escritura)],
    sesion: SesionBd,
    hoy: Annotated[date, Depends(hoy_cdmx)],
) -> TransaccionVista:
    """E18 (CU-05 + CU-12): valida en el orden de §4.3 y registra; ningún rechazo registra nada.

    El portafolio queda bloqueado (`FOR UPDATE OF portafolio`) desde la dependencia hasta el
    commit, así que dos ventas concurrentes no pueden dejar un saldo negativo (RF-28).
    """
    registro = transacciones.registrar_transaccion(sesion, usuario.id, portafolio, cuerpo.como_nueva(), hoy)
    return transaccion_vista(registro)
