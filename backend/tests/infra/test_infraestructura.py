"""Pruebas de la base e infraestructura (WP1; §9 «Terminado cuando»; §8.1)."""

from __future__ import annotations

import logging
import os
import re
import secrets
import socket
import subprocess
import sys
from collections.abc import Iterator
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from typing import Any

import psycopg
import pytest
from fastapi import Depends, FastAPI, Request, Response
from fastapi.testclient import TestClient
from psycopg.conninfo import conninfo_to_dict
from pydantic import BaseModel, SecretStr, StrictBool, ValidationError
from sqlalchemy import Engine, delete, insert, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.api.comunes import fuente_vista, instrumento_vista
from app.api.tipos import (
    FechaEstricta,
    Identificador,
    IdRuta,
    Importe,
    ModeloEntrada,
    Nombre,
    Precio,
    TipoTransaccion,
    Titulos,
    como_texto,
)
from app.config import Settings, config_actual
from app.datos.integridad import traducir
from app.datos.modelos import (
    MODELOS,
    Consentimiento,
    Instrumento,
    Intermediario,
    Portafolio,
    Transaccion,
    Usuario,
    VersionAviso,
)
from app.datos.registros import FuenteRegistro, InstrumentoRegistro
from app.db import crear_fabrica, crear_motor_bd, obtener_sesion
from app.errores import (
    ConfirmacionInvalida,
    DatosInvalidos,
    ErrorCampo,
    ErrorDominio,
    FechaFueraDeIntervalo,
    NoEncontrado,
    PeriodoFueraDeIntervalo,
    SaldoNegativo,
    SesionRequerida,
    errores_de_validacion,
    importar_si_existe,
    sobre,
)
from app.main import crear_app
from app.reloj import ahora_epoch, epoch_iso, hoy_cdmx, momento_iso
from tests.conftest import (
    PUERTOS_PROHIBIDOS,
    RUTA_BACKEND,
    ClientePrueba,
    ClusterPg,
    RedBloqueada,
)


def _config(**cambios: Any) -> Settings:
    valores: dict[str, Any] = {
        "database_url": "postgresql+psycopg://app_077:x@127.0.0.1:1/nada",
        "sesion_clave": secrets.token_urlsafe(32),
    }
    valores.update(cambios)
    return Settings(_env_file=None, **valores)  # type: ignore[call-arg]


def _url_dueno(cluster: ClusterPg) -> str:
    datos = conninfo_to_dict(cluster.conninfo_dueno)
    return f"postgresql+psycopg://postgres:{datos['password']}@127.0.0.1:{cluster.puerto}/{cluster.base}"


# ---------------------------------------------------------------------------
# Sin base de datos
# ---------------------------------------------------------------------------


def test_importar_main_no_construye_settings() -> None:
    """`import app.main` no construye Settings (y por eso no lee backend/.env); `app` está en dir()."""
    codigo = (
        "import app.config as c\n"
        "def _prohibido(*a, **k):\n"
        "    raise SystemExit('Settings se construyó al importar app.main')\n"
        "c.Settings.__init__ = _prohibido\n"
        "import app.main as m\n"
        "assert 'app' in dir(m), 'app no está en dir(app.main)'\n"
        "assert m._app is None\n"
        "print('ok')\n"
    )
    entorno = {k: v for k, v in os.environ.items() if k not in ("DATABASE_URL", "SESION_CLAVE")}
    resultado = subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=str(RUTA_BACKEND),
        capture_output=True,
        text=True,
        timeout=120,
        env=entorno,
        stdin=subprocess.DEVNULL,
    )
    assert resultado.returncode == 0, resultado.stderr[-2000:]
    assert resultado.stdout.strip().endswith("ok")


def test_app_perezosa_se_crea_una_sola_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.main as principal

    centinela = object()
    creadas: list[object] = []

    def crear_falsa(config: object = None) -> FastAPI:
        creadas.append(config)
        return FastAPI()

    monkeypatch.setattr(principal, "_app", None)
    monkeypatch.setattr(principal, "crear_app", crear_falsa)
    monkeypatch.setattr(principal, "cargar_config", lambda: centinela)
    primera = principal.app
    assert isinstance(primera, FastAPI)
    assert principal.app is primera
    assert creadas == [centinela]
    assert "app" in dir(principal)
    with pytest.raises(AttributeError):
        principal.no_existe  # noqa: B018


def test_settings_valida_sin_repetir_secretos(monkeypatch: pytest.MonkeyPatch) -> None:
    clave_corta = "corta-" + secrets.token_hex(4)
    with pytest.raises(ValidationError) as info:
        _config(sesion_clave=clave_corta)
    assert "al menos 32 caracteres" in str(info.value)
    assert clave_corta not in str(info.value)

    for origenes in ("*", "http://localhost:5173/", "http://localhost:5173/ruta", "localhost:5173", ""):
        with pytest.raises(ValidationError):
            _config(cors_origins=origenes)
    for minutos in (4, 1441):
        with pytest.raises(ValidationError):
            _config(sesion_duracion_minutos=minutos)

    monkeypatch.delenv("SESION_CLAVE", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)  # type: ignore[call-arg]

    clave = secrets.token_urlsafe(32)
    config = _config(sesion_clave=clave, cors_origins="http://localhost:5173, https://ejemplo.mx:8443")
    assert config.lista_origenes == ["http://localhost:5173", "https://ejemplo.mx:8443"]
    assert config.clave_sesion_bytes == clave.encode("utf-8")
    assert config.sesion_duracion_minutos == 480 and config.sesion_cookie_segura is False
    assert clave not in repr(config) and "app_077:x@" not in repr(config)


