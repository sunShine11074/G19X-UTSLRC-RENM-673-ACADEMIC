"""Dependencias de portafolio: propiedad del recurso de la ruta (§3.10; RF-02; RD-01; RNF-03).

Se resuelven antes que el cuerpo, así que un portafolio ajeno o inexistente da el mismo 404
con cualquier cuerpo (orden de validación de §4.1). FastAPI guarda en caché
`usuario_vigente*` y `obtener_sesion` dentro de cada solicitud: la ruta comparte con estas
dependencias la misma sesión de la base y, con ella, sus bloqueos.
"""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.api.tipos import IdRuta
from app.cuentas.dependencias import UsuarioVigente, usuario_vigente, usuario_vigente_escritura
from app.datos.registros import PortafolioRegistro
from app.db import obtener_sesion
from app.servicios.portafolios import obtener_portafolio

SesionBd = Annotated[Session, Depends(obtener_sesion)]


def portafolio_propio(
    portafolio_id: IdRuta,
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente)],
    sesion: SesionBd,
) -> PortafolioRegistro:
    """Lecturas (GET): el portafolio del usuario, sin bloqueo."""
    return obtener_portafolio(sesion, usuario.id, portafolio_id)


def portafolio_propio_escritura(
    portafolio_id: IdRuta,
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente_escritura)],
    sesion: SesionBd,
) -> PortafolioRegistro:
    """PATCH y DELETE: cuenta con FOR SHARE; el UPDATE o el DELETE bloquean la fila después."""
    return obtener_portafolio(sesion, usuario.id, portafolio_id)


def portafolio_propio_bloqueado(
    portafolio_id: IdRuta,
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente_escritura)],
    sesion: SesionBd,
) -> PortafolioRegistro:
    """POST de transacciones: `FOR UPDATE OF portafolio` hasta el commit de la solicitud (RF-28; R-12)."""
    return obtener_portafolio(sesion, usuario.id, portafolio_id, bloquear=True)
