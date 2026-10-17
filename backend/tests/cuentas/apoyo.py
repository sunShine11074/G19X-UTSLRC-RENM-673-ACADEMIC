"""Apoyo de las pruebas de cuentas y sesión (WP3): llamadas a E02 a E04, conteos y cookies."""

from __future__ import annotations

import http.cookies
import secrets
from typing import Any

import httpx
import psycopg
from fastapi.testclient import TestClient

NOMBRE_COOKIE = "sesion_077"
AVISO_VIGENTE_DESDE = "2026-10-16T00:00:00-06:00"  # el de 04_cargar_semillas.sql
MD5_AVISO = "b00c17f34657d28740dc9605a7323676"

CREDENCIALES_INVALIDAS = {
    "codigo": "credenciales_invalidas",
    "regla": "RF-01",
    "mensaje": "No se pudo iniciar sesión. Revisa tu correo y tu contraseña; una cuenta cuyo "
    "consentimiento se revocó ya no puede abrir sesión.",
}
SESION_REQUERIDA = {"codigo": "sesion_requerida", "regla": "RNF-03", "mensaje": "Inicia sesión para continuar."}
ORIGEN_NO_PERMITIDO = {"codigo": "origen_no_permitido", "regla": "R-12", "mensaje": "Origen no permitido."}


def contrasena_nueva() -> str:
    """Contraseña de prueba de 24 caracteres; nunca se imprime."""
    return secrets.token_urlsafe(18)


def aviso_id(cliente: TestClient) -> int:
    respuesta = cliente.get("/api/aviso-privacidad")
    assert respuesta.status_code == 200, respuesta.status_code
    return int(respuesta.json()["id"])


def registrar(
    cliente: TestClient,
    correo: Any,
    contrasena: Any,
    *,
    consentimiento: Any = True,
    version_aviso_id: Any = None,
    **extra: Any,
) -> httpx.Response:
    """POST /api/cuentas; sin `version_aviso_id`, usa el del aviso vigente."""
    cuerpo = {
        "correo": correo,
        "contrasena": contrasena,
        "consentimiento": consentimiento,
        "version_aviso_id": aviso_id(cliente) if version_aviso_id is None else version_aviso_id,
        **extra,
    }
    return cliente.post("/api/cuentas", json=cuerpo)


def iniciar(cliente: TestClient, correo: Any, contrasena: Any) -> httpx.Response:
    return cliente.post("/api/sesion", json={"correo": correo, "contrasena": contrasena})


def conteos(dueno: psycopg.Connection[Any]) -> tuple[int, int]:
    """(usuarios, consentimientos), contados por el dueño."""
    fila = dueno.execute("SELECT (SELECT count(*) FROM usuario), (SELECT count(*) FROM consentimiento)").fetchone()
    assert fila is not None
    return int(fila[0]), int(fila[1])


def morsel(respuesta: httpx.Response) -> http.cookies.Morsel[str]:
    """La cookie de sesión del Set-Cookie de la respuesta."""
    cabeceras = respuesta.headers.get_list("set-cookie")
    assert len(cabeceras) == 1, cabeceras
    cookie: http.cookies.SimpleCookie = http.cookies.SimpleCookie()
    cookie.load(cabeceras[0])
    assert NOMBRE_COOKIE in cookie
    return cookie[NOMBRE_COOKIE]


def es_borrado(respuesta: httpx.Response, segura: bool = False) -> bool:
    """True si la respuesta borra la cookie con los mismos atributos con que se pone."""
    m = morsel(respuesta)
    return (
        m.value == ""
        and m["max-age"] == "0"
        and m["path"] == "/api"
        and m["httponly"] is True
        and m["samesite"].lower() == "strict"
        and bool(m["secure"]) is segura
        and m["domain"] == ""
    )


def con_cookie(valor: str) -> dict[str, str]:
    """Encabezado Cookie explícito, para mandar un valor alterado o ajeno."""
    return {"Cookie": f"{NOMBRE_COOKIE}={valor}"}