def test_modelos_insertan_sin_id_ni_momentos() -> None:
    dialecto = postgresql.dialect()
    momentos = {"momento", "registrada_en", "incorporada_en", "valores_sustituidos"}
    assert len(MODELOS) == 13
    for modelo in MODELOS:
        tabla = modelo.__table__
        columnas = [c for c in tabla.columns if c.identity is None and c.server_default is None]
        sentencia = str(insert(modelo).values({c.name: None for c in columnas}).compile(dialect=dialecto))
        lista = sentencia.split("(", 1)[1].split(")", 1)[0]
        insertadas = {c.strip() for c in lista.split(",")}
        assert insertadas == {c.name for c in columnas}, tabla.name
        assert not insertadas & momentos, tabla.name
        if tabla.name != "emision_cetes":  # su llave es el instrumento, sin identidad
            assert "id" not in insertadas, tabla.name
            assert tabla.c.id.identity is not None and tabla.c.id.identity.always
    assert Transaccion.__table__.c.cantidad.type.__class__.__name__ == "Integer"


def test_bloqueo_del_portafolio_lleva_of() -> None:
    sentencia = select(Portafolio).where(Portafolio.id == 1).with_for_update(of=Portafolio)
    assert "FOR UPDATE OF portafolio" in str(sentencia.compile(dialect=postgresql.dialect()))


class _CuerpoCifras(BaseModel):
    precio: Precio | None = None
    importe: Importe | None = None
    titulos: Titulos | None = None
    fecha: FechaEstricta | None = None
    nombre: Nombre | None = None
    tipo: TipoTransaccion | None = None
    ident: Identificador | None = None


def _mensaje(**campos: Any) -> tuple[str, str]:
    with pytest.raises(ValidationError) as info:
        _CuerpoCifras(**campos)
    error = info.value.errors()[0]
    campo = errores_de_validacion([error])[0]
    return campo.mensaje, campo.regla


def test_cifras_sin_redondear() -> None:
    assert como_texto(_CuerpoCifras(precio="50.00").precio) == "50.00"  # type: ignore[arg-type]
    assert como_texto(_CuerpoCifras(precio="1.1234567").precio) == "1.1234567"  # type: ignore[arg-type]
    assert como_texto(_CuerpoCifras(precio="1.12345670").precio) == "1.12345670"  # type: ignore[arg-type]
    assert como_texto(_CuerpoCifras(importe="0").importe) == "0"  # type: ignore[arg-type]
    assert como_texto(_CuerpoCifras(importe="14.50").importe) == "14.50"  # type: ignore[arg-type]
    assert como_texto(Decimal("1E+2")) == "100"

    assert _mensaje(precio=50) == ('Envía esta cifra como texto, por ejemplo "50.00".', "RD-12")
    assert _mensaje(precio=50.5) == ('Envía esta cifra como texto, por ejemplo "50.00".', "RD-12")
    for texto in ("1e5", "1,000.00", "+1", " 1", "01", "1.", ".5", "-1", "NaN", "1" * 41):
        assert _mensaje(precio=texto) == ("Escribe una cifra sin signo, separadores ni exponente.", "RD-14"), texto
    assert _mensaje(precio="0") == ("El precio debe ser mayor que cero.", "RD-06")
    assert _mensaje(precio="0.000") == ("El precio debe ser mayor que cero.", "RD-06")
    assert _mensaje(precio="1.12345678") == ("El precio admite a lo más 7 decimales; no se redondea.", "RD-13")
    assert _mensaje(precio="100000000000") == ("El precio es demasiado grande.", "RD-12")
    assert _mensaje(precio="1.0000000000000000000000000000001") == (
        "El precio admite a lo más 7 decimales; no se redondea.",
        "RD-13",
    )
    assert _mensaje(importe="-0.01") == ("El importe no puede ser negativo.", "RF-05")
    assert _mensaje(importe="1.234") == ("El importe admite a lo más 2 decimales; no se redondea.", "RD-13")
    assert _mensaje(importe="10000000000000000") == ("El importe es demasiado grande.", "RD-12")


