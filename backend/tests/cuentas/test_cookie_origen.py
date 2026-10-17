"""Cookie de sesión, comprobación del origen, CORS y `security` en OpenAPI (§6.4; §6.6; D-01; D-41; D-42; §8.3)."""

from __future__ import annotations

import http.cookies
import re
import secrets
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.config import Settings
from app.cuentas.sesion import (
    NOMBRE_COOKIE,
    TokenSesion,
    borrar_cookie,
    cabecera_borrado,
    emitir,
    leer,
    poner_cookie,
)
from app.reloj import epoch_iso
from tests.conftest import ORIGEN_PRUEBAS, URL_BASE_PRUEBAS, ClientePrueba, CuentaPrueba
from tests.cuentas.apoyo import (
    ORIGEN_NO_PERMITIDO,
    SESION_REQUERIDA,
    con_cookie,
    contrasena_nueva,
    es_borrado,
    iniciar,
    morsel,
    registrar,
)

DURACION = 480 * 60
PATRON_VALOR = re.compile(r"v1\.[1-9][0-9]{0,18}\.[0-9]{1,12}\.[0-9]{1,12}\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}")
RUTAS_PUBLICAS = {
    ("GET", "/health"),
    ("GET", "/api/aviso-privacidad"),
    ("POST", "/api/cuentas"),
    ("POST", "/api/sesion"),
    ("DELETE", "/api/sesion"),
}


def _config(**cambios: Any) -> Settings:
    valores: dict[str, Any] = {
        "database_url": "postgresql+psycopg://app_077:x@127.0.0.1:1/nada",
        "sesion_clave": secrets.token_urlsafe(32),
    }
    valores.update(cambios)
    return Settings(_env_file=None, **valores)  # type: ignore[call-arg]


# ---------------------------------------------------------------------------
# Token y cookie, sin base de datos
# ---------------------------------------------------------------------------


def test_emitir_y_leer() -> None:
    clave = secrets.token_bytes(32)
    ahora = 1_792_000_000
    valor, token = emitir(42, clave, ahora, DURACION)
    assert token == TokenSesion(usuario_id=42, emitida=ahora, expira=ahora + DURACION)
    assert PATRON_VALOR.fullmatch(valor)
    assert leer(valor, clave, ahora, DURACION) == token
    assert leer(valor, clave, ahora + DURACION - 1, DURACION) == token
    assert emitir(42, clave, ahora, DURACION)[0] != valor  # nonce nuevo en cada inicio de sesión

    # El valor más largo posible cabe en 115 caracteres.
    largo, _ = emitir(2**63 - 1, clave, 999_999_999_999 - DURACION, DURACION)
    assert len(largo) == 115 and PATRON_VALOR.fullmatch(largo)


def test_leer_rechaza_lo_alterado_caducado_o_mal_formado() -> None:
    clave = secrets.token_bytes(32)
    ahora = 1_792_000_000
    valor, _ = emitir(42, clave, ahora, DURACION)

    # Cualquier carácter cambiado invalida la cookie.
    for i, caracter in enumerate(valor):
        for sustituto in {"A", "0", "_"} - {caracter}:
            alterado = valor[:i] + sustituto + valor[i + 1 :]
            assert leer(alterado, clave, ahora, DURACION) is None, i

    assert leer(valor, secrets.token_bytes(32), ahora, DURACION) is None  # otra clave
    assert leer(valor, clave, ahora + DURACION, DURACION) is None  # caducada: ahora = exp
    assert leer(valor, clave, ahora - 61, DURACION) is None  # emitida más de 60 s en el futuro
    assert leer(valor, clave, ahora - 60, DURACION) is not None
    assert leer(valor, clave, ahora, DURACION - 1) is None  # exp − iat mayor que la duración

    larga, _ = emitir(42, clave, ahora, DURACION + 1)
    assert leer(larga, clave, ahora, DURACION) is None
    for malo in (None, "", "v1", valor + ".", valor + "x" * 50, "v2" + valor[2:], valor.replace(".", ",", 1),
                 " " + valor, "v1.٤٢" + valor[4:]):
        assert leer(malo, clave, ahora, DURACION) is None


