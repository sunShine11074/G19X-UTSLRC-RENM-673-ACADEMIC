"""Infraestructura de las pruebas (§8.1).

Levanta un clúster temporal de PostgreSQL 18 con 02, 03 y 04, y da la configuración, la
aplicación, los clientes, las cuentas, la limpieza, el reloj y el bloqueo de red que usan
todos los paquetes. Nunca se conecta al clúster de desarrollo (5432) ni lee backend/.env.
Las contraseñas del clúster temporal salen de `secrets` y nunca se imprimen.

Variables de entorno opcionales:
- P077_PG_BIN: carpeta de los binarios de PostgreSQL 18.
- P077_PG_PUERTO: puerto del clúster temporal (si no, uno libre).
- P077_PG_LOCALE: configuración regional de initdb (por omisión es-MX; «C.UTF-8» usa el
  proveedor builtin).
"""

from __future__ import annotations

import atexit
import os
import re
import secrets
import shutil
import socket
import subprocess
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import ExitStack
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from psycopg import sql
from psycopg.conninfo import make_conninfo

from app.config import Settings
from app.reloj import ahora_epoch, hoy_cdmx

RUTA_PRUEBAS = Path(__file__).resolve().parent
RUTA_BACKEND = RUTA_PRUEBAS.parent
BIN_POR_OMISION = Path("C:/Program Files/PostgreSQL/18/bin")
BASE_PRUEBAS = "proyecto077_pruebas"
ROL_APP = "app_077"
ORIGEN_PRUEBAS = "http://localhost:5173"
URL_BASE_PRUEBAS = "http://localhost:8000"
LOCALE_POR_OMISION = "es-MX"
SCRIPTS_SQL = ("02_crear_esquema.sql", "03_probar_esquema.sql", "04_cargar_semillas.sql")
TABLAS_DE_CUENTA = ("transaccion", "portafolio", "intermediario", "consentimiento", "usuario")

# 5432: clúster de desarrollo de Ramon; 55432: el del orquestador; 50000-50059: reservados.
PUERTOS_PROHIBIDOS = frozenset({5432, 55432, *range(50000, 50060)})


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--registro-resultados",
        action="store_true",
        default=False,
        help="Guarda la evidencia en tests/resultados/AAAA-MM-DD/ (D-32).",
    )


# ---------------------------------------------------------------------------
# Clúster temporal
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClusterPg:
    """Datos del clúster temporal. Las cadenas con contraseña no salen en el repr."""

    bin_dir: Path
    puerto: int
    base: str
    url_app: str = field(repr=False)  # app_077, para Settings.database_url
    conninfo_dueno: str = field(repr=False)  # postgres, para psycopg
    salida_03: str = field(repr=False)  # salida de 03_probar_esquema.sql
    directorio: Path  # carpeta de datos (data_directory)

    def exe(self, nombre: str) -> str:
        """Ruta de un binario de PostgreSQL (pg_dump, psql…)."""
        return _exe(self.bin_dir, nombre)


def _exe(bin_dir: Path, nombre: str) -> str:
    ruta = shutil.which(nombre, path=str(bin_dir))
    if ruta is None:
        raise FileNotFoundError(f"No está {nombre} en {bin_dir}")
    return ruta


def _entorno(contrasena: str | None = None) -> dict[str, str]:
    """Entorno de los subprocesos: sin variables PG* heredadas (nada de PGHOST ni PGPORT)."""
    entorno = {k: v for k, v in os.environ.items() if not k.upper().startswith("PG")}
    entorno["PGCLIENTENCODING"] = "UTF8"
    if contrasena is not None:
        entorno["PGPASSWORD"] = contrasena
    return entorno