def test_titulos_fechas_nombres_tipos_e_ids() -> None:
    assert _CuerpoCifras(titulos="100").titulos == 100  # type: ignore[arg-type]
    assert _CuerpoCifras(titulos="2147483647").titulos == 2147483647  # type: ignore[arg-type]
    assert _mensaje(titulos=5) == ('Envía esta cifra como texto, por ejemplo "50.00".', "RD-12")
    for texto in ("1.5", "0", "-1", "01", "2147483648", "99999999999999999999", ""):
        assert _mensaje(titulos=texto) == ("La cantidad de títulos debe ser un entero mayor que cero.", "RD-06"), texto

    assert _CuerpoCifras(fecha="2026-09-10").fecha == date(2026, 9, 10)  # type: ignore[arg-type]
    for texto in ("2026-11-31", "2026-1-01", "10/09/2026", "2026-09-10T00:00:00", "２０２６-09-10", "2026-09-10\n"):
        assert _mensaje(fecha=texto) == ("Escribe una fecha válida con el formato AAAA-MM-DD.", "RD-14"), texto
    assert _mensaje(fecha=20260910)[0] == "Escribe una fecha válida con el formato AAAA-MM-DD."

    assert _CuerpoCifras(nombre=" Casa A ").nombre == " Casa A "  # sin recortar (RD-14)
    assert _mensaje(nombre="   ") == ("Escribe un nombre.", "RD-03")
    assert _mensaje(nombre="") == ("Escribe un nombre.", "RD-03")
    assert _mensaje(nombre="a" * 121) == ("El nombre admite a lo más 120 caracteres.", "RD-03")
    assert _mensaje(nombre="a\tb") == ("El nombre no puede tener caracteres de control.", "RD-03")
    assert _mensaje(nombre=5) == ("Dato inválido.", "—")

    assert _CuerpoCifras(tipo="venta").tipo == "venta"
    assert _mensaje(tipo="Compra") == ("El tipo debe ser compra o venta.", "RF-05")

    assert _CuerpoCifras(ident=1).ident == 1
    for valor in ("1", 0, 2**63, 1.0, True):
        assert _mensaje(ident=valor)[0] == "Identificador inválido.", valor


def test_errores_de_validacion_sin_input() -> None:
    secreto = secrets.token_urlsafe(18)
    errores = errores_de_validacion(
        [
            {"type": "missing", "loc": ("body", "correo"), "msg": "Field required", "input": {"x": secreto}},
            {"type": "extra_forbidden", "loc": ("body", "otro"), "msg": "Extra", "input": secreto},
            {"type": "json_invalid", "loc": ("body", 12), "msg": "JSON decode error", "input": {},
             "ctx": {"error": secreto}},
            {"type": "model_attributes_type", "loc": ("body",), "msg": "x", "input": [secreto]},
            {"type": "bool_type", "loc": ("body", "confirmo"), "msg": "x", "input": secreto},
            {"type": "int_parsing", "loc": ("path", "portafolio_id"), "msg": "x", "input": secreto},
            {"type": "less_than_equal", "loc": ("query", "id"), "msg": "x", "input": secreto, "ctx": {"le": 3}},
            {"type": "string_type", "loc": ("body", "tasas", 0, "valor"), "msg": "x", "input": 5},
            {"type": "dato_invalido", "loc": ("body", "precio"), "msg": "Mensaje propio.", "ctx": {"regla": "RD-12"}},
        ]
    )
    assert errores == [
        ErrorCampo("correo", "—", "Falta este dato."),
        ErrorCampo("otro", "—", "Este dato no se puede enviar."),
        ErrorCampo("—", "—", "El cuerpo no es JSON válido."),
        ErrorCampo("—", "—", "El cuerpo debe ser un objeto JSON."),
        ErrorCampo("confirmo", "—", "Debe ser true o false."),
        ErrorCampo("portafolio_id", "—", "Identificador inválido."),
        ErrorCampo("id", "—", "Identificador inválido."),
        ErrorCampo("valor", "—", "Dato inválido."),
        ErrorCampo("precio", "RD-12", "Mensaje propio."),
    ]
    assert secreto not in repr(errores)


def test_sobre_de_errores() -> None:
    saldo = SaldoNegativo("DEMOACC", "Casa A", date(2026, 9, 18), -50)
    assert saldo.estado == 409
    assert sobre(saldo) == {
        "codigo": "saldo_negativo",
        "regla": "RF-28",
        "mensaje": "La venta dejaría el saldo de DEMOACC con Casa A en este portafolio en -50 títulos el "
        "18/09/2026. El saldo con cada intermediario no puede quedar negativo, aunque la posición total alcance.",
        "datos": {"fecha_saldo_negativo": "2026-09-18", "saldo_resultante": "-50"},
    }
    assert sobre(NoEncontrado("portafolio")) == {
        "codigo": "no_encontrado",
        "regla": "RF-02",
        "mensaje": "No existe el portafolio.",
    }
    invalidos = DatosInvalidos([ErrorCampo("nombre", "RD-03", "Escribe un nombre.")])
    assert sobre(invalidos)["regla"] == "RD-03" and sobre(invalidos)["errores"] == [
        {"campo": "nombre", "regla": "RD-03", "mensaje": "Escribe un nombre."}
    ]
    varias = DatosInvalidos([ErrorCampo("a", "RD-12", "x"), ErrorCampo("b", "RD-14", "y")])
    assert sobre(varias)["regla"] is None

    class Intervalo:
        inicio = date(2026, 9, 10)
        fin = date(2026, 10, 14)

    assert FechaFueraDeIntervalo(Intervalo()).mensaje == (
        "La fecha debe estar entre el 10/09/2026 y el 14/10/2026, el intervalo que cubren los datos de mercado."
    )
    assert PeriodoFueraDeIntervalo(Intervalo()).mensaje == (
        "El periodo debe empezar a partir del 11/09/2026 y terminar a más tardar el 14/10/2026."
    )
    assert ConfirmacionInvalida("Confirma la revocación.").regla == "RF-12"
    assert ConfirmacionInvalida("Escribe el nombre del portafolio para confirmar.").regla == "RD-10"