def test_atributos_de_la_cookie() -> None:
    for segura in (False, True):
        config = _config(sesion_cookie_segura=segura)
        puesta = Response()
        poner_cookie(puesta, "valor", 28_800, config)
        cabecera = puesta.headers["set-cookie"]
        cookie: http.cookies.SimpleCookie = http.cookies.SimpleCookie()
        cookie.load(cabecera)
        m = cookie[NOMBRE_COOKIE]
        assert m.value == "valor" and m["max-age"] == "28800" and m["path"] == "/api"
        assert m["httponly"] is True and m["samesite"].lower() == "strict" and m["domain"] == ""
        assert bool(m["secure"]) is segura and m["expires"] == ""

        borrada = Response()
        borrar_cookie(borrada, config)
        propia = cabecera_borrado(config)
        assert set(propia) == {"set-cookie"}
        sin_fecha = re.compile(r"expires=[^;]+; ")
        assert sin_fecha.sub("", propia["set-cookie"]) == sin_fecha.sub("", borrada.headers["set-cookie"])
        assert "HttpOnly" in propia["set-cookie"] and "Max-Age=0" in propia["set-cookie"]
        assert ("Secure" in propia["set-cookie"]) is segura


# ---------------------------------------------------------------------------
# Por la API
# ---------------------------------------------------------------------------