def _buscar_binarios() -> Path:
    candidatos: list[Path] = []
    if os.environ.get("P077_PG_BIN"):
        candidatos.append(Path(os.environ["P077_PG_BIN"]))
    pg_ctl = shutil.which("pg_ctl")
    if pg_ctl:
        candidatos.append(Path(pg_ctl).parent)
    candidatos.append(BIN_POR_OMISION)
    revisados: list[str] = []
    for directorio in candidatos:
        if not all(shutil.which(n, path=str(directorio)) for n in ("initdb", "pg_ctl", "psql")):
            revisados.append(f"{directorio}: faltan initdb, pg_ctl o psql")
            continue
        version = subprocess.run(
            [_exe(directorio, "pg_ctl"), "--version"],
            capture_output=True,
            text=True,
            timeout=60,
            stdin=subprocess.DEVNULL,
            env=_entorno(),
        ).stdout.strip()
        if re.search(r"\(PostgreSQL\) 18\b", version):
            return directorio
        revisados.append(f"{directorio}: {version or 'sin versión'}")
    pytest.fail(
        "No se encontraron los binarios de PostgreSQL 18 (initdb, pg_ctl y psql). Define P077_PG_BIN "
        "o instala PostgreSQL 18. Revisados: " + "; ".join(revisados),
        pytrace=False,
    )


def _puerto_permitido(puerto: int) -> bool:
    return 1024 <= puerto <= 65535 and puerto not in PUERTOS_PROHIBIDOS


