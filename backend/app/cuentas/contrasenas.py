"""Contraseñas: hash Argon2id, verificación y política (§6.2; RNF-04; P-06; D-02; D-04).

El hash usa el mínimo de OWASP con p = 1: `$argon2id$v=19$m=19456,t=2,p=1$…`, con sal
aleatoria por cuenta. No se usa `PasswordHash.recommended()`, que deja p = 4. Ninguna
función registra ni devuelve en un mensaje la contraseña o el hash.
"""

import secrets
import unicodedata

from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from pwdlib.hashers.argon2 import Argon2Hasher

from app.errores import ErrorCampo

LARGO_MINIMO = 15  # recomendado de RF-01 crit. 1
LARGO_MAXIMO = 128  # D-02
REGLA = "RF-01"

HASHER = PasswordHash((Argon2Hasher(time_cost=2, memory_cost=19456, parallelism=1),))

# Hash de una contraseña al azar: iguala el tiempo de respuesta cuando el correo no existe.
HASH_FICTICIO: str = HASHER.hash(secrets.token_urlsafe(32))


def normalizar(contrasena: str) -> str:
    """Forma NFKC, al registrarse y al iniciar sesión (D-02). No recorta ni trunca."""
    return unicodedata.normalize("NFKC", contrasena)


def codificable(texto: str) -> bool:
    """False si el texto no se puede codificar en UTF-8 (p. ej., un sustituto suelto como «\\ud800»).

    JSON y pydantic los admiten, pero Argon2 y la base no: sin esta revisión darían un 500.
    """
    try:
        texto.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def errores_politica(contrasena_nfkc: str, correo: str) -> list[ErrorCampo]:
    """Errores de la política (D-02), sin repetir el valor; lista vacía si la cumple.

    Largo de 15 a 128 puntos de código, sin reglas de composición, y distinta del correo
    (comparados con `casefold()` y sin los espacios de los extremos). Además, codificable en
    UTF-8, para poder calcular el hash.
    """
    errores: list[ErrorCampo] = []
    if not codificable(contrasena_nfkc):
        errores.append(ErrorCampo("contrasena", REGLA, "La contraseña tiene caracteres no válidos."))
    if len(contrasena_nfkc) < LARGO_MINIMO:
        errores.append(ErrorCampo("contrasena", REGLA, "La contraseña debe tener al menos 15 caracteres."))
    elif len(contrasena_nfkc) > LARGO_MAXIMO:
        errores.append(ErrorCampo("contrasena", REGLA, "La contraseña admite a lo más 128 caracteres."))
    correo_comparable = normalizar(correo).strip().casefold()
    if correo_comparable and contrasena_nfkc.strip().casefold() == correo_comparable:
        errores.append(ErrorCampo("contrasena", REGLA, "La contraseña no puede ser tu correo."))
    return errores


def calcular_hash(contrasena_nfkc: str) -> str:
    """Hash Argon2id con sal nueva; se calcula antes de abrir la transacción de la base."""
    return HASHER.hash(contrasena_nfkc)


def verificar(contrasena_nfkc: str, hash_guardado: str | None) -> tuple[bool, str | None]:
    """(válida, hash nuevo o None). Con `hash_guardado=None` verifica contra HASH_FICTICIO.

    El hash nuevo aparece cuando los parámetros guardados no son los actuales (*rehash*).
    Un hash que no se reconoce cuenta como contraseña errónea y no se registra.
    """
    if hash_guardado is None:
        HASHER.verify(contrasena_nfkc, HASH_FICTICIO)
        return False, None
    try:
        return HASHER.verify_and_update(contrasena_nfkc, hash_guardado)
    except UnknownHashError:
        return False, None
