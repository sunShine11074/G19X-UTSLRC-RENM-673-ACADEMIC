"""Errores de dominio, sobre único de error y manejadores (§3.4; D-35).

Sobre: {"codigo", "regla", "mensaje", "errores"?, "datos"?}. `errores` solo aparece en
`datos_invalidos`, y `datos` solo cuando hay datos extra. Ninguna respuesta copia el `input`,
la `url` ni el `ctx` de pydantic (RNF-04; CPNF-04), y los registros llevan solo la clase de
la excepción y la ruta, sin cuerpo, parámetros ni cookies (RNF-04; RNF-05).
"""

from __future__ import annotations

import logging
import os
import traceback
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Protocol

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.routing import Match
from starlette.types import ASGIApp, Message, Receive, Scope, Send

registro = logging.getLogger("app.errores")

MENSAJE_CONFIRMAR_PORTAFOLIO = "Escribe el nombre del portafolio para confirmar."
MENSAJE_CONFIRMAR_REVOCACION = "Confirma la revocación."
SIN_REGLA = "—"


class _ConIntervalo(Protocol):
    """Cualquier objeto con `inicio` y `fin` (motor.Intervalo, IntervaloDatos…)."""

    @property
    def inicio(self) -> date: ...

    @property
    def fin(self) -> date: ...


def _ddmmaaaa(fecha: date) -> str:
    return fecha.strftime("%d/%m/%Y")


@dataclass(frozen=True)
class ErrorCampo:
    """Error de un campo: nombre del campo, regla del SRS (o «—») y mensaje sin el valor."""

    campo: str
    regla: str
    mensaje: str


class ErrorDominio(Exception):
    """Error que se responde con el sobre único."""

    estado: int
    codigo: str
    regla: str | None
    mensaje: str
    errores: tuple[ErrorCampo, ...] = ()
    datos: Mapping[str, str] | None = None
    cabeceras: Mapping[str, str] | None = None  # p. ej., el Set-Cookie que borra la sesión en un 401

    def __init__(
        self,
        estado: int,
        codigo: str,
        regla: str | None,
        mensaje: str,
        *,
        errores: Iterable[ErrorCampo] = (),
        datos: Mapping[str, str] | None = None,
        cabeceras: Mapping[str, str] | None = None,
    ) -> None:
        super().__init__(mensaje)
        self.estado = estado
        self.codigo = codigo
        self.regla = regla
        self.mensaje = mensaje
        self.errores = tuple(errores)
        self.datos = datos
        self.cabeceras = cabeceras


class SesionRequerida(ErrorDominio):
    def __init__(self, cabeceras: Mapping[str, str] | None = None) -> None:
        super().__init__(401, "sesion_requerida", "RNF-03", "Inicia sesión para continuar.", cabeceras=cabeceras)