def _elegir_puerto() -> int:
    if os.environ.get("P077_PG_PUERTO"):
        puerto = int(os.environ["P077_PG_PUERTO"])
        if not _puerto_permitido(puerto):
            pytest.fail(f"P077_PG_PUERTO={puerto} no está permitido (5432, 55432 y 50000-50059 no).", pytrace=False)
        return puerto
    for _ in range(50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            puerto = s.getsockname()[1]
        if _puerto_permitido(puerto):
            return puerto
    pytest.fail("No se encontró un puerto libre para el clúster temporal.", pytrace=False)


def _argumentos_locale() -> list[str]:
    locale = os.environ.get("P077_PG_LOCALE", LOCALE_POR_OMISION)
    if locale.upper() in ("C.UTF-8", "C.UTF8", "BUILTIN"):
        return ["--locale=C", "--locale-provider=builtin", "--builtin-locale=C.UTF-8"]
    return [f"--locale={locale}"]


def _texto(datos: bytes | None) -> str:
    return (datos or b"").decode("utf-8", errors="replace")


class _Parada:
    """Detiene el clúster y borra su carpeta una sola vez (finalizer y atexit)."""

    def __init__(self, pg_ctl: str, datos: Path, raiz: Path) -> None:
        self.pg_ctl = pg_ctl
        self.datos = datos
        self.raiz = raiz
        self.hecha = False
        self.candado = threading.Lock()

    def __call__(self, borrar: bool = True) -> None:
        with self.candado:
            if self.hecha:
                return
            self.hecha = True
        if (self.datos / "postmaster.pid").exists():
            subprocess.run(
                [self.pg_ctl, "-D", str(self.datos), "stop", "-m", "immediate", "-w", "-t", "60"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=120,
                env=_entorno(),
            )
        if borrar:
            for _ in range(10):
                shutil.rmtree(self.raiz, ignore_errors=True)
                if not self.raiz.exists():
                    break
                time.sleep(0.5)


def _ejecutar_script(bin_dir: Path, puerto: int, clave: str, script: Path) -> str:
    resultado = subprocess.run(
        [
            _exe(bin_dir, "psql"),
            "-X", "-q", "-w",
            "-h", "127.0.0.1",
            "-p", str(puerto),
            "-U", "postgres",
            "-d", BASE_PRUEBAS,
            "-v", "ON_ERROR_STOP=1",
            "-f", str(script),
        ],
        capture_output=True,
        stdin=subprocess.DEVNULL,
        timeout=600,
        env=_entorno(clave),
        cwd=str(RUTA_BACKEND),
    )
    salida = _texto(resultado.stdout) + _texto(resultado.stderr)
    if resultado.returncode != 0:
        cola = "\n".join(salida.splitlines()[-15:])
        raise RuntimeError(f"{script.name} falló con el código {resultado.returncode}:\n{cola}")
    return salida


@pytest.fixture(scope="session")
def cluster_pg(tmp_path_factory: pytest.TempPathFactory) -> Iterator[ClusterPg]:
    """Clúster temporal de PostgreSQL 18 con 02, 03 y 04; nunca el 5432."""
    bin_dir = _buscar_binarios()
    raiz = tmp_path_factory.mktemp("pg077")
    datos = raiz / "datos"
    clave_dueno = secrets.token_urlsafe(24)
    clave_app = secrets.token_urlsafe(24)

    archivo_clave = raiz / "clave_dueno.txt"
    archivo_clave.write_text(clave_dueno, encoding="utf-8")
    try:
        initdb = subprocess.run(
            [
                _exe(bin_dir, "initdb"),
                "-D", str(datos),
                "-U", "postgres",
                "--encoding=UTF8",
                *_argumentos_locale(),
                "--auth=scram-sha-256",
                f"--pwfile={archivo_clave}",
                "--no-sync",
            ],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=300,
            env=_entorno(),
        )
    finally:
        archivo_clave.unlink(missing_ok=True)
    if initdb.returncode != 0:
        pytest.fail(f"initdb falló:\n{_texto(initdb.stdout)}{_texto(initdb.stderr)}", pytrace=False)

    pg_ctl = _exe(bin_dir, "pg_ctl")
    parada = _Parada(pg_ctl, datos, raiz)
    atexit.register(parada)
    try:
        # Otro proceso puede tomar el puerto libre antes que el servidor: se reintenta con otro.
        intentos = 1 if os.environ.get("P077_PG_PUERTO") else 3
        for _ in range(intentos):
            puerto = _elegir_puerto()
            opciones = (
                f"-p {puerto} -c listen_addresses=127.0.0.1 -c lc_messages=C "
                "-c fsync=off -c synchronous_commit=off -c full_page_writes=off"
            )
            # En Windows, pg_ctl hereda sus manejadores al servidor: la salida va a un archivo, no a una tubería.
            with open(raiz / "pg_ctl.out", "ab") as salida_pg_ctl:
                inicio = subprocess.run(
                    [pg_ctl, "-D", str(datos), "-l", str(raiz / "pg.log"), "-w", "-t", "60", "-o", opciones, "start"],
                    stdin=subprocess.DEVNULL,
                    stdout=salida_pg_ctl,
                    stderr=subprocess.STDOUT,
                    timeout=120,
                    env=_entorno(),
                )
            if inicio.returncode == 0:
                break
        else:
            raise RuntimeError(
                f"pg_ctl start falló (código {inicio.returncode}); revisa {raiz / 'pg.log'} y {raiz / 'pg_ctl.out'}."
            )

        conninfo_postgres = make_conninfo(
            host="127.0.0.1", port=puerto, dbname="postgres", user="postgres", password=clave_dueno,
            connect_timeout=10,
        )
        with psycopg.connect(conninfo_postgres, autocommit=True) as conexion:
            conexion.execute(
                sql.SQL("CREATE ROLE {} LOGIN PASSWORD {}").format(sql.Identifier(ROL_APP), sql.Literal(clave_app))
            )
            conexion.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(BASE_PRUEBAS)))
            conexion.execute(
                sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                    sql.Identifier(BASE_PRUEBAS), sql.Identifier(ROL_APP)
                )
            )

        # 03 antes de 04: exige las tablas vacías.
        salidas = {
            nombre: _ejecutar_script(bin_dir, puerto, clave_dueno, RUTA_BACKEND / nombre) for nombre in SCRIPTS_SQL
        }
    except BaseException:
        parada(borrar=False)  # se conserva pg.log para revisar qué pasó
        raise

    cluster = ClusterPg(
        bin_dir=bin_dir,
        puerto=puerto,
        base=BASE_PRUEBAS,
        url_app=f"postgresql+psycopg://{ROL_APP}:{clave_app}@127.0.0.1:{puerto}/{BASE_PRUEBAS}",
        conninfo_dueno=make_conninfo(
            host="127.0.0.1", port=puerto, dbname=BASE_PRUEBAS, user="postgres", password=clave_dueno,
            connect_timeout=10,
        ),
        salida_03=salidas["03_probar_esquema.sql"],
        directorio=datos,
    )
    try:
        yield cluster
    finally:
        parada()


# ---------------------------------------------------------------------------
# Configuración, aplicación y base
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def config_pruebas(cluster_pg: ClusterPg) -> Settings:
    """Settings del clúster temporal; nunca lee backend/.env."""
    return Settings(
        _env_file=None,  # type: ignore[call-arg]
        database_url=cluster_pg.url_app,  # type: ignore[arg-type]
        sesion_clave=secrets.token_urlsafe(32),  # type: ignore[arg-type]
        cors_origins=ORIGEN_PRUEBAS,
        sesion_duracion_minutos=480,
        sesion_cookie_segura=False,
    )