def test_reloj_y_vistas() -> None:
    assert epoch_iso(0) == "1969-12-31T18:00:00-06:00"
    assert momento_iso(datetime(2026, 10, 16, 6, 0, tzinfo=timezone.utc)) == "2026-10-16T00:00:00-06:00"
    with pytest.raises(ValueError):
        momento_iso(datetime(2026, 10, 16))
    assert isinstance(hoy_cdmx(), date) and isinstance(ahora_epoch(), int)

    cetes = InstrumentoRegistro(
        7, "BI261008", "CETES 261008", "cetes", "MXN", False, date(2026, 10, 8), Decimal("10.00")
    )
    assert instrumento_vista(cetes).valor_nominal == "10.00"
    fuente = FuenteRegistro(1, "Banco de México", "https://www.banxico.org.mx", False, "Fuente: …",
                            datetime(2026, 10, 16, 6, 0, tzinfo=timezone.utc))
    assert fuente_vista(fuente).fecha_carga == "2026-10-16T00:00:00-06:00"


# ---------------------------------------------------------------------------
# Con el clúster temporal
# ---------------------------------------------------------------------------


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cluster_temporal(cluster_pg: ClusterPg, dueno: psycopg.Connection[Any]) -> None:
    assert cluster_pg.puerto not in PUERTOS_PROHIBIDOS
    aprobados = re.search(r"RESULTADO: pasaron los (\d+) casos", cluster_pg.salida_03)
    assert aprobados and int(aprobados.group(1)) > 0, "03_probar_esquema.sql no informó sus casos aprobados"
    fila = dueno.execute(
        "SELECT current_database(), inet_server_port(), datctype, lower('ÁÉÍÓÚÜÑ') "
        "FROM pg_database WHERE datname = current_database()"
    ).fetchone()
    assert fila is not None
    base, puerto, ctype, minusculas = fila
    assert (base, puerto) == ("proyecto077_pruebas", cluster_pg.puerto)
    assert minusculas == "áéíóúüñ"
    locale = os.environ.get("P077_PG_LOCALE", "es-MX")
    if locale.upper() not in ("C.UTF-8", "C.UTF8", "BUILTIN"):
        assert ctype == locale
    conteos = dueno.execute(
        "SELECT (SELECT count(*) FROM instrumento), (SELECT count(*) FROM precio_cierre), "
        "(SELECT count(*) FROM tasa_referencia), (SELECT count(*) FROM version_aviso), "
        "(SELECT count(*) FROM usuario)"
    ).fetchone()
    assert conteos == (7, 71, 32, 1, 0)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_health_404_405_y_cache(cliente: ClientePrueba) -> None:
    salud = cliente.get("/health")
    assert salud.status_code == 200 and salud.json() == {"estado": "ok"}
    assert "no-store" not in salud.headers.get("cache-control", "")

    for ruta in ("/api/no-existe", "/otra/ruta"):
        desconocida = cliente.get(ruta)
        assert desconocida.status_code == 404
        assert desconocida.json() == {"codigo": "no_encontrado", "regla": "RF-02", "mensaje": "No existe el recurso."}
    assert cliente.get("/api/no-existe").headers["cache-control"] == "no-store"

    metodo = cliente.delete("/health")
    assert metodo.status_code == 405
    assert metodo.json() == {
        "codigo": "metodo_no_permitido",
        "regla": "RD-09",
        "mensaje": "Esta operación no está disponible.",
    }
    assert "GET" in metodo.headers.get("allow", "")
    assert len(cliente.respuestas) == 5


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_superusuario_falla_al_arrancar(cluster_pg: ClusterPg, config_pruebas: Settings) -> None:
    clave = conninfo_to_dict(cluster_pg.conninfo_dueno)["password"]
    config = config_pruebas.model_copy(update={"database_url": SecretStr(_url_dueno(cluster_pg))})
    with pytest.raises(RuntimeError, match="superusuario") as info:
        with TestClient(crear_app(config)):
            pass
    assert clave not in str(info.value) and "postgresql" not in str(info.value)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_zona_horaria_distinta_falla_al_arrancar(config_pruebas: Settings) -> None:
    url = config_pruebas.database_url.get_secret_value() + "?options=-c%20TimeZone%3DUTC"
    config = config_pruebas.model_copy(update={"database_url": SecretStr(url)})
    with pytest.raises(RuntimeError, match="zona horaria"):
        with TestClient(crear_app(config)):
            pass


# Aplicación con rutas de prueba (no se tocan las de app_pruebas) ------------


class _CuerpoPrueba(ModeloEntrada):
    correo: str
    contrasena: SecretStr
    precio: Precio
    cantidad: Titulos
    fecha: FechaEstricta
    nombre: Nombre
    confirmo: StrictBool
    intermediario_id: Identificador


class _CuerpoPortafolio(ModeloEntrada):
    usuario_id: Identificador
    nombre: str


