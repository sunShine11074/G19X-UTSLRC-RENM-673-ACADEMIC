"""Cookie de sesión firmada con HMAC-SHA256, solo con la biblioteca estándar (§6.4; D-01).

Valor: `v1.<usuario_id>.<iat>.<exp>.<nonce>.<firma>`, de 115 caracteres o menos.
- `iat` y `exp`: segundos de época UTC; `exp = iat + duración`.
- `nonce`: `secrets.token_urlsafe(16)`, 22 caracteres.
- `firma`: base64url sin relleno de HMAC-SHA256(clave, «proyecto077/sesion/v1|» + mensaje),
  43 caracteres; `mensaje` es `v1.uid.iat.exp.nonce` en ASCII.

La caducidad es absoluta y no se renueva. Sin tabla de sesiones: cada solicitud comprueba
además que la cuenta siga activa (dependencias.py; RD-23). Cambiar SESION_CLAVE invalida
todas las sesiones. Ni el valor de la cookie ni la clave se registran (RNF-05).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import http.cookies
import re
import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # solo anotaciones: este módulo no importa FastAPI ni Starlette (§2)
    from starlette.responses import Response

    from app.config import Settings

NOMBRE_COOKIE = "sesion_077"
RUTA_COOKIE = "/api"
VERSION = "v1"
LARGO_MAXIMO_VALOR = 160
TOLERANCIA_RELOJ_S = 60  # un iat hasta 60 s en el futuro se admite

_PREFIJO_FIRMA = b"proyecto077/sesion/v1|"
_PATRON = re.compile(
    r"v1\.([1-9][0-9]{0,18})\.([0-9]{1,12})\.([0-9]{1,12})\.([A-Za-z0-9_-]{22})\.([A-Za-z0-9_-]{43})"
)


@dataclass(frozen=True)
class TokenSesion:
    usuario_id: int
    emitida: int  # iat
    expira: int  # exp


def _firma(mensaje: str, clave: bytes) -> str:
    digest = hmac.new(clave, _PREFIJO_FIRMA + mensaje.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def emitir(usuario_id: int, clave: bytes, ahora: int, duracion_s: int) -> tuple[str, TokenSesion]:
    """Emite un token nuevo (cada inicio de sesión reemplaza la cookie: sin fijación de sesión)."""
    if usuario_id < 1 or duracion_s < 1:
        raise ValueError("usuario_id y duracion_s deben ser positivos.")
    token = TokenSesion(usuario_id=usuario_id, emitida=ahora, expira=ahora + duracion_s)
    mensaje = f"{VERSION}.{token.usuario_id}.{token.emitida}.{token.expira}.{secrets.token_urlsafe(16)}"
    return f"{mensaje}.{_firma(mensaje, clave)}", token


def leer(valor: str | None, clave: bytes, ahora: int, duracion_s: int) -> TokenSesion | None:
    """Token de la cookie, o None si falta, está mal formada, alterada o caducada.

    Orden: largo; forma; firma con `compare_digest`, antes de interpretar los números;
    `iat ≤ ahora + 60`, `ahora < exp` y `0 < exp − iat ≤ duracion_s`.
    """
    if not valor or len(valor) > LARGO_MAXIMO_VALOR:
        return None
    coincidencia = _PATRON.fullmatch(valor)
    if coincidencia is None:
        return None
    mensaje, _, firma = valor.rpartition(".")
    if not hmac.compare_digest(_firma(mensaje, clave), firma):
        return None
    usuario_id, emitida, expira = (int(coincidencia.group(i)) for i in (1, 2, 3))
    if emitida > ahora + TOLERANCIA_RELOJ_S or ahora >= expira or not 0 < expira - emitida <= duracion_s:
        return None
    return TokenSesion(usuario_id=usuario_id, emitida=emitida, expira=expira)


def poner_cookie(respuesta: Response, valor: str, max_age: int, config: Settings) -> None:
    """HttpOnly; SameSite=Strict; Path=/api; Max-Age; sin Domain; Secure según la configuración."""
    respuesta.set_cookie(
        NOMBRE_COOKIE,
        valor,
        max_age=max_age,
        path=RUTA_COOKIE,
        secure=config.sesion_cookie_segura,
        httponly=True,
        samesite="strict",
    )


def borrar_cookie(respuesta: Response, config: Settings) -> None:
    """Borra la cookie con los mismos atributos con que se puso (delete_cookie usa lax y no HttpOnly)."""
    respuesta.delete_cookie(
        NOMBRE_COOKIE,
        path=RUTA_COOKIE,
        secure=config.sesion_cookie_segura,
        httponly=True,
        samesite="strict",
    )


def cabecera_borrado(config: Settings) -> dict[str, str]:
    """{"set-cookie": …} que borra la cookie, para `SesionRequerida`; igual al de `borrar_cookie`."""
    cookie: http.cookies.SimpleCookie = http.cookies.SimpleCookie()
    cookie[NOMBRE_COOKIE] = ""
    morsel = cookie[NOMBRE_COOKIE]
    morsel["max-age"] = 0
    morsel["expires"] = 0
    morsel["path"] = RUTA_COOKIE
    if config.sesion_cookie_segura:
        morsel["secure"] = True
    morsel["httponly"] = True
    morsel["samesite"] = "strict"
    return {"set-cookie": cookie.output(header="").strip()}
