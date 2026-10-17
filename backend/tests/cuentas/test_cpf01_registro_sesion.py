"""CPF-01: registro e inicio de sesión (RF-01; RD-03; RD-11; RD-23; D-02; D-03; D-05; D-46; §8.3)."""

from __future__ import annotations

import json
import re
import secrets
import unicodedata
from types import SimpleNamespace
from typing import Any

import psycopg
import pytest
from pwdlib.hashers.argon2 import Argon2Hasher

from app.cuentas import contrasenas
from tests.conftest import ClientePrueba
from tests.cuentas.apoyo import (
    AVISO_VIGENTE_DESDE,
    CREDENCIALES_INVALIDAS,
    NOMBRE_COOKIE,
    aviso_id,
    contrasena_nueva,
    conteos,
    iniciar,
    registrar,
)

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

MOMENTO_CDMX = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?-0[56]:00")
HASH_OWASP = re.compile(r"\$argon2id\$v=19\$m=19456,t=2,p=1\$[A-Za-z0-9+/]+\$[A-Za-z0-9+/]+")
MENSAJE_CORREO = "Escribe un correo válido, como nombre@example.com."


def _sin_contrasena(cliente: ClientePrueba, *secretos: str) -> None:
    for cuerpo in cliente.respuestas:
        for secreto in secretos:
            assert secreto.encode() not in cuerpo
        assert b"contrasena_hash" not in cuerpo and b"$argon2" not in cuerpo