@pytest.fixture(scope="module")
def app_con_pruebas(config_pruebas: Settings) -> Iterator[FastAPI]:
    app = crear_app(config_pruebas)

    @app.post("/api/prueba/validacion")
    def validacion(cuerpo: _CuerpoPrueba) -> dict[str, str]:
        return {"precio": como_texto(cuerpo.precio), "fecha": cuerpo.fecha.isoformat()}

    @app.get("/api/prueba/consulta/{recurso_id}")
    def consulta(recurso_id: IdRuta, dia: FechaEstricta | None = None) -> dict[str, Any]:
        return {"recurso_id": recurso_id, "dia": None if dia is None else dia.isoformat()}

    @app.get("/api/prueba/error/{tipo}")
    def error(tipo: str) -> None:
        if tipo == "saldo":
            raise SaldoNegativo("DEMOACC", "Casa A", date(2026, 9, 18), -50)
        if tipo == "sesion":
            raise SesionRequerida(cabeceras={"set-cookie": "sesion_prueba=; Max-Age=0; Path=/api"})
        raise RuntimeError(f"fallo con {tipo}")

    @app.post("/api/prueba/portafolio", status_code=201)
    def portafolio(
        cuerpo: _CuerpoPortafolio, confirmar: bool = True, sesion: Session = Depends(obtener_sesion)
    ) -> dict[str, int]:
        nuevo = sesion.execute(
            insert(Portafolio)
            .values(usuario_id=cuerpo.usuario_id, nombre=cuerpo.nombre, divisa_base="MXN")
            .returning(Portafolio.id)
        ).scalar_one()
        if confirmar:
            sesion.commit()
        return {"id": nuevo}

    @app.get("/api/prueba/cookie/poner")
    def poner_cookie(respuesta: Response) -> dict[str, str]:
        respuesta.set_cookie("sesion_prueba", "valor123", path="/api", httponly=True, samesite="strict")
        return {}

    @app.get("/api/prueba/cookie/ver")
    def ver_cookie(request: Request) -> dict[str, Any]:
        return {"valor": request.cookies.get("sesion_prueba")}

    @app.get("/api/prueba/config")
    def ver_config(config: Settings = Depends(config_actual)) -> dict[str, list[str]]:
        return {"origenes": config.lista_origenes}

    errores_motor = importar_si_existe("app.motor.errores")
    if errores_motor is not None:

        @app.get("/api/prueba/motor/{codigo}")
        def error_motor(codigo: str) -> None:
            intervalo = SimpleNamespace(inicio=date(2026, 9, 10), fin=date(2026, 10, 14))
            if codigo == "cifra":
                raise errores_motor.CifraNoCalculable(7, date(2026, 10, 8), "sin precio")
            if codigo == "historial":
                raise errores_motor.HistorialInvalido("motivo")
            raise errores_motor.PeriodoInvalido(codigo, "RF-09", intervalo)

    yield app