class CredencialesInvalidas(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(
            401,
            "credenciales_invalidas",
            "RF-01",
            "No se pudo iniciar sesión. Revisa tu correo y tu contraseña; una cuenta cuyo "
            "consentimiento se revocó ya no puede abrir sesión.",
        )


class OrigenNoPermitido(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(403, "origen_no_permitido", "R-12", "Origen no permitido.")


_RECURSOS_NO_ENCONTRADOS = {
    "portafolio": "No existe el portafolio.",
    "intermediario": "No existe el intermediario.",
    "instrumento": "No existe el instrumento.",
    "recurso": "No existe el recurso.",
}


class NoEncontrado(ErrorDominio):
    """404 idéntico para lo ajeno y lo inexistente (RF-02 crit. 2; RNF-03)."""

    def __init__(self, recurso: str) -> None:
        if recurso not in _RECURSOS_NO_ENCONTRADOS:
            raise ValueError(f"Recurso desconocido: {recurso}")
        super().__init__(404, "no_encontrado", "RF-02", _RECURSOS_NO_ENCONTRADOS[recurso])


class MetodoNoPermitido(ErrorDominio):
    def __init__(self, *, cabeceras: Mapping[str, str] | None = None) -> None:
        super().__init__(
            405, "metodo_no_permitido", "RD-09", "Esta operación no está disponible.", cabeceras=cabeceras
        )


class CorreoRegistrado(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(409, "correo_registrado", "RD-03", "Ya existe una cuenta con ese correo.")


class NombreDuplicado(ErrorDominio):
    def __init__(self, recurso: str) -> None:
        if recurso not in ("portafolio", "intermediario"):
            raise ValueError(f"Recurso desconocido: {recurso}")
        super().__init__(
            409,
            "nombre_duplicado",
            "RD-03",
            f"Ya tienes un {recurso} con ese nombre (no se distinguen mayúsculas ni espacios "
            "al inicio o al final).",
        )


class AvisoCambio(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(
            409, "aviso_cambio", "RF-12", "El aviso de privacidad cambió. Léelo de nuevo antes de registrarte."
        )


class SaldoNegativo(ErrorDominio):
    """CU-12: la primera fecha en que el saldo del par quedaría negativo (RF-28)."""

    def __init__(self, clave: str, intermediario: str, fecha: date, saldo: int) -> None:
        super().__init__(
            409,
            "saldo_negativo",
            "RF-28",
            f"La venta dejaría el saldo de {clave} con {intermediario} en este portafolio en "
            f"{saldo} títulos el {_ddmmaaaa(fecha)}. El saldo con cada intermediario no puede "
            "quedar negativo, aunque la posición total alcance.",
            datos={"fecha_saldo_negativo": fecha.isoformat(), "saldo_resultante": str(saldo)},
        )


class DatosInvalidos(ErrorDominio):
    """422 con los errores por campo. La regla del sobre es la común a todos, o null si varía."""

    def __init__(self, errores: Iterable[ErrorCampo]) -> None:
        lista = tuple(errores)
        reglas = {e.regla for e in lista if e.regla != SIN_REGLA}
        regla = reglas.pop() if len(reglas) == 1 else None
        super().__init__(422, "datos_invalidos", regla, "Revisa los datos marcados.", errores=lista)


class FechaPosteriorAlRegistro(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(
            422, "fecha_posterior_al_registro", "RD-07", "La fecha de concertación no puede ser posterior a hoy."
        )


class FechaFueraDeIntervalo(ErrorDominio):
    def __init__(self, intervalo: _ConIntervalo) -> None:
        super().__init__(
            422,
            "fecha_fuera_de_intervalo",
            "RD-07",
            f"La fecha debe estar entre el {_ddmmaaaa(intervalo.inicio)} y el {_ddmmaaaa(intervalo.fin)}, "
            "el intervalo que cubren los datos de mercado.",
        )


class FechaEnODespuesDelVencimiento(ErrorDominio):
    def __init__(self, clave: str, vencimiento: date) -> None:
        super().__init__(
            422,
            "fecha_en_o_despues_del_vencimiento",
            "RF-26a",
            f"La emisión {clave} vence el {_ddmmaaaa(vencimiento)}: no se registran transacciones "
            "en esa fecha ni después.",
        )


class PlazoCetesExcedido(ErrorDominio):
    def __init__(self, limite: int) -> None:
        super().__init__(
            422,
            "plazo_cetes_excedido",
            "RD-05",
            f"La emisión vence en más de {limite} días desde la fecha de concertación.",
        )


class DivisaDistinta(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(
            422, "divisa_distinta", "RD-08", "El instrumento no está en la divisa base del portafolio (MXN)."
        )


class PeriodoInvertido(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(422, "periodo_invertido", "RF-09", "La fecha final no puede ser anterior a la inicial.")


class PeriodoFueraDeIntervalo(ErrorDominio):
    def __init__(self, intervalo: _ConIntervalo) -> None:
        primer_inicio = intervalo.inicio + timedelta(days=1)
        super().__init__(
            422,
            "periodo_fuera_de_intervalo",
            "RF-09",
            f"El periodo debe empezar a partir del {_ddmmaaaa(primer_inicio)} y terminar a más tardar "
            f"el {_ddmmaaaa(intervalo.fin)}.",
        )


class ConfirmacionInvalida(ErrorDominio):
    """RD-10 (eliminar un portafolio) o RF-12 (revocar); la regla se deduce del mensaje si no se da."""

    def __init__(self, mensaje: str, regla: str | None = None) -> None:
        if regla is None:
            regla = "RF-12" if mensaje == MENSAJE_CONFIRMAR_REVOCACION else "RD-10"
        super().__init__(422, "confirmacion_invalida", regla, mensaje)


class CifraNoCalculable(ErrorDominio):
    def __init__(self, clave: str, fecha: date) -> None:
        super().__init__(
            422,
            "cifra_no_calculable",
            "RD-24",
            f"No hay un precio o una tasa para valuar {clave} al {_ddmmaaaa(fecha)}.",
        )


class SinAvisoVigente(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(
            503,
            "sin_aviso_vigente",
            "RF-12",
            "No hay un aviso de privacidad vigente; por ahora no se pueden crear cuentas.",
        )


class SinDatosDeMercado(ErrorDominio):
    def __init__(self) -> None:
        super().__init__(503, "sin_datos_de_mercado", "RD-07", "No hay datos de mercado cargados.")


# ---------------------------------------------------------------------------
# Sobre y respuestas
# ---------------------------------------------------------------------------


def sobre(error: ErrorDominio) -> dict[str, Any]:
    """Cuerpo JSON del error."""
    cuerpo: dict[str, Any] = {"codigo": error.codigo, "regla": error.regla, "mensaje": error.mensaje}
    if error.codigo == "datos_invalidos":
        cuerpo["errores"] = [
            {"campo": e.campo, "regla": e.regla, "mensaje": e.mensaje} for e in error.errores
        ]
    if error.datos:
        cuerpo["datos"] = dict(error.datos)
    return cuerpo


def respuesta_error(error: ErrorDominio) -> JSONResponse:
    """Respuesta HTTP con el sobre y las cabeceras del error."""
    return JSONResponse(
        status_code=error.estado,
        content=sobre(error),
        headers=dict(error.cabeceras) if error.cabeceras else None,
    )


def respuesta_error_interno() -> JSONResponse:
    """500 genérico; nunca dice qué falló."""
    return JSONResponse(
        status_code=500,
        content={"codigo": "error_interno", "regla": None, "mensaje": "Ocurrió un error inesperado."},
    )


def _ubicacion(exc: BaseException) -> str:
    """Archivo, línea y función de los últimos marcos, sin el mensaje ni variables."""
    marcos = traceback.extract_tb(exc.__traceback__)[-3:]
    return " < ".join(f"{os.path.basename(m.filename)}:{m.lineno} {m.name}" for m in reversed(marcos))


def registrar_error_interno(exc: BaseException, metodo: str | None, ruta: str | None) -> None:
    """Registra solo la clase de la excepción, la ruta y dónde ocurrió (RNF-04; RNF-05)."""
    registro.error(
        "Error inesperado %s en %s %s [%s]", type(exc).__name__, metodo or "?", ruta or "?", _ubicacion(exc)
    )


# ---------------------------------------------------------------------------
# Errores de validación de FastAPI (RequestValidationError)
# ---------------------------------------------------------------------------

_UBICACIONES = frozenset({"body", "query", "path"})
_TIPOS_PROPIOS = frozenset({"dato_invalido", "fecha_invalida"})
_MENSAJES_POR_TIPO = {
    "missing": "Falta este dato.",
    "extra_forbidden": "Este dato no se puede enviar.",
    "json_invalid": "El cuerpo no es JSON válido.",
    "model_attributes_type": "El cuerpo debe ser un objeto JSON.",
    "dict_type": "El cuerpo debe ser un objeto JSON.",
    "bool_type": "Debe ser true o false.",
    "bool_parsing": "Debe ser true o false.",
}


def _campo_de(ubicacion: Sequence[Any]) -> str:
    for parte in reversed(tuple(ubicacion)):
        if isinstance(parte, str) and parte not in _UBICACIONES:
            return parte
    return SIN_REGLA


def _mensaje_de(error: Mapping[str, Any]) -> str:
    tipo = str(error.get("type", ""))
    ctx = error.get("ctx")
    if tipo in _TIPOS_PROPIOS or (isinstance(ctx, Mapping) and "regla" in ctx):
        return str(error.get("msg", "Dato inválido."))
    if tipo in _MENSAJES_POR_TIPO:
        return _MENSAJES_POR_TIPO[tipo]
    if tipo.startswith("int_") or tipo in ("greater_than_equal", "less_than_equal"):
        return "Identificador inválido."
    return "Dato inválido."


def errores_de_validacion(errores: Iterable[Mapping[str, Any]]) -> list[ErrorCampo]:
    """Convierte los errores de pydantic en ErrorCampo sin copiar `input`, `url` ni `ctx`."""
    resultado: list[ErrorCampo] = []
    for error in errores:
        ctx = error.get("ctx")
        regla = str(ctx["regla"]) if isinstance(ctx, Mapping) and "regla" in ctx else SIN_REGLA
        resultado.append(ErrorCampo(_campo_de(error.get("loc", ())), regla, _mensaje_de(error)))
    return resultado


# ---------------------------------------------------------------------------
# Manejadores
# ---------------------------------------------------------------------------


async def _manejar_dominio(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ErrorDominio)
    return respuesta_error(exc)


async def _manejar_validacion(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    return respuesta_error(DatosInvalidos(errores_de_validacion(exc.errors())))


_METODOS_HTTP = ("DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT")


def _metodos_de_la_ruta(request: Request) -> list[str]:
    """Métodos con que la ruta pedida coincide por completo (Starlette solo da los de la primera ruta)."""
    rutas = request.app.router.routes
    return [
        metodo
        for metodo in _METODOS_HTTP
        if any(ruta.matches({**request.scope, "method": metodo})[0] is Match.FULL for ruta in rutas)
    ]


async def _manejar_http(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    error: ErrorDominio
    if exc.status_code == 404:
        error = NoEncontrado("recurso")
    elif exc.status_code == 405:
        metodos = _metodos_de_la_ruta(request)
        # RFC 9110 §15.5.6: Allow lista todos los métodos de la ruta.
        error = MetodoNoPermitido(cabeceras={"Allow": ", ".join(metodos)} if metodos else exc.headers)
    else:
        error = ErrorDominio(
            exc.status_code, "error_http", None, "La solicitud no se pudo atender.", cabeceras=exc.headers
        )
    return respuesta_error(error)


async def _manejar_bd(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DBAPIError)
    from app.datos.integridad import traducir  # aquí, para no importar app.datos al cargar este módulo

    error = traducir(exc)
    if error is None:
        orig = exc.orig
        diag = getattr(orig, "diag", None)
        registro.error(
            "Error de la base sin traducción %s (SQLSTATE %s, restricción %s) en %s %s [%s]",
            type(exc).__name__,
            getattr(orig, "sqlstate", None),
            getattr(diag, "constraint_name", None),
            request.method,
            request.url.path,
            _ubicacion(exc),
        )
        return respuesta_error_interno()
    return respuesta_error(error)


async def _manejar_excepcion(request: Request, exc: Exception) -> JSONResponse:
    """Último recurso (ServerErrorMiddleware); lo normal es que lo atienda MiddlewareErrorInterno."""
    registrar_error_interno(exc, request.method, request.url.path)
    return respuesta_error_interno()


def _registrar_errores_motor(app: FastAPI) -> None:
    """Traduce los errores del motor (§5.9)."""
    from app.motor import errores as modulo  # aquí, para no importar el motor al cargar este módulo

    async def _periodo(request: Request, exc: Exception) -> JSONResponse:
        codigo = getattr(exc, "codigo", None)
        intervalo = getattr(exc, "intervalo", None)
        error: ErrorDominio
        if codigo == "periodo_invertido":
            error = PeriodoInvertido()
        elif codigo == "periodo_fuera_de_intervalo" and intervalo is not None:
            error = PeriodoFueraDeIntervalo(intervalo)
        elif codigo == "fecha_fuera_de_intervalo" and intervalo is not None:
            error = FechaFueraDeIntervalo(intervalo)
        else:
            registrar_error_interno(exc, request.method, request.url.path)
            return respuesta_error_interno()
        return respuesta_error(error)

    async def _cifra(request: Request, exc: Exception) -> JSONResponse:
        clave = getattr(exc, "clave", None) or f"el instrumento {getattr(exc, 'instrumento_id', '?')}"
        return respuesta_error(CifraNoCalculable(clave, exc.fecha))  # type: ignore[attr-defined]

    async def _historial(request: Request, exc: Exception) -> JSONResponse:
        registrar_error_interno(exc, request.method, request.url.path)
        return respuesta_error_interno()

    app.add_exception_handler(modulo.PeriodoInvalido, _periodo)
    app.add_exception_handler(modulo.CifraNoCalculable, _cifra)
    app.add_exception_handler(modulo.HistorialInvalido, _historial)


class MiddlewareErrorInterno:
    """Convierte cualquier excepción no atendida en el 500 genérico, sin volver a lanzarla.

    Así el servidor no registra el mensaje ni la traza, que podrían llevar datos (RNF-04; RNF-05).
    Va dentro de CORS y Cache-Control para que el 500 lleve sus cabeceras.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        iniciada = False

        async def enviar(mensaje: Message) -> None:
            nonlocal iniciada
            if mensaje["type"] == "http.response.start":
                iniciada = True
            await send(mensaje)

        try:
            await self.app(scope, receive, enviar)
        except Exception as exc:
            registrar_error_interno(exc, scope.get("method"), scope.get("path"))
            if not iniciada:
                await respuesta_error_interno()(scope, receive, send)


def registrar_manejadores(app: FastAPI) -> None:
    """Registra los manejadores del sobre único y el middleware del 500.

    Se llama antes de agregar otros middlewares, para que MiddlewareErrorInterno quede adentro.
    """
    app.add_exception_handler(ErrorDominio, _manejar_dominio)
    app.add_exception_handler(RequestValidationError, _manejar_validacion)
    app.add_exception_handler(StarletteHTTPException, _manejar_http)
    app.add_exception_handler(IntegrityError, _manejar_bd)
    app.add_exception_handler(DataError, _manejar_bd)
    _registrar_errores_motor(app)
    app.add_exception_handler(Exception, _manejar_excepcion)
    app.add_middleware(MiddlewareErrorInterno)
