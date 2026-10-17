"""Rutas de cuentas y sesión: E02 a E07 (§4.2; §4.3; §6).

Públicas (sin `security` en OpenAPI): E02, E03, E04 y E05. E06 usa `usuario_vigente` y E07
`usuario_vigente_revocacion`. La comprobación de `Origin` de los métodos que escriben es la
dependencia global `verificar_origen` (main.py; D-41).
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.esquemas_cuentas import (
    AvisoVista,
    CuentaCreadaVista,
    CuentaVista,
    CuerpoInicioSesion,
    CuerpoRegistro,
    CuerpoRevocacion,
    SesionVista,
    aviso_vista,
    cuenta_creada_vista,
    cuenta_vista,
)
from app.config import Settings, config_actual
from app.cuentas import servicio
from app.cuentas.dependencias import UsuarioVigente, usuario_vigente, usuario_vigente_revocacion
from app.cuentas.sesion import borrar_cookie, emitir, poner_cookie
from app.db import obtener_sesion
from app.errores import MENSAJE_CONFIRMAR_REVOCACION, ConfirmacionInvalida
from app.reloj import ahora_epoch, epoch_iso

router = APIRouter(prefix="/api", tags=["cuentas"])

SesionBd = Annotated[Session, Depends(obtener_sesion)]
Config = Annotated[Settings, Depends(config_actual)]


@router.get("/aviso-privacidad")
def ver_aviso_privacidad(sesion: SesionBd) -> AvisoVista:
    """E02 (CU-09; RF-12 crit. 2): el aviso vigente, igual con sesión y sin ella."""
    return aviso_vista(servicio.aviso_vigente(sesion))


@router.post("/cuentas", status_code=status.HTTP_201_CREATED)
def registrar_cuenta(cuerpo: CuerpoRegistro, sesion: SesionBd) -> CuentaCreadaVista:
    """E03 (CU-01): alta con el otorgamiento del consentimiento. No abre la sesión (D-05)."""
    cuenta = servicio.registrar(
        sesion,
        cuerpo.correo,
        cuerpo.contrasena.get_secret_value(),
        cuerpo.consentimiento,
        cuerpo.version_aviso_id,
    )
    return cuenta_creada_vista(cuenta)


@router.post("/sesion")
def iniciar_sesion(
    cuerpo: CuerpoInicioSesion,
    respuesta: Response,
    sesion: SesionBd,
    config: Config,
    ahora: Annotated[int, Depends(ahora_epoch)],
) -> SesionVista:
    """E04 (CU-02): abre la sesión con una cookie nueva; 401 idéntico ante cualquier fallo."""
    usuario = servicio.iniciar_sesion(sesion, cuerpo.correo, cuerpo.contrasena.get_secret_value())
    valor, token = emitir(usuario.id, config.clave_sesion_bytes, ahora, config.sesion_duracion_minutos * 60)
    poner_cookie(respuesta, valor, token.expira - ahora, config)
    return SesionVista(correo=usuario.correo, expira_en=epoch_iso(token.expira))


@router.delete("/sesion", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def cerrar_sesion(config: Config) -> Response:
    """E05 (D-09): borra la cookie, aunque no haya sesión; idempotente."""
    respuesta = Response(status_code=status.HTTP_204_NO_CONTENT)
    borrar_cookie(respuesta, config)
    return respuesta


@router.get("/cuenta")
def ver_cuenta(usuario: Annotated[UsuarioVigente, Depends(usuario_vigente)], sesion: SesionBd) -> CuentaVista:
    """E06: la cuenta y sus consentimientos; el cliente sabe así si hay sesión (200 o 401)."""
    return cuenta_vista(servicio.leer_cuenta(sesion, usuario.id))


@router.post("/cuenta/revocacion", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def revocar_consentimiento(
    cuerpo: CuerpoRevocacion,
    usuario: Annotated[UsuarioVigente, Depends(usuario_vigente_revocacion)],
    sesion: SesionBd,
    config: Config,
) -> Response:
    """E07 (CU-10): registra la revocación, bloquea la cuenta y borra la cookie (RD-23)."""
    if cuerpo.confirmo is not True:
        raise ConfirmacionInvalida(MENSAJE_CONFIRMAR_REVOCACION)
    servicio.revocar(sesion, usuario.id)
    respuesta = Response(status_code=status.HTTP_204_NO_CONTENT)
    borrar_cookie(respuesta, config)
    return respuesta