@pytest.fixture
def cliente_pruebas(app_con_pruebas: FastAPI) -> Iterator[ClientePrueba]:
    with ClientePrueba(app_con_pruebas) as c:
        yield c


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_config_actual(cliente_pruebas: ClientePrueba) -> None:
    assert cliente_pruebas.get("/api/prueba/config").json() == {"origenes": ["http://localhost:5173"]}


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_errores_del_motor(cliente_pruebas: ClientePrueba) -> None:
    if importar_si_existe("app.motor.errores") is None:
        pytest.skip("El motor (WP2) aún no existe.")
    esperados = {
        "periodo_invertido": (422, "La fecha final no puede ser anterior a la inicial."),
        "periodo_fuera_de_intervalo": (
            422,
            "El periodo debe empezar a partir del 11/09/2026 y terminar a más tardar el 14/10/2026.",
        ),
        "fecha_fuera_de_intervalo": (
            422,
            "La fecha debe estar entre el 10/09/2026 y el 14/10/2026, el intervalo que cubren los datos de mercado.",
        ),
        "cifra": (422, "No hay un precio o una tasa para valuar el instrumento 7 al 08/10/2026."),
        "historial": (500, "Ocurrió un error inesperado."),
        "otro_codigo": (500, "Ocurrió un error inesperado."),
    }
    for codigo, (estado, mensaje) in esperados.items():
        respuesta = cliente_pruebas.get(f"/api/prueba/motor/{codigo}")
        assert (respuesta.status_code, respuesta.json()["mensaje"]) == (estado, mensaje), codigo


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_422_sin_input_ni_contrasena(cliente_pruebas: ClientePrueba) -> None:
    secreto = secrets.token_urlsafe(18)
    valido = {
        "correo": "ana@example.com",
        "contrasena": secreto,
        "precio": "50.00",
        "cantidad": "100",
        "fecha": "2026-09-10",
        "nombre": "Casa A",
        "confirmo": True,
        "intermediario_id": 3,
    }
    correcto = cliente_pruebas.post("/api/prueba/validacion", json=valido)
    assert correcto.status_code == 200 and correcto.json() == {"precio": "50.00", "fecha": "2026-09-10"}

    malos = cliente_pruebas.post(
        "/api/prueba/validacion",
        json={**valido, "precio": 50, "cantidad": secreto, "fecha": "2026-11-31", "nombre": "  ",
              "confirmo": "si", "intermediario_id": "3", "correo": 5, "extra": secreto},
    )
    assert malos.status_code == 422
    cuerpo = malos.json()
    assert cuerpo["codigo"] == "datos_invalidos" and cuerpo["mensaje"] == "Revisa los datos marcados."
    assert set(cuerpo) == {"codigo", "regla", "mensaje", "errores"}
    por_campo = {e["campo"]: (e["regla"], e["mensaje"]) for e in cuerpo["errores"]}
    assert por_campo == {
        "correo": ("—", "Dato inválido."),
        "precio": ("RD-12", 'Envía esta cifra como texto, por ejemplo "50.00".'),
        "cantidad": ("RD-06", "La cantidad de títulos debe ser un entero mayor que cero."),
        "fecha": ("RD-14", "Escribe una fecha válida con el formato AAAA-MM-DD."),
        "nombre": ("RD-03", "Escribe un nombre."),
        "confirmo": ("—", "Debe ser true o false."),
        "intermediario_id": ("—", "Identificador inválido."),
        "extra": ("—", "Este dato no se puede enviar."),
    }

    faltan = cliente_pruebas.post("/api/prueba/validacion", json={"contrasena": secreto})
    assert faltan.status_code == 422
    assert {e["mensaje"] for e in faltan.json()["errores"]} == {"Falta este dato."}

    roto = cliente_pruebas.post(
        "/api/prueba/validacion",
        content=('{"contrasena": "' + secreto + '", ').encode(),
        headers={"Content-Type": "application/json"},
    )
    assert roto.status_code == 422
    assert roto.json()["errores"] == [{"campo": "—", "regla": "—", "mensaje": "El cuerpo no es JSON válido."}]

    lista = cliente_pruebas.post("/api/prueba/validacion", json=[secreto])
    assert lista.status_code == 422
    assert lista.json()["errores"][0]["mensaje"] == "El cuerpo debe ser un objeto JSON."

    for cuerpo_bytes in cliente_pruebas.respuestas:
        assert secreto.encode() not in cuerpo_bytes
        assert b'"input"' not in cuerpo_bytes and b'"ctx"' not in cuerpo_bytes and b'"url"' not in cuerpo_bytes


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_parametros_de_ruta_y_consulta(cliente_pruebas: ClientePrueba) -> None:
    assert cliente_pruebas.get("/api/prueba/consulta/5?dia=2026-09-10").json() == {"recurso_id": 5, "dia": "2026-09-10"}
    for ruta in ("abc", "0", "9223372036854775808"):
        respuesta = cliente_pruebas.get(f"/api/prueba/consulta/{ruta}")
        assert respuesta.status_code == 422
        assert respuesta.json()["errores"] == [
            {"campo": "recurso_id", "regla": "—", "mensaje": "Identificador inválido."}
        ]
    mala_fecha = cliente_pruebas.get("/api/prueba/consulta/5?dia=2026-02-30")
    assert mala_fecha.status_code == 422
    assert mala_fecha.json()["errores"] == [
        {"campo": "dia", "regla": "RD-14", "mensaje": "Escribe una fecha válida con el formato AAAA-MM-DD."}
    ]


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_errores_de_dominio_y_500(cliente_pruebas: ClientePrueba, caplog: pytest.LogCaptureFixture) -> None:
    saldo = cliente_pruebas.get("/api/prueba/error/saldo")
    assert saldo.status_code == 409
    assert saldo.json()["datos"] == {"fecha_saldo_negativo": "2026-09-18", "saldo_resultante": "-50"}
    assert saldo.headers["cache-control"] == "no-store"

    sesion = cliente_pruebas.get("/api/prueba/error/sesion")
    assert sesion.status_code == 401
    assert sesion.json() == {
        "codigo": "sesion_requerida",
        "regla": "RNF-03",
        "mensaje": "Inicia sesión para continuar.",
    }
    assert "sesion_prueba=;" in sesion.headers["set-cookie"]

    secreto = secrets.token_hex(8)
    with caplog.at_level(logging.DEBUG):
        interno = cliente_pruebas.get(f"/api/prueba/error/{secreto}")
    assert interno.status_code == 500
    assert interno.json() == {"codigo": "error_interno", "regla": None, "mensaje": "Ocurrió un error inesperado."}
    assert interno.headers["cache-control"] == "no-store"
    assert "RuntimeError" in caplog.text
    assert secreto not in caplog.text.replace(f"/api/prueba/error/{secreto}", "")


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_sesion_de_bd_integridad_y_rollback(
    cliente_pruebas: ClientePrueba, dueno: psycopg.Connection[Any]
) -> None:
    fila = dueno.execute(
        "INSERT INTO usuario (correo, contrasena_hash, estado) VALUES ('ana@example.com', 'h', 'activa') RETURNING id"
    ).fetchone()
    assert fila is not None
    usuario_id = fila[0]

    creado = cliente_pruebas.post("/api/prueba/portafolio", json={"usuario_id": usuario_id, "nombre": "Retiro"})
    assert creado.status_code == 201
    duplicado = cliente_pruebas.post("/api/prueba/portafolio", json={"usuario_id": usuario_id, "nombre": " retiro "})
    assert duplicado.status_code == 409
    assert duplicado.json()["codigo"] == "nombre_duplicado"
    vacio = cliente_pruebas.post("/api/prueba/portafolio", json={"usuario_id": usuario_id, "nombre": "   "})
    assert vacio.status_code == 422
    assert vacio.json()["errores"] == [{"campo": "nombre", "regla": "RD-03", "mensaje": "Escribe un nombre."}]
    sin_commit = cliente_pruebas.post(
        "/api/prueba/portafolio?confirmar=false", json={"usuario_id": usuario_id, "nombre": "Otro"}
    )
    assert sin_commit.status_code == 201
    nombres = [r[0] for r in dueno.execute("SELECT nombre FROM portafolio ORDER BY id").fetchall()]
    assert nombres == ["Retiro"]  # sin commit, la sesión se deshizo al cerrarse


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_cookie_de_ida_y_vuelta_en_localhost(cliente_pruebas: ClientePrueba) -> None:
    puesta = cliente_pruebas.get("/api/prueba/cookie/poner")
    assert "HttpOnly" in puesta.headers["set-cookie"] and "Path=/api" in puesta.headers["set-cookie"]
    assert cliente_pruebas.get("/api/prueba/cookie/ver").json() == {"valor": "valor123"}
    with ClientePrueba(cliente_pruebas.app) as otro:  # type: ignore[arg-type]
        assert otro.get("/api/prueba/cookie/ver").json() == {"valor": None}


