"""Dependencias de FastAPI para la sesión, la autorización por propietario y el origen (§3.8; §6.4; §6.6).

`usuario_vigente*` (RD-23; RF-02; RD-01):
1. Lee la cookie. Si no es válida → 401 `SesionRequerida`, que borra la cookie, sin consultar
   la base (RNF-03).
2. Consulta la cuenta con el bloqueo de la variante:
   - `usuario_vigente` (lecturas): sin bloqueo;
   - `usuario_vigente_escritura`: FOR SHARE, para que una revocación concurrente espere;
   - `usuario_vigente_revocacion` (solo E07): FOR NO KEY UPDATE. Con FOR SHARE y luego UPDATE
     habría *deadlock*.
3. Sin fila o con la cuenta bloqueada → `SesionRequerida`.
4. Devuelve `UsuarioVigente(id, correo)`: el dueño sale solo de aquí.

FastAPI guarda en caché estas dependencias y `obtener_sesion` dentro de cada solicitud, así
que la ruta comparte la sesión de la base (y el bloqueo) con ellas.
"""

from typing import Annotated

from fastapi import Depends, Request, Security
from fastapi.security import APIKeyCookie
from sqlalchemy import TextClause, text
from sqlalchemy.orm import Session

from app.config import Settings, config_actual
from app.cuentas.servicio import ACTIVA, UsuarioVigente
from app.cuentas.sesion import NOMBRE_COOKIE, cabecera_borrado, leer
from app.db import obtener_sesion
from app.errores import OrigenNoPermitido, SesionRequerida
from app.reloj import ahora_epoch

__all__ = [
    "UsuarioVigente",
    "cookie_sesion",
    "usuario_vigente",
    "usuario_vigente_escritura",
    "usuario_vigente_revocacion",
    "verificar_origen",
]

# Esquema «security» de OpenAPI; con auto_error=False, sin cookie da None (y el 401 es el propio).
cookie_sesion = APIKeyCookie(name=NOMBRE_COOKIE, auto_error=False, scheme_name="sesion_077")

_CONSULTA = "SELECT correo, estado FROM usuario WHERE id = :u"
_SIN_BLOQUEO = text(_CONSULTA)
_FOR_SHARE = text(_CONSULTA + " FOR SHARE")
_FOR_NO_KEY_UPDATE = text(_CONSULTA + " FOR NO KEY UPDATE")

METODOS_SIN_ORIGEN = frozenset({"GET", "HEAD", "OPTIONS"})

ValorCookie = Annotated[str | None, Security(cookie_sesion)]
SesionBd = Annotated[Session, Depends(obtener_sesion)]
Config = Annotated[Settings, Depends(config_actual)]
Ahora = Annotated[int, Depends(ahora_epoch)]


def _usuario(valor: str | None, sesion: Session, config: Settings, ahora: int, consulta: TextClause) -> UsuarioVigente:
    token = leer(valor, config.clave_sesion_bytes, ahora, config.sesion_duracion_minutos * 60)
    if token is None:
        raise SesionRequerida(cabeceras=cabecera_borrado(config))
    fila = sesion.execute(consulta, {"u": token.usuario_id}).one_or_none()
    if fila is None or fila.estado != ACTIVA:
        raise SesionRequerida(cabeceras=cabecera_borrado(config))
    return UsuarioVigente(id=token.usuario_id, correo=fila.correo)


def usuario_vigente(valor: ValorCookie, sesion: SesionBd, config: Config, ahora: Ahora) -> UsuarioVigente:
    """Lecturas (L): SELECT sin bloqueo."""
    return _usuario(valor, sesion, config, ahora, _SIN_BLOQUEO)


def usuario_vigente_escritura(valor: ValorCookie, sesion: SesionBd, config: Config, ahora: Ahora) -> UsuarioVigente:
    """Escrituras (E): SELECT … FOR SHARE, hasta el commit o el rollback de la solicitud."""
    return _usuario(valor, sesion, config, ahora, _FOR_SHARE)


def usuario_vigente_revocacion(valor: ValorCookie, sesion: SesionBd, config: Config, ahora: Ahora) -> UsuarioVigente:
    """Solo E07 (R): SELECT … FOR NO KEY UPDATE, en la misma transacción que la revocación."""
    return _usuario(valor, sesion, config, ahora, _FOR_NO_KEY_UPDATE)


def verificar_origen(request: Request, config: Config) -> None:
    """Dependencia global (D-41): todo método que no sea GET, HEAD ni OPTIONS exige un `Origin` permitido.

    Se aplica también al registro, al inicio y al cierre de sesión (CSRF de *login*): en
    localhost todos los puertos son el mismo sitio y SameSite=Strict no basta.
    """
    if request.method in METODOS_SIN_ORIGEN:
        return
    origenes = request.headers.getlist("origin")
    if len(origenes) != 1 or origenes[0] not in config.lista_origenes:
        raise OrigenNoPermitido()