@pytest.fixture(scope="session")
def app_pruebas(config_pruebas: Settings) -> Iterator[FastAPI]:
    from app.main import crear_app

    app = crear_app(config_pruebas)
    try:
        yield app
    finally:
        app.state.engine.dispose()


@pytest.fixture
def dueno(cluster_pg: ClusterPg) -> Iterator[psycopg.Connection[Any]]:
    """Conexión de postgres en autocommit, solo para inspeccionar y limpiar."""
    with psycopg.connect(cluster_pg.conninfo_dueno, autocommit=True) as conexion:
        yield conexion


def _misma_ruta(a: str | Path, b: str | Path) -> bool:
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


@pytest.fixture
def bd_limpia(cluster_pg: ClusterPg, dueno: psycopg.Connection[Any]) -> None:
    """Vacía las tablas de cuenta (las semillas no se tocan) tras comprobar que es el clúster temporal."""
    fila = dueno.execute(
        "SELECT current_database(), inet_server_port(), current_setting('data_directory')"
    ).fetchone()
    assert fila is not None
    base, puerto, directorio = fila
    if (
        base != BASE_PRUEBAS
        or puerto != cluster_pg.puerto
        or puerto in PUERTOS_PROHIBIDOS
        or not _misma_ruta(directorio, cluster_pg.directorio)
    ):
        pytest.exit("bd_limpia: la conexión no es la del clúster temporal; no se limpió nada.", returncode=3)
    dueno.execute("SET lock_timeout = '15s'")
    dueno.execute(f"TRUNCATE {', '.join(TABLAS_DE_CUENTA)} RESTART IDENTITY")


# ---------------------------------------------------------------------------
# Clientes y cuentas
# ---------------------------------------------------------------------------


class ClientePrueba(TestClient):
    """TestClient con Origin permitido que guarda el cuerpo de cada respuesta en `respuestas` (CPNF-04)."""

    def __init__(self, app: FastAPI) -> None:
        super().__init__(app, base_url=URL_BASE_PRUEBAS, headers={"Origin": ORIGEN_PRUEBAS})
        self.respuestas: list[bytes] = []
        self.event_hooks = {"request": [], "response": [self._guardar]}

    def _guardar(self, respuesta: httpx.Response) -> None:
        respuesta.read()
        self.respuestas.append(respuesta.content)


@pytest.fixture
def cliente(app_pruebas: FastAPI) -> Iterator[ClientePrueba]:
    with ClientePrueba(app_pruebas) as c:
        yield c


@dataclass(frozen=True)
class CuentaPrueba:
    cliente: ClientePrueba  # con su propio frasco de cookies y la sesión abierta
    correo: str
    contrasena: str = field(repr=False)
    usuario_id: int


@pytest.fixture
def nueva_cuenta(
    app_pruebas: FastAPI, dueno: psycopg.Connection[Any]
) -> Iterator[Callable[..., CuentaPrueba]]:
    """Fábrica `nueva_cuenta(correo=None)`: registra (E02, E03) e inicia sesión (E04)."""
    with ExitStack() as pila:

        def crear(correo: str | None = None) -> CuentaPrueba:
            correo = correo if correo is not None else f"cuenta.{secrets.token_hex(4)}@example.com"
            contrasena = secrets.token_urlsafe(18)
            c = pila.enter_context(ClientePrueba(app_pruebas))
            aviso = c.get("/api/aviso-privacidad")
            assert aviso.status_code == 200, f"E02 respondió {aviso.status_code}"
            alta = c.post(
                "/api/cuentas",
                json={
                    "correo": correo,
                    "contrasena": contrasena,
                    "consentimiento": True,
                    "version_aviso_id": aviso.json()["id"],
                },
            )
            assert alta.status_code == 201, f"E03 respondió {alta.status_code} ({alta.json().get('codigo')})"
            inicio = c.post("/api/sesion", json={"correo": correo, "contrasena": contrasena})
            assert inicio.status_code == 200, f"E04 respondió {inicio.status_code} ({inicio.json().get('codigo')})"
            fila = dueno.execute(
                "SELECT id FROM usuario WHERE lower(btrim(correo)) = lower(btrim(%s))", (correo,)
            ).fetchone()
            assert fila is not None
            return CuentaPrueba(cliente=c, correo=correo, contrasena=contrasena, usuario_id=fila[0])

        yield crear