# Modelos, privilegios de app_077 e integridad -------------------------------


@pytest.fixture
def motor_app(config_pruebas: Settings) -> Iterator[Engine]:
    engine = crear_motor_bd(config_pruebas)
    try:
        yield engine
    finally:
        engine.dispose()


def _traducir(sesion: Session, sentencia: Any) -> ErrorDominio | None:
    with pytest.raises(DBAPIError) as info:
        with sesion.begin_nested():
            sesion.execute(sentencia)
    assert "SQL parameters hidden" in str(info.value)  # hide_parameters=True (RNF-04)
    return traducir(info.value)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_app_077_escribe_con_los_modelos_y_traduce_violaciones(motor_app: Engine) -> None:
    with crear_fabrica(motor_app)() as s:
        ana = s.execute(
            insert(Usuario).values(correo="ana@example.com", contrasena_hash="h", estado="activa").returning(Usuario.id)
        ).scalar_one()
        beto = s.execute(
            insert(Usuario)
            .values(correo="beto@example.com", contrasena_hash="h", estado="activa")
            .returning(Usuario.id)
        ).scalar_one()
        aviso = s.execute(select(VersionAviso.id)).scalar_one()
        momento = s.execute(
            insert(Consentimiento)
            .values(usuario_id=ana, version_aviso_id=aviso, tipo="otorgamiento", medio="web")
            .returning(Consentimiento.momento)
        ).scalar_one()
        assert momento.tzinfo is not None
        principal = s.execute(
            insert(Portafolio).values(usuario_id=ana, nombre="Principal", divisa_base="MXN").returning(Portafolio.id)
        ).scalar_one()
        ajeno = s.execute(
            insert(Portafolio).values(usuario_id=beto, nombre="Principal", divisa_base="MXN").returning(Portafolio.id)
        ).scalar_one()
        casa_a = s.execute(
            insert(Intermediario).values(usuario_id=ana, nombre="Casa A").returning(Intermediario.id)
        ).scalar_one()
        casa_beto = s.execute(
            insert(Intermediario).values(usuario_id=beto, nombre="Casa A").returning(Intermediario.id)
        ).scalar_one()
        demoacc = s.execute(select(Instrumento.id).where(Instrumento.clave == "DEMOACC")).scalar_one()

        def transaccion(**cambios: Any) -> Any:
            valores = dict(
                usuario_id=ana, portafolio_id=principal, intermediario_id=casa_a, instrumento_id=demoacc,
                tipo="compra", fecha_concertacion=date(2026, 9, 10), cantidad=100,
                precio=Decimal("50.00"), importe_comisiones=Decimal("14.50"),
            )
            valores.update(cambios)
            return insert(Transaccion).values(**valores).returning(Transaccion.id, Transaccion.registrada_en)

        tx_id, registrada = s.execute(transaccion()).one()
        assert tx_id >= 1 and registrada.tzinfo is not None
        precio = s.execute(select(Transaccion.precio).where(Transaccion.id == tx_id)).scalar_one()
        assert como_texto(precio) == "50.00"

        bloqueado = s.execute(
            select(Portafolio.id)
            .where(Portafolio.id == principal, Portafolio.usuario_id == ana)
            .with_for_update(of=Portafolio)
        ).scalar_one()
        assert bloqueado == principal
        s.execute(
            update(Portafolio)
            .where(Portafolio.id == principal, Portafolio.usuario_id == ana)
            .values(nombre="Retiro")
        )

        codigos = {
            "correo": _traducir(
                s, insert(Usuario).values(correo=" ANA@example.com", contrasena_hash="h", estado="activa")
            ),
            "portafolio": _traducir(s, insert(Portafolio).values(usuario_id=ana, nombre=" retiro ", divisa_base="MXN")),
            "intermediario": _traducir(s, insert(Intermediario).values(usuario_id=ana, nombre="casa a")),
            "nombre_vacio": _traducir(s, insert(Intermediario).values(usuario_id=ana, nombre="   ")),
            "divisa": _traducir(s, insert(Portafolio).values(usuario_id=ana, nombre="Dólares", divisa_base="USD")),
            "futura": _traducir(s, transaccion(fecha_concertacion=date(2099, 1, 1))),
            "escala": _traducir(s, transaccion(precio=Decimal("1.12345678"))),
            "venta": _traducir(s, transaccion(tipo="venta", importe_comisiones=Decimal("5000.00"))),
            "portafolio_ajeno": _traducir(s, transaccion(portafolio_id=ajeno)),
            "intermediario_ajeno": _traducir(s, transaccion(intermediario_id=casa_beto)),
            "instrumento": _traducir(s, transaccion(instrumento_id=2**62)),
            "fuera_de_rango": _traducir(s, transaccion(cantidad=2**31)),
            "privilegio": _traducir(s, update(Usuario).where(Usuario.id == ana).values(correo="x@example.com")),
        }
        resumen = {k: (None if v is None else (v.codigo, v.mensaje, tuple(v.errores))) for k, v in codigos.items()}
        assert resumen["correo"][:2] == ("correo_registrado", "Ya existe una cuenta con ese correo.")
        assert resumen["portafolio"][0] == "nombre_duplicado" and "portafolio" in resumen["portafolio"][1]
        assert resumen["intermediario"][0] == "nombre_duplicado" and "intermediario" in resumen["intermediario"][1]
        assert resumen["nombre_vacio"][2] == (ErrorCampo("nombre", "RD-03", "Escribe un nombre."),)
        assert resumen["divisa"][2][0].campo == "divisa_base"
        assert resumen["futura"][0] == "fecha_posterior_al_registro"
        assert resumen["escala"][2][0].campo == "precio"
        assert resumen["venta"][2][0].campo == "importe_comisiones"
        assert resumen["portafolio_ajeno"][1] == "No existe el portafolio."
        assert resumen["intermediario_ajeno"][1] == "No existe el intermediario."
        assert resumen["instrumento"][1] == "No existe el instrumento."
        assert resumen["fuera_de_rango"][0] == "datos_invalidos"
        assert resumen["privilegio"] is None  # 42501: error de programación → 500

        borrados = s.execute(
            delete(Portafolio).where(Portafolio.id == principal, Portafolio.usuario_id == ana).returning(Portafolio.id)
        ).scalars().all()
        assert borrados == [principal]
        assert s.execute(select(Transaccion.id).where(Transaccion.id == tx_id)).first() is None  # cascada (RD-10)
        s.rollback()


