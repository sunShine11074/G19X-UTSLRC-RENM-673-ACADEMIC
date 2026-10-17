"""Servicio de cuentas: aviso vigente, registro, inicio de sesión, revocación y lectura (§3.8; §6).

Reglas (RF-01; RF-12; RD-03; RD-11; RD-23; 4.3):
- El correo se guarda tal como se capturó (RD-14) y su unicidad se decide siempre en SQL,
  con la expresión del índice `lower(btrim(correo))`, nunca con `str.lower()`.
- Alta y otorgamiento van en una misma transacción; revocación y bloqueo, en otra.
- Ningún UPDATE escribe 'activa': el bloqueo es inmediato e irreversible (RD-23).
- Los momentos los fija `now()` de la base (RD-15).
- Nada se registra: ni contraseñas, ni hashes, ni correos.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import ColumnElement, func, insert, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.cuentas import contrasenas
from app.datos.modelos import Consentimiento, Usuario, VersionAviso
from app.errores import (
    AvisoCambio,
    CorreoRegistrado,
    CredencialesInvalidas,
    DatosInvalidos,
    ErrorCampo,
    SesionRequerida,
    SinAvisoVigente,
)

ACTIVA = "activa"
BLOQUEADA = "bloqueada"
MEDIO_WEB = "web"
OTORGAMIENTO = "otorgamiento"
REVOCACION = "revocacion"  # sin acento, como en 02

LARGO_MAXIMO_CORREO = 254  # al registrarse (D-44)
LARGO_MAXIMO_CORREO_SESION = 320  # al iniciar sesión: más largo da 401 sin calcular el hash

MENSAJE_CORREO = "Escribe un correo válido, como nombre@example.com."
MENSAJE_CONSENTIMIENTO = "Para registrarte debes marcar la casilla de consentimiento."


@dataclass(frozen=True)
class Aviso:
    id: int
    texto: str
    vigente_desde: datetime


@dataclass(frozen=True)
class ConsentimientoRegistro:
    tipo: str
    momento: datetime
    medio: str
    version_aviso_id: int
    aviso_vigente_desde: datetime


@dataclass(frozen=True)
class Cuenta:
    id: int
    correo: str
    estado: str
    consentimientos: tuple[ConsentimientoRegistro, ...]


@dataclass(frozen=True)
class UsuarioVigente:
    """Dueño de la solicitud. Se toma solo de la sesión, nunca del cuerpo ni de la ruta (RF-02; RD-01).

    `app.cuentas.dependencias` lo reexporta (§3.8).
    """

    id: int
    correo: str


def _clave_correo(valor: ColumnElement[str] | str) -> ColumnElement[str]:
    """Expresión del índice usuario_correo_uq: lower(btrim(…))."""
    return func.lower(func.btrim(valor))


def aviso_vigente(sesion: Session) -> Aviso:
    """La versión de mayor `vigente_desde` ≤ now() (4.4), con el texto sin alterar; si no hay, 503."""
    fila = sesion.execute(
        select(VersionAviso.id, VersionAviso.texto, VersionAviso.vigente_desde)
        .where(VersionAviso.vigente_desde <= func.now())
        .order_by(VersionAviso.vigente_desde.desc())
        .limit(1)
    ).one_or_none()
    if fila is None:
        raise SinAvisoVigente()
    return Aviso(id=fila.id, texto=fila.texto, vigente_desde=fila.vigente_desde)


def _correo_valido(correo: str) -> bool:
    """Solo la sintaxis, sin entregabilidad ni red (D-03); el valor guardado no se normaliza."""
    recortado = correo.strip(" ")  # equivale a btrim
    if not recortado or len(recortado) > LARGO_MAXIMO_CORREO:
        return False
    try:
        validate_email(recortado, check_deliverability=False)
    except EmailNotValidError:
        return False
    return True


def registrar(
    sesion: Session, correo: str, contrasena: str, consentimiento: bool, version_aviso_id: int
) -> Cuenta:
    """CU-01: valida, calcula el hash y da de alta la cuenta con su otorgamiento en una transacción.

    Errores: 422 con todos los datos inválidos juntos; 503 sin aviso vigente; 409 si el aviso
    cambió (D-46) o si el correo ya existe. No abre la sesión (D-05).
    """
    contrasena_nfkc = contrasenas.normalizar(contrasena)
    errores: list[ErrorCampo] = []
    if not _correo_valido(correo):
        errores.append(ErrorCampo("correo", "RF-01", MENSAJE_CORREO))
    errores.extend(contrasenas.errores_politica(contrasena_nfkc, correo))
    if consentimiento is not True:
        errores.append(ErrorCampo("consentimiento", "RD-11", MENSAJE_CONSENTIMIENTO))
    if errores:
        raise DatosInvalidos(errores)

    contrasena_hash = contrasenas.calcular_hash(contrasena_nfkc)  # antes de abrir la transacción

    aviso = aviso_vigente(sesion)
    if aviso.id != version_aviso_id:
        raise AvisoCambio()
    usuario_id = sesion.execute(
        pg_insert(Usuario)
        .values(correo=correo, contrasena_hash=contrasena_hash, estado=ACTIVA)
        .on_conflict_do_nothing(index_elements=[_clave_correo(Usuario.correo)])
        .returning(Usuario.id)
    ).scalar_one_or_none()
    if usuario_id is None:
        raise CorreoRegistrado()
    momento = sesion.execute(
        insert(Consentimiento)
        .values(usuario_id=usuario_id, version_aviso_id=aviso.id, tipo=OTORGAMIENTO, medio=MEDIO_WEB)
        .returning(Consentimiento.momento)
    ).scalar_one()
    sesion.commit()
    otorgamiento = ConsentimientoRegistro(
        tipo=OTORGAMIENTO,
        momento=momento,
        medio=MEDIO_WEB,
        version_aviso_id=aviso.id,
        aviso_vigente_desde=aviso.vigente_desde,
    )
    return Cuenta(id=usuario_id, correo=correo, estado=ACTIVA, consentimientos=(otorgamiento,))


def iniciar_sesion(sesion: Session, correo: str, contrasena: str) -> UsuarioVigente:
    """CU-02: el mismo 401 si el correo no existe, la contraseña es errónea o la cuenta está bloqueada.

    Si el correo no existe se verifica contra HASH_FICTICIO para igualar el tiempo. Si los
    parámetros del hash cambiaron, se guarda el hash nuevo (solo en una cuenta activa).
    """
    contrasena_nfkc = contrasenas.normalizar(contrasena)
    if (
        len(correo) > LARGO_MAXIMO_CORREO_SESION
        or len(contrasena_nfkc) > contrasenas.LARGO_MAXIMO
        or "\x00" in correo  # la base no admite NUL en un text
        or not contrasenas.codificable(correo)
        or not contrasenas.codificable(contrasena_nfkc)
    ):
        raise CredencialesInvalidas()  # sin calcular el hash
    fila = sesion.execute(
        select(Usuario.id, Usuario.correo, Usuario.contrasena_hash, Usuario.estado).where(
            _clave_correo(Usuario.correo) == _clave_correo(correo)
        )
    ).one_or_none()
    valida, hash_nuevo = contrasenas.verificar(contrasena_nfkc, None if fila is None else fila.contrasena_hash)
    if fila is None or not valida or fila.estado != ACTIVA:
        raise CredencialesInvalidas()
    if hash_nuevo is not None:
        sesion.execute(
            update(Usuario)
            .where(Usuario.id == fila.id, Usuario.estado == ACTIVA)
            .values(contrasena_hash=hash_nuevo)
        )
        sesion.commit()
    return UsuarioVigente(id=fila.id, correo=fila.correo)


def revocar(sesion: Session, usuario_id: int) -> None:
    """CU-10: registra la revocación con el aviso vigente (D-12) y bloquea la cuenta; un commit.

    Se llama con la fila del usuario bloqueada por `usuario_vigente_revocacion`
    (FOR NO KEY UPDATE), en la misma transacción.
    """
    aviso = aviso_vigente(sesion)
    sesion.execute(
        insert(Consentimiento).values(
            usuario_id=usuario_id, version_aviso_id=aviso.id, tipo=REVOCACION, medio=MEDIO_WEB
        )
    )
    bloqueadas = sesion.execute(
        update(Usuario)
        .where(Usuario.id == usuario_id, Usuario.estado == ACTIVA)
        .values(estado=BLOQUEADA)
        .returning(Usuario.id)
    ).scalars().all()
    if len(bloqueadas) != 1:
        raise SesionRequerida()  # la cuenta ya no estaba activa; se deshace la revocación
    sesion.commit()


def leer_cuenta(sesion: Session, usuario_id: int) -> Cuenta:
    """La cuenta con sus consentimientos ordenados por momento (RF-12 crit. 1, evidencia)."""
    usuario = sesion.execute(
        select(Usuario.id, Usuario.correo, Usuario.estado).where(Usuario.id == usuario_id)
    ).one_or_none()
    if usuario is None:
        raise SesionRequerida()
    filas = sesion.execute(
        select(
            Consentimiento.tipo,
            Consentimiento.momento,
            Consentimiento.medio,
            Consentimiento.version_aviso_id,
            VersionAviso.vigente_desde,
        )
        .join(VersionAviso, VersionAviso.id == Consentimiento.version_aviso_id)
        .where(Consentimiento.usuario_id == usuario_id)
        .order_by(Consentimiento.momento, Consentimiento.id)
    ).all()
    consentimientos = tuple(
        ConsentimientoRegistro(
            tipo=f.tipo,
            momento=f.momento,
            medio=f.medio,
            version_aviso_id=f.version_aviso_id,
            aviso_vigente_desde=f.vigente_desde,
        )
        for f in filas
    )
    return Cuenta(id=usuario.id, correo=usuario.correo, estado=usuario.estado, consentimientos=consentimientos)
