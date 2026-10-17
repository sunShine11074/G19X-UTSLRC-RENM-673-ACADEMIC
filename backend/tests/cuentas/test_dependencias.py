"""Dependencias `usuario_vigente*` que usan WP4 y WP5: dueño, bloqueos y cuenta bloqueada (§3.8; §6.4)."""

from __future__ import annotations

import threading
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
from app.cuentas.sesion import NOMBRE_COOKIE, emitir
from app.errores import SesionRequerida
from tests.conftest import ClientePrueba, ClusterPg, CuentaPrueba

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


# ---------------------------------------------------------------------------
# Por las rutas
# ---------------------------------------------------------------------------


def _llamadas(dependiente: Any) -> set[Callable[..., Any]]:
    """Todas las funciones de las que depende una ruta, también las indirectas."""
    llamadas: set[Callable[..., Any]] = set()
    pendientes = list(dependiente.dependencies)
    while pendientes:
        actual = pendientes.pop()
        if actual.call is not None:
            llamadas.add(actual.call)
        pendientes.extend(actual.dependencies)
    return llamadas


def test_las_rutas_que_escriben_bloquean_la_cuenta() -> None:
    """§4.2: toda ruta con sesión que no es GET usa la variante E (FOR SHARE) o R (FOR NO KEY UPDATE)."""
    from app.api import rutas_consultas, rutas_cuentas, rutas_portafolios, rutas_transacciones

    revisadas = set()
    for modulo in (rutas_cuentas, rutas_portafolios, rutas_transacciones, rutas_consultas):
        for ruta in modulo.router.routes:
            llamadas = _llamadas(ruta.dependant)
            con_sesion = llamadas & set(DEPENDENCIAS)
            for metodo in ruta.methods:
                if not con_sesion:
                    continue
                revisadas.add((metodo, ruta.path))
                if metodo == "GET":
                    assert con_sesion == {usuario_vigente}, (metodo, ruta.path)
                elif ruta.path == "/api/cuenta/revocacion":
                    assert con_sesion == {usuario_vigente_revocacion}, (metodo, ruta.path)
                else:
                    assert con_sesion == {usuario_vigente_escritura}, (metodo, ruta.path)
    escrituras = {r for r in revisadas if r[0] != "GET"}
    assert escrituras == {
        ("POST", "/api/cuenta/revocacion"),
        ("POST", "/api/intermediarios"),
        ("POST", "/api/portafolios"),
        ("PATCH", "/api/portafolios/{portafolio_id}"),
        ("DELETE", "/api/portafolios/{portafolio_id}"),
        ("POST", "/api/portafolios/{portafolio_id}/transacciones"),
    }


def test_la_revocacion_espera_a_la_escritura_que_ya_empezo(
    app_pruebas: FastAPI,
    cluster_pg: ClusterPg,
    dueno: psycopg.Connection[Any],
    nueva_cuenta: Callable[..., CuentaPrueba],
) -> None:
    """D-01; RD-23: una transacción que empezó antes de la revocación termina antes que ella.

    La compra queda detenida en el FOR UPDATE del portafolio con la cuenta ya tomada con FOR
    SHARE; la revocación (FOR NO KEY UPDATE) debe esperar a que la compra termine.
    """
    cuenta = nueva_cuenta()
    c = cuenta.cliente
    portafolio = c.post("/api/portafolios", json={"nombre": "Principal"}).json()["id"]
    casa = c.post("/api/intermediarios", json={"nombre": "Casa A"}).json()["id"]
    demoacc = next(i["id"] for i in c.get("/api/instrumentos").json() if i["clave"] == "DEMOACC")
    compra = {
        "intermediario_id": casa,
        "instrumento_id": demoacc,
        "tipo": "compra",
        "fecha_concertacion": "2026-09-15",
        "cantidad": "1",
        "precio": "100.00",
        "importe_comisiones": "0.00",
    }
    cookie = c.cookies.get(NOMBRE_COOKIE)
    eventos: list[tuple[str, int]] = []
    fallas: list[BaseException] = []
    candado = threading.Lock()

    def llamar(nombre: str, ruta: str, cuerpo: Any) -> None:
        try:
            with ClientePrueba(app_pruebas) as otro:
                respuesta = otro.post(ruta, json=cuerpo, headers={"Cookie": f"{NOMBRE_COOKIE}={cookie}"})
            with candado:
                eventos.append((nombre, respuesta.status_code))
        except BaseException as exc:  # se revisa en el hilo principal
            fallas.append(exc)

    escritura = threading.Thread(
        target=llamar, args=("transaccion", f"/api/portafolios/{portafolio}/transacciones", compra), daemon=True
    )
    revocacion = threading.Thread(target=llamar, args=("revocacion", "/api/cuenta/revocacion", {"confirmo": True}),
                                  daemon=True)
    with psycopg.connect(cluster_pg.conninfo_dueno) as bloqueo:
        bloqueo.execute("SET lock_timeout = '30s'")
        bloqueo.execute("SELECT id FROM portafolio WHERE id = %s FOR UPDATE", (portafolio,))
        try:
            escritura.start()
            limite = time.monotonic() + 30
            while time.monotonic() < limite and not fallas:
                fila = dueno.execute(
                    "SELECT count(*) FROM pg_stat_activity WHERE usename = 'app_077' AND wait_event_type = 'Lock'"
                ).fetchone()
                if fila and fila[0] >= 1:
                    break
                time.sleep(0.05)
            revocacion.start()
            revocacion.join(timeout=3)  # con FOR SHARE en la escritura, sigue esperando
            revocada_antes = not revocacion.is_alive()
        finally:
            bloqueo.rollback()
            escritura.join(timeout=60)
            revocacion.join(timeout=60)
    assert not fallas
    assert not revocada_antes, f"La revocación terminó antes que la escritura: {eventos}"
    assert sorted(eventos) == [("revocacion", 204), ("transaccion", 201)]
