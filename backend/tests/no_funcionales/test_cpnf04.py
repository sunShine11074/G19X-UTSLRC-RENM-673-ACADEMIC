"""CPNF-04: contraseñas no reversibles, con sal por cuenta, y fuera de respuestas, registros y respaldos (RNF-04).

- Dos cuentas con la misma contraseña tienen hashes distintos, Argon2id con m ≥ 19456, t ≥ 2 y p = 1.
- La contraseña no aparece en ninguna respuesta (tampoco en un 422 por contraseña corta ni
  en uno por campo extra), ni en los registros a nivel DEBUG (uvicorn, fastapi, sqlalchemy…),
  ni en un `pg_dump` del clúster temporal.
"""

from __future__ import annotations

import logging
import os
import re
import secrets
import subprocess
from typing import Any

import psycopg
import pytest
from psycopg.conninfo import conninfo_to_dict

from tests.conftest import ClientePrueba, ClusterPg

pytestmark = [pytest.mark.bd, pytest.mark.no_funcional, pytest.mark.usefixtures("bd_limpia")]

REGISTROS = ("", "uvicorn", "uvicorn.error", "uvicorn.access", "fastapi", "starlette", "sqlalchemy",
             "sqlalchemy.engine", "sqlalchemy.pool", "httpx", "app")
PATRON_HASH = re.compile(r"\$argon2id\$v=19\$m=(\d+),t=(\d+),p=(\d+)\$([A-Za-z0-9+/]+)\$([A-Za-z0-9+/]+)")


def _pg_dump(cluster: ClusterPg) -> bytes:
    datos = conninfo_to_dict(cluster.conninfo_dueno)
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
    entorno["PGPASSWORD"] = str(datos["password"])
    entorno["PGCLIENTENCODING"] = "UTF8"
    resultado = subprocess.run(
        [
            cluster.exe("pg_dump"), "-w",
            "-h", "127.0.0.1", "-p", str(cluster.puerto),
            "-U", "postgres", "-d", cluster.base,
        ],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=300,
        env=entorno,
    )
    assert resultado.returncode == 0, resultado.stderr.decode("utf-8", errors="replace")[-2000:]
    return resultado.stdout


def test_cpnf04(
    cliente: ClientePrueba,
    dueno: psycopg.Connection[Any],
    cluster_pg: ClusterPg,
    caplog: pytest.LogCaptureFixture,
) -> None:
    for nombre in REGISTROS:
        caplog.set_level(logging.DEBUG, logger=nombre)
    contrasena = secrets.token_urlsafe(18)
    corta = secrets.token_urlsafe(12)[:14]
    aviso = cliente.get("/api/aviso-privacidad").json()["id"]
    alta = {"contrasena": contrasena, "consentimiento": True, "version_aviso_id": aviso}

    cookies: list[str] = []
    for correo in ("ana@example.com", "beto@example.com"):
        assert cliente.post("/api/cuentas", json={"correo": correo, **alta}).status_code == 201
        inicio = cliente.post("/api/sesion", json={"correo": correo, "contrasena": contrasena})
        assert inicio.status_code == 200
        cookies.append(cliente.cookies["sesion_077"])
        assert cliente.get("/api/cuenta").status_code == 200

    # Rechazos que reciben la contraseña en el cuerpo.
    rechazos = [
        cliente.post("/api/cuentas", json={"correo": "carla@example.com", **alta, "contrasena": corta}),
        cliente.post("/api/cuentas", json={"correo": "carla@example.com", **alta, "extra": contrasena}),
        cliente.post("/api/cuentas", json={"correo": 5, **alta}),
        cliente.post("/api/cuentas", json={"correo": "ana@example.com", **alta}),
        cliente.post("/api/sesion", json={"correo": "ana@example.com", "contrasena": contrasena, "extra": 1}),
        cliente.post("/api/sesion", json={"correo": "ana@example.com", "contrasena": contrasena + "x"}),
        cliente.post("/api/sesion", json={"correo": ["ana@example.com"], "contrasena": contrasena}),
        cliente.post("/api/sesion", json={"correo": "ana@example.com", "contrasena": corta}),
    ]
    assert [r.status_code for r in rechazos] == [422, 422, 422, 409, 422, 401, 422, 401]
    assert cliente.post("/api/cuenta/revocacion", json={"confirmo": True}).status_code == 204

    # Hashes: Argon2id, parámetros mínimos y sal distinta por cuenta.
    hashes = [fila[0] for fila in dueno.execute("SELECT contrasena_hash FROM usuario ORDER BY id").fetchall()]
    assert len(hashes) == 2 and hashes[0] != hashes[1]
    sales = set()
    for valor in hashes:
        coincidencia = PATRON_HASH.fullmatch(valor)
        assert coincidencia, "el hash no es Argon2id v19"
        m, t, p, sal, _ = coincidencia.groups()
        assert int(m) >= 19456 and int(t) >= 2 and int(p) == 1
        sales.add(sal)
        assert contrasena not in valor
    assert len(sales) == 2

    # Respuestas.
    assert len(cliente.respuestas) >= 15
    for cuerpo in cliente.respuestas:
        for secreto in (contrasena, corta, *hashes):
            assert secreto.encode() not in cuerpo
        assert b"contrasena_hash" not in cuerpo and b'"input"' not in cuerpo

    # Registros a nivel DEBUG: hubo registros (sqlalchemy al menos) y ninguno lleva la contraseña ni la cookie.
    assert any(r.name.startswith("sqlalchemy.engine") for r in caplog.records)
    texto = caplog.text + "\n".join(str(r.args) for r in caplog.records)
    for secreto in (contrasena, corta, *cookies):
        assert secreto not in texto
    assert "SQL parameters hidden" in texto  # hide_parameters=True (RNF-04; RNF-05)

    # Respaldo de la base del clúster temporal (pg_dump de bin_dir).
    respaldo = _pg_dump(cluster_pg)
    assert b"$argon2id$" in respaldo and b"ana@example.com" in respaldo  # el respaldo sí trae las cuentas
    for secreto in (contrasena, corta):
        assert secreto.encode() not in respaldo

    # El registro del servidor del clúster temporal tampoco la tiene.
    registro_pg = cluster_pg.directorio.parent / "pg.log"
    if registro_pg.exists():
        assert contrasena.encode() not in registro_pg.read_bytes()