def test_crit1_registro_inicio_de_sesion_y_cuenta(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    version = aviso_id(cliente)
    contrasena = contrasena_nueva()

    alta = registrar(cliente, "ana@example.com", contrasena, version_aviso_id=version)
    assert alta.status_code == 201
    cuerpo = alta.json()
    assert set(cuerpo) == {"correo", "estado", "consentimiento"}
    assert (cuerpo["correo"], cuerpo["estado"]) == ("ana@example.com", "activa")
    otorgamiento = cuerpo["consentimiento"]
    assert set(otorgamiento) == {"tipo", "momento", "medio", "version_aviso_id"}
    assert (otorgamiento["tipo"], otorgamiento["medio"], otorgamiento["version_aviso_id"]) == (
        "otorgamiento",
        "web",
        version,
    )
    assert MOMENTO_CDMX.fullmatch(otorgamiento["momento"])
    # El registro no abre la sesión (D-05).
    assert "set-cookie" not in alta.headers and NOMBRE_COOKIE not in cliente.cookies

    sin_sesion = cliente.get("/api/cuenta")
    assert sin_sesion.status_code == 401

    inicio = iniciar(cliente, "ana@example.com", contrasena)
    assert inicio.status_code == 200
    assert set(inicio.json()) == {"correo", "expira_en"}
    assert inicio.json()["correo"] == "ana@example.com"
    assert MOMENTO_CDMX.fullmatch(inicio.json()["expira_en"])
    assert inicio.headers["set-cookie"].startswith(f"{NOMBRE_COOKIE}=")

    cuenta = cliente.get("/api/cuenta")
    assert cuenta.status_code == 200
    vista = cuenta.json()
    assert (vista["correo"], vista["estado"]) == ("ana@example.com", "activa")
    assert vista["consentimientos"] == [
        {**otorgamiento, "aviso_vigente_desde": AVISO_VIGENTE_DESDE},
    ]

    filas = dueno.execute("SELECT correo, contrasena_hash, estado FROM usuario").fetchall()
    assert len(filas) == 1
    correo, contrasena_hash, estado = filas[0]
    assert (correo, estado) == ("ana@example.com", "activa")
    assert HASH_OWASP.fullmatch(contrasena_hash)
    _sin_contrasena(cliente, contrasena)


def test_crit2_correo_unico_sin_distinguir_mayusculas_ni_espacios(
    cliente: ClientePrueba, dueno: psycopg.Connection[Any]
) -> None:
    contrasena = contrasena_nueva()
    assert registrar(cliente, "ana@example.com", contrasena).status_code == 201
    antes = conteos(dueno)

    for variante in ("Ana@example.com ", " ANA@EXAMPLE.COM", "ana@example.com"):
        repetido = registrar(cliente, variante, contrasena_nueva())
        assert repetido.status_code == 409, variante
        assert repetido.json() == {
            "codigo": "correo_registrado",
            "regla": "RD-03",
            "mensaje": "Ya existe una cuenta con ese correo.",
        }
    assert conteos(dueno) == antes

    inicio = iniciar(cliente, " ANA@example.com", contrasena)
    assert inicio.status_code == 200
    assert inicio.json()["correo"] == "ana@example.com"  # el guardado, tal como se capturó


def test_correo_se_guarda_tal_como_se_capturo(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    contrasena = contrasena_nueva()
    alta = registrar(cliente, "  Beto.Lopez@Example.COM ", contrasena)
    assert alta.status_code == 201
    assert alta.json()["correo"] == "  Beto.Lopez@Example.COM "
    assert dueno.execute("SELECT correo FROM usuario").fetchall() == [("  Beto.Lopez@Example.COM ",)]
    assert iniciar(cliente, "beto.lopez@example.com", contrasena).status_code == 200


def test_crit3_datos_invalidos_no_escriben_nada(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    version = aviso_id(cliente)
    contrasena = contrasena_nueva()
    valido: dict[str, Any] = {
        "correo": "ana@example.com",
        "contrasena": contrasena,
        "consentimiento": True,
        "version_aviso_id": version,
    }
    corta = secrets.token_urlsafe(12)[:14]
    larga = secrets.token_urlsafe(100)[:129]
    casos: dict[str, tuple[dict[str, Any], list[tuple[str, str, str]]]] = {
        "correo sin dominio": ({"correo": "ana@"}, [("correo", "RF-01", MENSAJE_CORREO)]),
        "correo vacío": ({"correo": "   "}, [("correo", "RF-01", MENSAJE_CORREO)]),
        "correo .test": ({"correo": "ana@ejemplo.test"}, [("correo", "RF-01", MENSAJE_CORREO)]),
        "correo de 255": ({"correo": "a" * 64 + "@" + "b" * 63 + "." + "c" * 63 + "." + "d" * 61 + ".mx"},
                          [("correo", "RF-01", MENSAJE_CORREO)]),
        "contraseña de 14": (
            {"contrasena": corta},
            [("contrasena", "RF-01", "La contraseña debe tener al menos 15 caracteres.")],
        ),
        "contraseña de 129": (
            {"contrasena": larga},
            [("contrasena", "RF-01", "La contraseña admite a lo más 128 caracteres.")],
        ),
        "contraseña igual al correo": (
            {"correo": "ana.lopez.garcia@example.com", "contrasena": " ANA.Lopez.Garcia@example.com "},
            [("contrasena", "RF-01", "La contraseña no puede ser tu correo.")],
        ),
        "sin consentimiento": (
            {"consentimiento": False},
            [("consentimiento", "RD-11", "Para registrarte debes marcar la casilla de consentimiento.")],
        ),
        "consentimiento ausente": ({"consentimiento": None}, [("consentimiento", "—", "Falta este dato.")]),
        "consentimiento en texto": ({"consentimiento": "true"}, [("consentimiento", "—", "Debe ser true o false.")]),
        "correo como número": ({"correo": 5}, [("correo", "—", "Dato inválido.")]),
        "contraseña como número": ({"contrasena": 123456789012345678}, [("contrasena", "—", "Dato inválido.")]),
        "versión en texto": (
            {"version_aviso_id": str(version)},
            [("version_aviso_id", "—", "Identificador inválido.")],
        ),
        "campo extra": ({"extra": contrasena}, [("extra", "—", "Este dato no se puede enviar.")]),
        "todo junto": (
            {"correo": "ana@", "contrasena": corta, "consentimiento": False},
            [
                ("correo", "RF-01", MENSAJE_CORREO),
                ("contrasena", "RF-01", "La contraseña debe tener al menos 15 caracteres."),
                ("consentimiento", "RD-11", "Para registrarte debes marcar la casilla de consentimiento."),
            ],
        ),
    }
    antes = conteos(dueno)
    for nombre, (cambios, esperados) in casos.items():
        cuerpo = {**valido, **cambios}
        cuerpo = {k: v for k, v in cuerpo.items() if v is not None}
        respuesta = cliente.post("/api/cuentas", json=cuerpo)
        assert respuesta.status_code == 422, nombre
        sobre = respuesta.json()
        assert (sobre["codigo"], sobre["mensaje"]) == ("datos_invalidos", "Revisa los datos marcados."), nombre
        obtenidos = [(e["campo"], e["regla"], e["mensaje"]) for e in sobre["errores"]]
        assert obtenidos == esperados, nombre
        assert conteos(dueno) == antes, nombre
    assert antes == (0, 0)
    _sin_contrasena(cliente, contrasena, corta, larga)


def test_crit3_401_identico_en_todos_los_casos(
    cliente: ClientePrueba, dueno: psycopg.Connection[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    contrasena_ana = contrasena_nueva()
    contrasena_beto = contrasena_nueva()
    assert registrar(cliente, "ana@example.com", contrasena_ana).status_code == 201
    assert registrar(cliente, "beto@example.com", contrasena_beto).status_code == 201
    with ClientePrueba(cliente.app) as beto:  # type: ignore[arg-type]
        assert iniciar(beto, "beto@example.com", contrasena_beto).status_code == 200
        assert beto.post("/api/cuenta/revocacion", json={"confirmo": True}).status_code == 204

    verificaciones: list[bool] = []
    verificar_original = contrasenas.verificar

    def espia(contrasena_nfkc: str, hash_guardado: str | None) -> tuple[bool, str | None]:
        verificaciones.append(hash_guardado is None)
        return verificar_original(contrasena_nfkc, hash_guardado)

    monkeypatch.setattr(contrasenas, "verificar", espia)
    # Y el cálculo de Argon2 mismo: con un correo inexistente también se verifica (contra HASH_FICTICIO).
    argon2: list[str] = []
    hasher = contrasenas.HASHER

    class EspiaHasher:
        def verify(self, *args: Any, **kwargs: Any) -> Any:
            argon2.append("verify")
            return hasher.verify(*args, **kwargs)

        def verify_and_update(self, *args: Any, **kwargs: Any) -> Any:
            argon2.append("verify_and_update")
            return hasher.verify_and_update(*args, **kwargs)

    monkeypatch.setattr(contrasenas, "HASHER", EspiaHasher())

    casos = {
        "correo inexistente": ("nadie@example.com", contrasena_ana),
        "contraseña errónea": ("ana@example.com", contrasena_ana[:-1] + ("x" if contrasena_ana[-1] != "x" else "y")),
        "cuenta bloqueada": ("beto@example.com", contrasena_beto),
        "contraseña vacía": ("ana@example.com", ""),
        "correo de 321": ("a" * 309 + "@example.com", contrasena_ana),
        "contraseña de 129": ("ana@example.com", "x" * 129),
    }
    respuestas = {nombre: iniciar(cliente, correo, clave) for nombre, (correo, clave) in casos.items()}
    primera = respuestas["correo inexistente"]
    assert primera.status_code == 401 and primera.json() == CREDENCIALES_INVALIDAS
    for nombre, respuesta in respuestas.items():
        assert respuesta.status_code == 401, nombre
        assert respuesta.content == primera.content, nombre
        assert sorted(respuesta.headers.items()) == sorted(primera.headers.items()), nombre
        assert "set-cookie" not in respuesta.headers, nombre
    # Los correos y contraseñas demasiado largos dan 401 sin calcular el hash; el inexistente usa el ficticio.
    assert verificaciones == [True, False, False, False]
    assert argon2 == ["verify", "verify_and_update", "verify_and_update", "verify_and_update"]
    assert NOMBRE_COOKIE not in cliente.cookies


def test_aviso_distinto_del_vigente_da_409(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    version = aviso_id(cliente)
    respuesta = registrar(cliente, "ana@example.com", contrasena_nueva(), version_aviso_id=version + 1000)
    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "codigo": "aviso_cambio",
        "regla": "RF-12",
        "mensaje": "El aviso de privacidad cambió. Léelo de nuevo antes de registrarte.",
    }
    assert conteos(dueno) == (0, 0)


def test_sin_aviso_vigente_da_503(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    version = aviso_id(cliente)
    dueno.execute("UPDATE version_aviso SET vigente_desde = vigente_desde + interval '100 years'")
    try:
        aviso = cliente.get("/api/aviso-privacidad")
        alta = registrar(cliente, "ana@example.com", contrasena_nueva(), version_aviso_id=version)
    finally:
        dueno.execute("UPDATE version_aviso SET vigente_desde = vigente_desde - interval '100 years'")
    esperado = {
        "codigo": "sin_aviso_vigente",
        "regla": "RF-12",
        "mensaje": "No hay un aviso de privacidad vigente; por ahora no se pueden crear cuentas.",
    }
    assert (aviso.status_code, aviso.json()) == (503, esperado)
    assert (alta.status_code, alta.json()) == (503, esperado)
    assert conteos(dueno) == (0, 0)
    assert aviso_id(cliente) == version


def test_contrasena_se_normaliza_con_nfkc(cliente: ClientePrueba) -> None:
    base = contrasena_nueva()
    ancha = "".join(chr(ord(c) + 0xFEE0) if "!" <= c <= "~" else c for c in base)  # formas de ancho completo
    assert ancha != base
    assert registrar(cliente, "ana@example.com", ancha).status_code == 201
    assert iniciar(cliente, "ana@example.com", base).status_code == 200
    assert iniciar(cliente, "ana@example.com", ancha).status_code == 200


def test_rehash_y_hash_desconocido(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    contrasena = contrasena_nueva()
    viejo = Argon2Hasher(time_cost=3, memory_cost=19456, parallelism=1).hash(contrasena)
    dueno.execute(
        "INSERT INTO usuario (correo, contrasena_hash, estado) VALUES "
        "('ana@example.com', %s, 'activa'), ('beto@example.com', 'no-es-un-hash', 'activa')",
        (viejo,),
    )
    assert iniciar(cliente, "ana@example.com", contrasena).status_code == 200
    (nuevo,) = dueno.execute("SELECT contrasena_hash FROM usuario WHERE correo = 'ana@example.com'").fetchone() or ("",)
    assert nuevo != viejo and HASH_OWASP.fullmatch(nuevo)
    assert iniciar(cliente, "ana@example.com", contrasena).status_code == 200

    desconocido = iniciar(cliente, "beto@example.com", contrasena)
    assert desconocido.status_code == 401 and desconocido.json() == CREDENCIALES_INVALIDAS
    assert dueno.execute("SELECT contrasena_hash FROM usuario WHERE correo = 'beto@example.com'").fetchone() == (
        "no-es-un-hash",
    )


def test_entradas_enormes_no_se_normalizan(
    cliente: ClientePrueba, dueno: psycopg.Connection[Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    """NFKC tarda un tiempo cuadrático con U+FDFA repetido y no suelta el GIL: congelaría la API.

    Ningún texto de más de LARGO_MAXIMO_CRUDO (4 × 128) puntos de código pasa por NFKC, que junta
    a lo más 4 en 1, así que aun normalizado excedería los 128; se rechaza igual que antes.
    """
    contrasena = contrasena_nueva()
    assert registrar(cliente, "ana@example.com", contrasena).status_code == 201
    largos: list[int] = []

    def normalize(forma: str, texto: str) -> str:
        largos.append(len(texto))
        return unicodedata.normalize(forma, texto)

    monkeypatch.setattr(contrasenas, "unicodedata", SimpleNamespace(normalize=normalize))
    bomba = "ﷺ" * 20_000
    primera = iniciar(cliente, "nadie@example.com", contrasena)
    for correo, clave in (("ana@example.com", bomba), (bomba, contrasena), (bomba, bomba)):
        respuesta = iniciar(cliente, correo, clave)
        assert (respuesta.status_code, respuesta.content) == (401, primera.content)
    alta = registrar(cliente, "beto@example.com", bomba)
    assert alta.status_code == 422
    assert alta.json()["errores"] == [
        {"campo": "contrasena", "regla": "RF-01", "mensaje": "La contraseña admite a lo más 128 caracteres."}
    ]
    alta = registrar(cliente, bomba, contrasena_nueva())
    assert alta.status_code == 422
    assert alta.json()["errores"] == [{"campo": "correo", "regla": "RF-01", "mensaje": MENSAJE_CORREO}]
    assert largos and max(largos) <= 4 * contrasenas.LARGO_MAXIMO, max(largos)
    assert contrasenas.LARGO_MAXIMO_CRUDO == 4 * contrasenas.LARGO_MAXIMO
    assert conteos(dueno) == (1, 1)
    # Una contraseña de más de 128 puntos de código que NFKC deja en 128 o menos sigue valiendo.
    compuesta = "ᾂ" * 30  # 120 puntos de código; NFKC la deja en 30 (U+1F82)
    assert unicodedata.normalize("NFKC", compuesta) == "ᾂ" * 30
    assert registrar(cliente, "carla@example.com", compuesta * 4).status_code == 201  # 480 → 120
    assert iniciar(cliente, "carla@example.com", "ᾂ" * 120).status_code == 200


def test_correo_de_mas_de_254_con_espacios_se_rechaza(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    """D-44: el límite de 254 se aplica al valor que se guarda (RD-14), con sus espacios."""
    for correo in (" " * 300 + "pad@example.com", "pad@example.com" + " " * 240):
        respuesta = registrar(cliente, correo, contrasena_nueva())
        assert respuesta.status_code == 422
        assert respuesta.json()["errores"] == [{"campo": "correo", "regla": "RF-01", "mensaje": MENSAJE_CORREO}]
    assert conteos(dueno) == (0, 0)
    justo = "pad@example.com" + " " * 239
    assert len(justo) == 254
    assert registrar(cliente, justo, contrasena_nueva()).status_code == 201
    assert dueno.execute("SELECT length(correo) FROM usuario").fetchall() == [(254,)]


def test_caracteres_que_no_se_pueden_guardar(cliente: ClientePrueba, dueno: psycopg.Connection[Any]) -> None:
    """NUL y sustitutos sueltos (válidos en JSON) dan 422 o 401, nunca un 500."""
    contrasena = contrasena_nueva()
    assert registrar(cliente, "ana@example.com", contrasena).status_code == 201
    version = aviso_id(cliente)
    sustituto = chr(0xD800)
    nul = chr(0)

    def enviar(ruta: str, cuerpo: dict[str, Any]) -> Any:
        # json.dumps escapa el sustituto como \ud800; httpx no podría codificarlo en UTF-8.
        contenido = json.dumps(cuerpo).encode("ascii")
        return cliente.post(ruta, content=contenido, headers={"Content-Type": "application/json"})

    alta = enviar(
        "/api/cuentas",
        {
            "correo": "beto@example.com",
            "contrasena": sustituto * 20,
            "consentimiento": True,
            "version_aviso_id": version,
        },
    )
    assert alta.status_code == 422
    assert alta.json()["errores"] == [
        {"campo": "contrasena", "regla": "RF-01", "mensaje": "La contraseña tiene caracteres no válidos."}
    ]
    for correo in (f"beto{nul}@example.com", f"beto{sustituto}@example.com"):
        malo = enviar(
            "/api/cuentas",
            {"correo": correo, "contrasena": contrasena, "consentimiento": True, "version_aviso_id": version},
        )
        assert malo.status_code == 422 and malo.json()["errores"][0]["campo"] == "correo"

    primera = iniciar(cliente, "nadie@example.com", contrasena)
    for correo, clave in (
        (f"ana@example.com{nul}", contrasena),
        (f"ana{sustituto}@example.com", contrasena),
        ("ana@example.com", contrasena + sustituto),
    ):
        respuesta = enviar("/api/sesion", {"correo": correo, "contrasena": clave})
        assert respuesta.status_code == 401
        assert respuesta.content == primera.content
    assert conteos(dueno) == (1, 1)