# Fixtures del contrato -------------------------------------------------------


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_sin_red_bloquea_todo_salvo_el_cluster(
    sin_red: None, cluster_pg: ClusterPg, cliente: ClientePrueba, dueno: psycopg.Connection[Any]
) -> None:
    with pytest.raises(RedBloqueada):
        socket.getaddrinfo("example.com", 443)
    with pytest.raises(RedBloqueada):
        socket.create_connection(("192.0.2.1", 80), timeout=1)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as externo:
        with pytest.raises(RedBloqueada):
            externo.connect(("192.0.2.1", 80))
    with pytest.raises(RedBloqueada):
        socket.create_connection(("127.0.0.1", 5432), timeout=1)
    with socket.create_connection(("127.0.0.1", cluster_pg.puerto), timeout=5):
        pass
    assert cliente.get("/health").status_code == 200
    with ClientePrueba(cliente.app) as otro:  # type: ignore[arg-type]
        assert otro.get("/health").status_code == 200
    assert dueno.execute("SELECT 1").fetchone() == (1,)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_reloj_sustituye_y_restaura(app_pruebas: FastAPI, reloj: Any) -> None:
    reloj.fijar_hoy(date(2026, 10, 1))
    reloj.fijar_ahora(1_800_000_000)
    assert app_pruebas.dependency_overrides[hoy_cdmx]() == date(2026, 10, 1)
    assert app_pruebas.dependency_overrides[ahora_epoch]() == 1_800_000_000
    reloj.restaurar()
    assert hoy_cdmx not in app_pruebas.dependency_overrides
    assert ahora_epoch not in app_pruebas.dependency_overrides


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_bd_limpia_vacia_las_cuentas_y_conserva_semillas(dueno: psycopg.Connection[Any]) -> None:
    conteos = dueno.execute(
        "SELECT (SELECT count(*) FROM usuario), (SELECT count(*) FROM portafolio), (SELECT count(*) FROM instrumento)"
    ).fetchone()
    assert conteos == (0, 0, 7)


@pytest.mark.bd
@pytest.mark.usefixtures("bd_limpia")
def test_nueva_cuenta(nueva_cuenta: Any) -> None:
    if importar_si_existe("app.api.rutas_cuentas") is None:
        pytest.skip("Las rutas de cuentas (WP3) aún no existen.")
    ana = nueva_cuenta("ana@example.com")
    beto = nueva_cuenta()
    assert ana.usuario_id != beto.usuario_id
    assert ana.contrasena not in repr(ana)
    assert ana.cliente.get("/api/cuenta").status_code == 200
    assert ana.cliente.cookies is not beto.cliente.cookies
