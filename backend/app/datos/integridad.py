"""Traducción de IntegrityError y DataError de PostgreSQL a errores de dominio (§3.7).

Lee `exc.orig.sqlstate` y `exc.orig.diag.constraint_name`; en un índice único, el nombre que
reporta PostgreSQL es el del índice. Lo que no se traduce (42501, otro 23503…) es un error de
programación: el manejador responde 500 y lo registra sin parámetros.
"""

from sqlalchemy.exc import DBAPIError

from app.errores import (
    CorreoRegistrado,
    DatosInvalidos,
    ErrorCampo,
    ErrorDominio,
    FechaPosteriorAlRegistro,
    NoEncontrado,
    NombreDuplicado,
    SIN_REGLA,
)

_UNICOS = {
    "usuario_correo_uq": lambda: CorreoRegistrado(),
    "portafolio_nombre_uq": lambda: NombreDuplicado("portafolio"),
    "intermediario_nombre_uq": lambda: NombreDuplicado("intermediario"),
}

_LLAVES_FORANEAS = {
    "transaccion_portafolio_fk": "portafolio",
    "transaccion_intermediario_fk": "intermediario",
    "transaccion_instrumento_fk": "instrumento",
}

# CHECK de transaccion y portafolio: (campo, regla, mensaje), con los mensajes de la API (§3.5).
_CHECKS: dict[str, tuple[str, str, str]] = {
    "transaccion_tipo_ck": ("tipo", "RF-05", "El tipo debe ser compra o venta."),
    "transaccion_cantidad_ck": ("cantidad", "RD-06", "La cantidad de títulos debe ser un entero mayor que cero."),
    "transaccion_precio_ck": ("precio", "RD-06", "El precio debe ser mayor que cero."),
    "transaccion_precio_escala_ck": ("precio", "RD-13", "El precio admite a lo más 7 decimales; no se redondea."),
    "transaccion_precio_tamano_ck": ("precio", "RD-12", "El precio es demasiado grande."),
    "transaccion_importe_comisiones_ck": ("importe_comisiones", "RF-05", "El importe no puede ser negativo."),
    "transaccion_importe_comisiones_escala_ck": (
        "importe_comisiones",
        "RD-13",
        "El importe admite a lo más 2 decimales; no se redondea.",
    ),
    "transaccion_importe_comisiones_tamano_ck": ("importe_comisiones", "RD-12", "El importe es demasiado grande."),
    "transaccion_importe_venta_ck": (
        "importe_comisiones",
        "RF-05",
        "En una venta, el importe de las comisiones debe ser menor que títulos × precio.",
    ),
    "portafolio_divisa_base_ck": ("divisa_base", "RD-08", "En esta versión la única divisa base es MXN."),
}

_ESTADOS_DE_DATOS = frozenset({"22003", "22008", "22P02"})  # fuera de rango, fecha inválida, texto inválido


def _campo_de_restriccion(nombre: str) -> str:
    """transaccion_precio_escala_ck → precio; transaccion_importe_venta_ck → importe_comisiones."""
    campo = nombre.removeprefix("transaccion_").removesuffix("_ck")
    for sufijo in ("_escala", "_tamano"):
        campo = campo.removesuffix(sufijo)
    return "importe_comisiones" if campo == "importe_venta" else campo


def traducir(exc: DBAPIError) -> ErrorDominio | None:
    """Error de dominio que corresponde a la violación, o None si no hay traducción."""
    orig = exc.orig
    sqlstate = getattr(orig, "sqlstate", None)
    diag = getattr(orig, "diag", None)
    restriccion = getattr(diag, "constraint_name", None) or ""

    if sqlstate == "23505" and restriccion in _UNICOS:
        return _UNICOS[restriccion]()
    if sqlstate == "23514":
        if restriccion == "transaccion_fecha_concertacion_ck":
            return FechaPosteriorAlRegistro()
        if restriccion.endswith("_nombre_ck"):
            return DatosInvalidos([ErrorCampo("nombre", "RD-03", "Escribe un nombre.")])
        if restriccion in _CHECKS:
            return DatosInvalidos([ErrorCampo(*_CHECKS[restriccion])])
        if restriccion.startswith("transaccion_") and restriccion.endswith("_ck"):
            return DatosInvalidos([ErrorCampo(_campo_de_restriccion(restriccion), SIN_REGLA, "Dato inválido.")])
        return None
    if sqlstate == "23503" and restriccion in _LLAVES_FORANEAS:
        return NoEncontrado(_LLAVES_FORANEAS[restriccion])
    if sqlstate in _ESTADOS_DE_DATOS:
        return DatosInvalidos([ErrorCampo(SIN_REGLA, SIN_REGLA, "Dato inválido.")])
    return None
