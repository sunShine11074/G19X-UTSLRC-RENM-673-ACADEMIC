"""Dependencias `usuario_vigente*` que usan WP4 y WP5: dueño, bloqueos y cuenta bloqueada (§3.8; §6.4)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import psycopg
import pytest
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.config import Settings
from app.cuentas import dependencias, servicio
from app.cuentas.dependencias import (
    UsuarioVigente,
    usuario_vigente,
    usuario_vigente_escritura,
    usuario_vigente_revocacion,
)
from app.cuentas.sesion import emitir
from app.errores import SesionRequerida
from tests.conftest import CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.usefixtures("bd_limpia")]

DEPENDENCIAS = (usuario_vigente, usuario_vigente_escritura, usuario_vigente_revocacion)


def _espera_bloqueo(sesion: Session, funcion: Callable[..., UsuarioVigente], *argumentos: Any) -> None:
    """La consulta de `funcion` debe chocar con un bloqueo de otra transacción (55P03)."""
    sesion.execute(text("SET LOCAL lock_timeout = '300ms'"))
    with pytest.raises(OperationalError) as info:
        funcion(*argumentos)
    assert getattr(info.value.orig, "sqlstate", None) == "55P03"
    sesion.rollback()


def test_interfaz_para_wp4_y_wp5() -> None:
    assert dependencias.UsuarioVigente is servicio.UsuarioVigente
    assert {"usuario_vigente", "usuario_vigente_escritura", "usuario_vigente_revocacion", "verificar_origen"} <= set(
        dependencias.__all__
    )


def test_dueno_y_bloqueos(
    app_pruebas: FastAPI, config_pruebas: Settings, nueva_cuenta: Callable[..., CuentaPrueba]
) -> None:
    ana = nueva_cuenta("ana@example.com")
    ahora = int(time.time())
    valor, _ = emitir(ana.usuario_id, config_pruebas.clave_sesion_bytes, ahora, 480 * 60)
    fabrica = app_pruebas.state.fabrica_sesiones
    esperado = UsuarioVigente(id=ana.usuario_id, correo="ana@example.com")

    with fabrica() as a, fabrica() as b:
        for funcion in DEPENDENCIAS:
            assert funcion(valor, a, config_pruebas, ahora) == esperado
            a.rollback()

        # Una escritura (FOR SHARE) no detiene a otra escritura ni a una lectura, pero sí a la revocación.
        assert usuario_vigente_escritura(valor, a, config_pruebas, ahora) == esperado
        assert usuario_vigente_escritura(valor, b, config_pruebas, ahora) == esperado
        b.rollback()
        assert usuario_vigente(valor, b, config_pruebas, ahora) == esperado
        b.rollback()
        _espera_bloqueo(b, usuario_vigente_revocacion, valor, b, config_pruebas, ahora)
        a.rollback()

        # La revocación (FOR NO KEY UPDATE) detiene a las escrituras, no a las lecturas.
        assert usuario_vigente_revocacion(valor, a, config_pruebas, ahora) == esperado
        _espera_bloqueo(b, usuario_vigente_escritura, valor, b, config_pruebas, ahora)
        assert usuario_vigente(valor, b, config_pruebas, ahora) == esperado
        b.rollback()
        a.rollback()

        # Al soltarse el bloqueo, la escritura pasa.
        b.execute(text("SET LOCAL lock_timeout = '300ms'"))
        assert usuario_vigente_escritura(valor, b, config_pruebas, ahora) == esperado
        b.rollback()


def test_cuenta_bloqueada_o_cookie_invalida(
    app_pruebas: FastAPI,
    config_pruebas: Settings,
    nueva_cuenta: Callable[..., CuentaPrueba],
    dueno: psycopg.Connection[Any],
) -> None:
    ana = nueva_cuenta("ana@example.com")
    ahora = int(time.time())
    valor, _ = emitir(ana.usuario_id, config_pruebas.clave_sesion_bytes, ahora, 480 * 60)
    dueno.execute("UPDATE usuario SET estado = 'bloqueada' WHERE id = %s", (ana.usuario_id,))
    with app_pruebas.state.fabrica_sesiones() as sesion:
        for funcion in DEPENDENCIAS:
            for cookie in (valor, None, valor[:-1]):
                with pytest.raises(SesionRequerida) as info:
                    funcion(cookie, sesion, config_pruebas, ahora)
                assert info.value.cabeceras is not None
                assert info.value.cabeceras["set-cookie"].startswith('sesion_077=""')
            sesion.rollback()