@contextmanager
def _consultas(app: FastAPI) -> Iterator[list[str]]:
    """Sentencias SQL que ejecuta la aplicación mientras dura el bloque."""
    sentencias: list[str] = []

    def anotar(conn: Any, cursor: Any, sentencia: str, *args: Any) -> None:
        sentencias.append(sentencia)

    engine = app.state.engine
    event.listen(engine, "before_cursor_execute", anotar)
    try:
        yield sentencias
    finally:
        event.remove(engine, "before_cursor_execute", anotar)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cookie_al_iniciar_sesion(cliente: ClientePrueba, reloj: Any) -> None:
    ahora = int(time.time())
    reloj.fijar_ahora(ahora)
    contrasena = contrasena_nueva()
    assert registrar(cliente, "ana@example.com", contrasena).status_code == 201

    inicio = iniciar(cliente, "ana@example.com", contrasena)
    assert inicio.status_code == 200
    assert inicio.json() == {"correo": "ana@example.com", "expira_en": epoch_iso(ahora + DURACION)}
    m = morsel(inicio)
    assert PATRON_VALOR.fullmatch(m.value) and len(m.value) <= 115
    assert m["httponly"] is True and m["samesite"].lower() == "strict"
    assert m["path"] == "/api" and m["max-age"] == str(DURACION)
    assert m["domain"] == "" and not m["secure"]
    assert cliente.get("/api/cuenta").status_code == 200

    # Cada inicio de sesión emite un token nuevo y reemplaza la cookie (sin fijación de sesión).
    segundo = iniciar(cliente, "ana@example.com", contrasena)
    assert morsel(segundo).value != m.value
    assert cliente.cookies.get(NOMBRE_COOKIE) == morsel(segundo).value


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cookie_invalida_da_401_sin_consultar_la_base(
    app_pruebas: FastAPI, config_pruebas: Settings, nueva_cuenta: Callable[..., CuentaPrueba]
) -> None:
    ana = nueva_cuenta("ana@example.com")
    valor = ana.cliente.cookies.get(NOMBRE_COOKIE)
    assert valor
    ahora = int(time.time())
    clave = config_pruebas.clave_sesion_bytes
    i = valor.index(".", 3) + 1  # primer dígito de iat
    alterados = {
        "un byte del nonce": valor[:-50] + ("A" if valor[-50] != "A" else "B") + valor[-49:],
        "un byte del iat": valor[:i] + ("1" if valor[i] != "1" else "2") + valor[i + 1 :],
        "la firma": valor[:-1] + ("A" if valor[-1] != "A" else "B"),
        "otra clave": emitir(ana.usuario_id, secrets.token_bytes(32), ahora, DURACION)[0],
        "duración mayor": emitir(ana.usuario_id, clave, ahora, DURACION + 1)[0],
        "caducada": emitir(ana.usuario_id, clave, ahora - DURACION, DURACION)[0],
        "basura": "x" * 200,
    }
    with ClientePrueba(app_pruebas) as otro:
        for caso, alterado in alterados.items():
            with _consultas(app_pruebas) as sentencias:
                respuesta = otro.get("/api/cuenta", headers=con_cookie(alterado))
            assert respuesta.status_code == 401, caso
            assert respuesta.json() == SESION_REQUERIDA, caso
            assert es_borrado(respuesta), caso
            assert sentencias == [], caso  # RNF-03: sin consultar la base

        sin_cookie = otro.get("/api/cuenta")
        assert sin_cookie.status_code == 401 and es_borrado(sin_cookie)

        # Una firma válida de un usuario que no existe sí consulta la base, y da el mismo 401.
        inexistente = emitir(2**62, clave, ahora, DURACION)[0]
        respuesta = otro.get("/api/cuenta", headers=con_cookie(inexistente))
        assert respuesta.status_code == 401 and respuesta.json() == SESION_REQUERIDA
        # Y la cookie original sigue sirviendo.
        assert otro.get("/api/cuenta", headers=con_cookie(valor)).status_code == 200


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_caducidad_absoluta_con_el_reloj(nueva_cuenta: Callable[..., CuentaPrueba], reloj: Any) -> None:
    ahora = int(time.time())
    reloj.fijar_ahora(ahora)
    ana = nueva_cuenta("ana@example.com")
    reloj.fijar_ahora(ahora + DURACION - 1)
    assert ana.cliente.get("/api/cuenta").status_code == 200
    reloj.fijar_ahora(ahora + DURACION)
    caducada = ana.cliente.get("/api/cuenta")
    assert caducada.status_code == 401 and caducada.json() == SESION_REQUERIDA
    assert es_borrado(caducada)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cierre_de_sesion(nueva_cuenta: Callable[..., CuentaPrueba], app_pruebas: FastAPI) -> None:
    ana = nueva_cuenta("ana@example.com")
    cierre = ana.cliente.delete("/api/sesion")
    assert cierre.status_code == 204 and cierre.content == b"" and es_borrado(cierre)
    assert NOMBRE_COOKIE not in ana.cliente.cookies
    assert ana.cliente.get("/api/cuenta").status_code == 401
    otra_vez = ana.cliente.delete("/api/sesion")  # idempotente, aun sin sesión
    assert otra_vez.status_code == 204 and es_borrado(otra_vez)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_origen_en_los_metodos_que_escriben(
    app_pruebas: FastAPI, nueva_cuenta: Callable[..., CuentaPrueba], cliente: ClientePrueba
) -> None:
    ana = nueva_cuenta("ana@example.com")
    valor = ana.cliente.cookies.get(NOMBRE_COOKIE)
    assert valor
    contrasena = contrasena_nueva()
    escrituras: list[tuple[str, str, Any]] = [
        ("POST", "/api/cuentas", {"correo": "beto@example.com", "contrasena": contrasena,
                                  "consentimiento": True, "version_aviso_id": 1}),
        ("POST", "/api/cuentas", {"basura": True}),  # el origen va antes que la forma
        ("POST", "/api/sesion", {"correo": "ana@example.com", "contrasena": ana.contrasena}),
        ("DELETE", "/api/sesion", None),
        ("POST", "/api/cuenta/revocacion", {"confirmo": True}),  # antes que la sesión
    ]
    portafolio = ana.cliente.post("/api/portafolios", json={"nombre": "Principal"}).json()["id"]
    escrituras += [
        ("POST", "/api/portafolios", {"nombre": "Otro"}),
        ("PATCH", f"/api/portafolios/{portafolio}", {"nombre": "Robado"}),
        ("DELETE", f"/api/portafolios/{portafolio}", {"confirmacion": "Principal"}),
        ("POST", "/api/intermediarios", {"nombre": "Casa A"}),
        ("POST", f"/api/portafolios/{portafolio}/transacciones", {"cantidad": "1"}),
    ]
    # Están todas las operaciones de OpenAPI que no son GET.
    operaciones = {
        (metodo.upper(), ruta)
        for ruta, metodos in app_pruebas.openapi()["paths"].items()
        for metodo in metodos
        if metodo != "get"
    }
    probadas = {(metodo, re.sub(r"/[0-9]+", "/{portafolio_id}", ruta)) for metodo, ruta, _ in escrituras}
    assert operaciones == probadas
    origenes_malos: list[str | None] = [
        None,
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "https://localhost:5173",
        "http://localhost:5173/",
        "null",
        "",
    ]
    with TestClient(app_pruebas, base_url=URL_BASE_PRUEBAS) as sin_origen:
        for origen in origenes_malos:
            cabeceras = {**con_cookie(valor), **({} if origen is None else {"Origin": origen})}
            for metodo, ruta, cuerpo in escrituras:
                respuesta = sin_origen.request(metodo, ruta, json=cuerpo, headers=cabeceras)
                assert respuesta.status_code == 403, (origen, metodo, ruta)
                assert respuesta.json() == ORIGEN_NO_PERMITIDO
                assert "set-cookie" not in respuesta.headers
        # Dos encabezados Origin, aunque uno sea el permitido.
        doble = sin_origen.post(
            "/api/sesion",
            json={"correo": "ana@example.com", "contrasena": ana.contrasena},
            headers=[("Origin", ORIGEN_PRUEBAS), ("Origin", "http://localhost:5174")],
        )
        assert doble.status_code == 403
        # Los GET no exigen Origin.
        assert sin_origen.get("/api/aviso-privacidad").status_code == 200
        assert sin_origen.get("/api/cuenta", headers=con_cookie(valor)).status_code == 200

    # Nada cambió: la cuenta sigue activa, beto no existe y el portafolio sigue igual.
    assert ana.cliente.get("/api/cuenta").json()["estado"] == "activa"
    assert [p["nombre"] for p in ana.cliente.get("/api/portafolios").json()] == ["Principal"]
    assert ana.cliente.get("/api/intermediarios").json() == []
    assert ana.cliente.get(f"/api/portafolios/{portafolio}/transacciones").json() == []
    assert iniciar(cliente, "beto@example.com", contrasena).status_code == 401


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cors(cliente: ClientePrueba) -> None:
    previa = cliente.options(
        "/api/sesion",
        headers={
            "Origin": ORIGEN_PRUEBAS,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert previa.status_code == 200
    assert previa.headers["access-control-allow-origin"] == ORIGEN_PRUEBAS
    assert previa.headers["access-control-allow-credentials"] == "true"
    assert {m.strip() for m in previa.headers["access-control-allow-methods"].split(",")} == {
        "GET",
        "POST",
        "PATCH",
        "DELETE",
    }

    ajena = cliente.options(
        "/api/sesion",
        headers={"Origin": "http://localhost:5174", "Access-Control-Request-Method": "POST"},
    )
    assert ajena.status_code == 400 and "access-control-allow-origin" not in ajena.headers
    otro_metodo = cliente.options(
        "/api/sesion", headers={"Origin": ORIGEN_PRUEBAS, "Access-Control-Request-Method": "PUT"}
    )
    assert otro_metodo.status_code == 400  # solo GET, POST, PATCH y DELETE
    for encabezado in ("authorization", "x-otro"):
        otro_encabezado = cliente.options(
            "/api/sesion",
            headers={
                "Origin": ORIGEN_PRUEBAS,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": encabezado,
            },
        )
        assert otro_encabezado.status_code == 400, encabezado  # solo Content-Type

    simple = cliente.get("/api/aviso-privacidad")
    assert simple.headers["access-control-allow-origin"] == ORIGEN_PRUEBAS
    assert simple.headers["access-control-allow-credentials"] == "true"
    assert simple.headers["cache-control"] == "no-store"


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_security_en_openapi(app_pruebas: FastAPI) -> None:
    esquema = app_pruebas.openapi()
    assert esquema["components"]["securitySchemes"]["sesion_077"] == {
        "type": "apiKey",
        "in": "cookie",
        "name": NOMBRE_COOKIE,
    }
    vistas: set[tuple[str, str]] = set()
    for ruta, operaciones in esquema["paths"].items():
        for metodo, operacion in operaciones.items():
            clave = (metodo.upper(), ruta)
            vistas.add(clave)
            if clave in RUTAS_PUBLICAS:
                assert "security" not in operacion, clave
            else:
                assert operacion.get("security") == [{"sesion_077": []}], clave
    assert RUTAS_PUBLICAS | {("GET", "/api/cuenta"), ("POST", "/api/cuenta/revocacion")} <= vistas
    # Ninguna respuesta documentada expone el hash.
    assert "contrasena_hash" not in str(esquema)
