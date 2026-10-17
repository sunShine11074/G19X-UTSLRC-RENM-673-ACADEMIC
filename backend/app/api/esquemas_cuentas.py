"""Cuerpos y respuestas de las rutas de cuentas y sesión, E02 a E07 (§4.3).

La contraseña llega como `SecretStr`: no aparece en el repr ni en los errores (RNF-04).
Ninguna respuesta lleva `contrasena_hash`. Los momentos van en ISO 8601 con el desfase de
la Ciudad de México (RD-15).
"""

from pydantic import BaseModel, SecretStr, StrictBool

from app.api.tipos import Identificador, ModeloEntrada
from app.cuentas.servicio import Aviso, ConsentimientoRegistro, Cuenta
from app.reloj import momento_iso


class CuerpoRegistro(ModeloEntrada):
    """E03. La sintaxis del correo, la política de la contraseña y el consentimiento los revisa el servicio."""

    correo: str
    contrasena: SecretStr
    consentimiento: StrictBool
    version_aviso_id: Identificador


class CuerpoInicioSesion(ModeloEntrada):
    """E04. No se valida la sintaxis del correo."""

    correo: str
    contrasena: SecretStr


class CuerpoRevocacion(ModeloEntrada):
    """E07. Un valor distinto de true da 422 `confirmacion_invalida` (D-11)."""

    confirmo: StrictBool


class AvisoVista(BaseModel):
    id: int
    texto: str
    vigente_desde: str


class ConsentimientoOtorgadoVista(BaseModel):
    tipo: str
    momento: str
    medio: str
    version_aviso_id: int


class CuentaCreadaVista(BaseModel):
    correo: str
    estado: str
    consentimiento: ConsentimientoOtorgadoVista


class SesionVista(BaseModel):
    correo: str
    expira_en: str  # ISO 8601 con desfase


class ConsentimientoVista(BaseModel):
    tipo: str
    momento: str
    medio: str
    version_aviso_id: int
    aviso_vigente_desde: str


class CuentaVista(BaseModel):
    correo: str
    estado: str
    consentimientos: list[ConsentimientoVista]


def aviso_vista(a: Aviso) -> AvisoVista:
    return AvisoVista(id=a.id, texto=a.texto, vigente_desde=momento_iso(a.vigente_desde))


def cuenta_creada_vista(c: Cuenta) -> CuentaCreadaVista:
    otorgamiento = c.consentimientos[0]
    return CuentaCreadaVista(
        correo=c.correo,
        estado=c.estado,
        consentimiento=ConsentimientoOtorgadoVista(
            tipo=otorgamiento.tipo,
            momento=momento_iso(otorgamiento.momento),
            medio=otorgamiento.medio,
            version_aviso_id=otorgamiento.version_aviso_id,
        ),
    )


def consentimiento_vista(r: ConsentimientoRegistro) -> ConsentimientoVista:
    return ConsentimientoVista(
        tipo=r.tipo,
        momento=momento_iso(r.momento),
        medio=r.medio,
        version_aviso_id=r.version_aviso_id,
        aviso_vigente_desde=momento_iso(r.aviso_vigente_desde),
    )


def cuenta_vista(c: Cuenta) -> CuentaVista:
    return CuentaVista(
        correo=c.correo, estado=c.estado, consentimientos=[consentimiento_vista(r) for r in c.consentimientos]
    )