# ---------------------------------------------------------------------------
# Reloj y red
# ---------------------------------------------------------------------------

_AUSENTE = object()


class RelojPrueba:
    """Sustituye hoy_cdmx y ahora_epoch en `app.dependency_overrides`; se restaura al final."""

    def __init__(self, app: FastAPI) -> None:
        self._app = app
        self._previos: dict[Callable[..., Any], Any] = {}

    def _fijar(self, dependencia: Callable[..., Any], sustituto: Callable[[], Any]) -> None:
        if dependencia not in self._previos:
            self._previos[dependencia] = self._app.dependency_overrides.get(dependencia, _AUSENTE)
        self._app.dependency_overrides[dependencia] = sustituto

    def fijar_hoy(self, dia: date) -> None:
        self._fijar(hoy_cdmx, lambda: dia)

    def fijar_ahora(self, epoch: int) -> None:
        self._fijar(ahora_epoch, lambda: epoch)

    def restaurar(self) -> None:
        for dependencia, previo in self._previos.items():
            if previo is _AUSENTE:
                self._app.dependency_overrides.pop(dependencia, None)
            else:
                self._app.dependency_overrides[dependencia] = previo
        self._previos.clear()


@pytest.fixture
def reloj(app_pruebas: FastAPI) -> Iterator[RelojPrueba]:
    sustituto = RelojPrueba(app_pruebas)
    try:
        yield sustituto
    finally:
        sustituto.restaurar()


class RedBloqueada(OSError):
    """Intento de conexión de red durante una prueba con `sin_red` (RNF-08)."""


@pytest.fixture
def sin_red(cluster_pg: ClusterPg, monkeypatch: pytest.MonkeyPatch) -> None:
    """Solo permite conexiones a 127.0.0.1:puerto del clúster temporal y resolver nombres locales.

    Los pares de sockets que el bucle de eventos crea con `socket.socketpair` siguen
    funcionando (en Windows se conectan por 127.0.0.1). libpq no usa el módulo socket.
    """
    permitido = ("127.0.0.1", cluster_pg.puerto)
    nombres_locales = {"127.0.0.1", "localhost", "::1"}
    connect_original = socket.socket.connect
    connect_ex_original = socket.socket.connect_ex
    socketpair_original = socket.socketpair
    getaddrinfo_original = socket.getaddrinfo
    local = threading.local()

    def _revisar(direccion: Any) -> None:
        if getattr(local, "en_socketpair", False):
            return
        if isinstance(direccion, tuple) and len(direccion) >= 2 and (direccion[0], direccion[1]) == permitido:
            return
        raise RedBloqueada(f"Conexión de red bloqueada en la prueba (RNF-08): {direccion!r}")

    def connect(self: socket.socket, direccion: Any) -> None:
        _revisar(direccion)
        return connect_original(self, direccion)

    def connect_ex(self: socket.socket, direccion: Any) -> int:
        _revisar(direccion)
        return connect_ex_original(self, direccion)

    def socketpair(*args: Any, **kwargs: Any) -> tuple[socket.socket, socket.socket]:
        local.en_socketpair = True
        try:
            return socketpair_original(*args, **kwargs)
        finally:
            local.en_socketpair = False

    def getaddrinfo(host: Any, *args: Any, **kwargs: Any) -> Any:
        nombre = host.decode() if isinstance(host, bytes) else host
        if nombre is not None and nombre not in nombres_locales and not getattr(local, "en_socketpair", False):
            raise RedBloqueada(f"Resolución de nombres bloqueada en la prueba (RNF-08): {nombre!r}")
        return getaddrinfo_original(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "socketpair", socketpair)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def ruta_oraculo() -> Path:
    """Carpeta del oráculo congelado (solo se leen entradas/ y esperados/)."""
    return RUTA_PRUEBAS / "oraculo"


@pytest.fixture(scope="session")
def carpeta_resultados(request: pytest.FixtureRequest, tmp_path_factory: pytest.TempPathFactory) -> Path:
    """tests/resultados/AAAA-MM-DD/ con --registro-resultados; si no, una carpeta temporal."""
    if request.config.getoption("--registro-resultados"):
        carpeta = RUTA_PRUEBAS / "resultados" / hoy_cdmx().isoformat()
        carpeta.mkdir(parents=True, exist_ok=True)
        return carpeta
    return tmp_path_factory.mktemp("resultados")
