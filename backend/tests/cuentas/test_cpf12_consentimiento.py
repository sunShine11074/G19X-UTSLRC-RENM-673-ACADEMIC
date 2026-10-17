"""CPF-12: aviso de privacidad, otorgamiento y revocación del consentimiento (RF-12; RD-11; RD-23; §8.3)."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Any

import psycopg
import pytest

from app.reloj import momento_iso
from tests.conftest import ClientePrueba, CuentaPrueba
from tests.cuentas.apoyo import (
    AVISO_VIGENTE_DESDE,
    CREDENCIALES_INVALIDAS,
    MD5_AVISO,
    NOMBRE_COOKIE,
    SESION_REQUERIDA,
    con_cookie,
    conteos,
    es_borrado,
    iniciar,
    registrar,
)

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]


def test_aviso_vigente_con_y_sin_sesion(
    cliente: ClientePrueba, nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    sin_sesion = cliente.get("/api/aviso-privacidad")
    assert sin_sesion.status_code == 200
    aviso = sin_sesion.json()
    assert set(aviso) == {"id", "texto", "vigente_desde"}
    assert aviso["vigente_desde"] == AVISO_VIGENTE_DESDE
    assert hashlib.md5(aviso["texto"].encode("utf-8")).hexdigest() == MD5_AVISO  # texto sin alterar
    assert "Revoca" in aviso["texto"]
    fila = dueno.execute(
        "SELECT id, md5(convert_to(texto, 'UTF8')) FROM version_aviso WHERE vigente_desde <= now() "
        "ORDER BY vigente_desde DESC LIMIT 1"
    ).fetchone()
    assert fila == (aviso["id"], MD5_AVISO)

    ana = nueva_cuenta("ana@example.com")
    con_sesion = ana.cliente.get("/api/aviso-privacidad")
    assert con_sesion.status_code == 200 and con_sesion.content == sin_sesion.content
    # Sin Origin también responde: es un GET.
    assert cliente.get("/api/aviso-privacidad", headers={"Origin": ""}).content == sin_sesion.content


def test_otorgamiento_con_medio_momento_y_version(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    antes = dueno.execute("SELECT now()").fetchone()
    ana = nueva_cuenta("ana@example.com")
    despues = dueno.execute("SELECT now()").fetchone()
    assert antes is not None and despues is not None
    filas = dueno.execute(
        "SELECT c.usuario_id, c.version_aviso_id, c.tipo, c.medio, c.momento, v.vigente_desde "
        "FROM consentimiento c JOIN version_aviso v ON v.id = c.version_aviso_id"
    ).fetchall()
    assert len(filas) == 1
    usuario_id, version, tipo, medio, momento, vigente_desde = filas[0]
    vigente = dueno.execute(
        "SELECT id FROM version_aviso WHERE vigente_desde <= now() ORDER BY vigente_desde DESC LIMIT 1"
    ).fetchone()
    assert (usuario_id, tipo, medio) == (ana.usuario_id, "otorgamiento", "web")
    assert vigente is not None and version == vigente[0]
    assert antes[0] <= momento <= despues[0]

    cuenta = ana.cliente.get("/api/cuenta")
    assert cuenta.status_code == 200
    assert cuenta.json() == {
        "correo": "ana@example.com",
        "estado": "activa",
        "consentimientos": [
            {
                "tipo": "otorgamiento",
                "momento": momento_iso(momento),
                "medio": "web",
                "version_aviso_id": version,
                "aviso_vigente_desde": momento_iso(vigente_desde),
            }
        ],
    }


def test_revocacion_bloquea_la_cuenta(
    cliente: ClientePrueba, nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    ana = nueva_cuenta("ana@example.com")
    beto = nueva_cuenta("beto@example.com")
    cookie_anterior = ana.cliente.cookies.get(NOMBRE_COOKIE)
    assert cookie_anterior

    # Confirmación inválida: 422 sin cambios.
    for cuerpo, codigo in (
        ({"confirmo": False}, "confirmacion_invalida"),
        ({}, "datos_invalidos"),
        ({"confirmo": "true"}, "datos_invalidos"),
        ({"confirmo": 1}, "datos_invalidos"),
    ):
        respuesta = ana.cliente.post("/api/cuenta/revocacion", json=cuerpo)
        assert respuesta.status_code == 422, cuerpo
        assert respuesta.json()["codigo"] == codigo, cuerpo
    falso = ana.cliente.post("/api/cuenta/revocacion", json={"confirmo": False})
    assert falso.json() == {"codigo": "confirmacion_invalida", "regla": "RF-12", "mensaje": "Confirma la revocación."}
    assert conteos(dueno) == (2, 2)
    assert ana.cliente.get("/api/cuenta").status_code == 200

    revocada = ana.cliente.post("/api/cuenta/revocacion", json={"confirmo": True})
    assert revocada.status_code == 204 and revocada.content == b""
    assert es_borrado(revocada)
    assert NOMBRE_COOKIE not in ana.cliente.cookies

    filas = dueno.execute(
        "SELECT tipo, medio, version_aviso_id FROM consentimiento WHERE usuario_id = %s ORDER BY momento, id",
        (ana.usuario_id,),
    ).fetchall()
    vigente = dueno.execute(
        "SELECT id FROM version_aviso WHERE vigente_desde <= now() ORDER BY vigente_desde DESC LIMIT 1"
    ).fetchone()
    assert vigente is not None
    assert filas == [("otorgamiento", "web", vigente[0]), ("revocacion", "web", vigente[0])]
    estados = dict(dueno.execute("SELECT id, estado FROM usuario").fetchall())
    assert estados == {ana.usuario_id: "bloqueada", beto.usuario_id: "activa"}

    # La cookie anterior ya no sirve, ni para leer ni para revocar otra vez.
    with ClientePrueba(cliente.app) as otro:  # type: ignore[arg-type]
        intentos = (("GET", "/api/cuenta", None), ("POST", "/api/cuenta/revocacion", {"confirmo": True}))
        for metodo, ruta, cuerpo in intentos:
            respuesta = otro.request(metodo, ruta, json=cuerpo, headers=con_cookie(cookie_anterior))
            assert respuesta.status_code == 401, ruta
            assert respuesta.json() == SESION_REQUERIDA
            assert es_borrado(respuesta)
    assert conteos(dueno) == (2, 3)

    # El inicio de sesión da el 401 genérico, y el correo no se puede volver a registrar.
    inicio = iniciar(cliente, "ana@example.com", ana.contrasena)
    assert inicio.status_code == 401 and inicio.json() == CREDENCIALES_INVALIDAS
    assert inicio.content == iniciar(cliente, "nadie@example.com", ana.contrasena).content
    repetido = registrar(cliente, " ANA@example.com", ana.contrasena)
    assert repetido.status_code == 409 and repetido.json()["codigo"] == "correo_registrado"

    # La otra cuenta no se ve afectada.
    assert beto.cliente.get("/api/cuenta").status_code == 200
    assert conteos(dueno) == (2, 3)
