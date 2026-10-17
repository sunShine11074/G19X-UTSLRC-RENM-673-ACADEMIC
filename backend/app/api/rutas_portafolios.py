"""Rutas del catálogo, los intermediarios y los portafolios: E08 y E10 a E16 (§4.2; §4.3).

Todas exigen sesión (D-08). Las lecturas usan `usuario_vigente` y las escrituras
`usuario_vigente_escritura` (FOR SHARE). No existen escrituras del catálogo ni PUT, PATCH o
DELETE de intermediarios (RD-09): un método no ofrecido da 405.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.comunes import (
    InstrumentoVista,
    IntermediarioVista,
    PortafolioVista,
    instrumento_vista,
    intermediario_vista,
    portafolio_vista,
)
from app.api.dependencias import portafolio_propio, portafolio_propio_escritura
from app.api.esquemas_portafolios import CuerpoEliminar, CuerpoIntermediario, CuerpoPortafolio, CuerpoRenombrar
from app.cuentas.dependencias import UsuarioVigente, usuario_vigente, usuario_vigente_escritura
from app.datos.registros import PortafolioRegistro
from app.db import obtener_sesion
from app.servicios import portafolios

router = APIRouter(prefix="/api")

SesionBd = Annotated[Session, Depends(obtener_sesion)]
Lector = Annotated[UsuarioVigente, Depends(usuario_vigente)]
Escritor = Annotated[UsuarioVigente, Depends(usuario_vigente_escritura)]


# ---------------------------------------------------------------------------
# Catálogo (CU-08)
# ---------------------------------------------------------------------------


@router.get("/instrumentos", tags=["catálogo"], dependencies=[Depends(usuario_vigente)])
def listar_instrumentos(sesion: SesionBd) -> list[InstrumentoVista]:
    """E08 (RF-04; RD-04): el catálogo, ordenado por clave; los CETES con vencimiento y valor nominal."""
    return [instrumento_vista(r) for r in portafolios.listar_instrumentos(sesion)]


# ---------------------------------------------------------------------------
# Intermediarios (CU-04)
# ---------------------------------------------------------------------------


@router.get("/intermediarios", tags=["intermediarios"])
def listar_intermediarios(usuario: Lector, sesion: SesionBd) -> list[IntermediarioVista]:
    """E10 (RF-25 crit. 1; RF-02): solo los intermediarios del usuario."""
    return [intermediario_vista(r) for r in portafolios.listar_intermediarios(sesion, usuario.id)]


@router.post("/intermediarios", tags=["intermediarios"], status_code=status.HTTP_201_CREATED)
def crear_intermediario(cuerpo: CuerpoIntermediario, usuario: Escritor, sesion: SesionBd) -> IntermediarioVista:
    """E11 (RF-25; RD-03; RD-09): el nombre se guarda tal como se capturó; 409 si ya existe."""
    return intermediario_vista(portafolios.crear_intermediario(sesion, usuario.id, cuerpo.nombre))


# ---------------------------------------------------------------------------
# Portafolios (CU-03)
# ---------------------------------------------------------------------------


@router.get("/portafolios", tags=["portafolios"])
def listar_portafolios(usuario: Lector, sesion: SesionBd) -> list[PortafolioVista]:
    """E12 (RF-03; RF-02 crit. 1): solo los portafolios del usuario."""
    return [portafolio_vista(r) for r in portafolios.listar_portafolios(sesion, usuario.id)]


@router.post("/portafolios", tags=["portafolios"], status_code=status.HTTP_201_CREATED)
def crear_portafolio(cuerpo: CuerpoPortafolio, usuario: Escritor, sesion: SesionBd) -> PortafolioVista:
    """E13 (RF-03 crit. 1 y 2; RD-03; RD-08): divisa base MXN; 409 si el nombre ya existe."""
    return portafolio_vista(portafolios.crear_portafolio(sesion, usuario.id, cuerpo.nombre))


@router.get("/portafolios/{portafolio_id}", tags=["portafolios"])
def ver_portafolio(portafolio: Annotated[PortafolioRegistro, Depends(portafolio_propio)]) -> PortafolioVista:
    """E14 (RF-03; RF-02): 404 si no existe o es ajeno."""
    return portafolio_vista(portafolio)


@router.patch("/portafolios/{portafolio_id}", tags=["portafolios"])
def renombrar_portafolio(
    portafolio: Annotated[PortafolioRegistro, Depends(portafolio_propio_escritura)],
    cuerpo: CuerpoRenombrar,
    usuario: Escritor,
    sesion: SesionBd,
) -> PortafolioVista:
    """E15 (RF-03 crit. 1 y 2; RD-03): solo cambia el nombre."""
    return portafolio_vista(portafolios.renombrar_portafolio(sesion, usuario.id, portafolio.id, cuerpo.nombre))


@router.delete(
    "/portafolios/{portafolio_id}",
    tags=["portafolios"],
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def eliminar_portafolio(
    portafolio: Annotated[PortafolioRegistro, Depends(portafolio_propio_escritura)],
    cuerpo: CuerpoEliminar,
    usuario: Escritor,
    sesion: SesionBd,
) -> Response:
    """E16 (RF-03 crit. 3; RD-10; D-10): con la confirmación, borra el portafolio y sus transacciones.

    Los intermediarios se conservan. Si la confirmación no coincide con el nombre: 422, sin cambios.
    """
    portafolios.eliminar_portafolio(sesion, usuario.id, portafolio.id, cuerpo.confirmacion)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
