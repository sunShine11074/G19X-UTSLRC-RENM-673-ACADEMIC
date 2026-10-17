"""CPF-03: gestionar portafolios (RF-03; RF-02; RD-03; RD-08; RD-10; D-10; §4.3 E12 a E16; §8.3)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import httpx
import psycopg
import pytest

from tests.conftest import ClientePrueba, CuentaPrueba

pytestmark = [pytest.mark.bd, pytest.mark.api, pytest.mark.usefixtures("bd_limpia")]

NO_EXISTE_PORTAFOLIO = {"codigo": "no_encontrado", "regla": "RF-02", "mensaje": "No existe el portafolio."}
NOMBRE_DUPLICADO = {
    "codigo": "nombre_duplicado",
    "regla": "RD-03",
    "mensaje": "Ya tienes un portafolio con ese nombre (no se distinguen mayúsculas ni espacios al inicio o "
    "al final).",
}
CONFIRMACION_INVALIDA = {
    "codigo": "confirmacion_invalida",
    "regla": "RD-10",
    "mensaje": "Escribe el nombre del portafolio para confirmar.",
}
SOLO_MXN = {"campo": "divisa_base", "regla": "RD-08", "mensaje": "En esta versión la única divisa base es MXN."}
SOLO_NOMBRE = {"campo": "divisa_base", "regla": "RF-03", "mensaje": "Solo se puede cambiar el nombre."}
NOMBRE_VACIO = {"campo": "nombre", "regla": "RD-03", "mensaje": "Escribe un nombre."}
ID_INEXISTENTE = 2**62


def _crear(c: ClientePrueba, nombre: Any, **extra: Any) -> httpx.Response:
    return c.post("/api/portafolios", json={"nombre": nombre, **extra})


def _id(respuesta: httpx.Response, estado: int = 201) -> int:
    assert respuesta.status_code == estado, (respuesta.status_code, respuesta.json())
    return int(respuesta.json()["id"])


def _errores(respuesta: httpx.Response) -> list[dict[str, str]]:
    assert respuesta.status_code == 422, (respuesta.status_code, respuesta.json())
    cuerpo = respuesta.json()
    assert cuerpo["codigo"] == "datos_invalidos" and cuerpo["mensaje"] == "Revisa los datos marcados."
    return cuerpo["errores"]


def _eliminar(c: ClientePrueba, portafolio_id: int, cuerpo: Any = None) -> httpx.Response:
    if cuerpo is None:
        return c.request("DELETE", f"/api/portafolios/{portafolio_id}")
    return c.request("DELETE", f"/api/portafolios/{portafolio_id}", json=cuerpo)


def _portafolios(dueno: psycopg.Connection[Any]) -> list[tuple[int, int, str, str]]:
    return [
        (int(f[0]), int(f[1]), f[2], f[3])
        for f in dueno.execute("SELECT id, usuario_id, nombre, divisa_base FROM portafolio ORDER BY id").fetchall()
    ]


def _conteo(dueno: psycopg.Connection[Any], tabla: str) -> int:
    fila = dueno.execute(f"SELECT count(*) FROM {tabla}").fetchone()
    assert fila is not None
    return int(fila[0])


def test_crear_en_mxn_y_rechazar_otra_divisa(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    cuenta = nueva_cuenta()
    c = cuenta.cliente

    retiro = _crear(c, "Retiro")
    assert retiro.status_code == 201
    assert retiro.json() == {"id": retiro.json()["id"], "nombre": "Retiro", "divisa_base": "MXN"}
    ahorro_id = _id(_crear(c, "ahorro", divisa_base="MXN"))

    for divisa in ("USD", "mxn", " MXN", "", None, 5):
        assert _errores(_crear(c, "Dólares", divisa_base=divisa)) == [SOLO_MXN]
    # Todos los errores de forma juntos.
    assert _errores(_crear(c, "", divisa_base="USD")) == [NOMBRE_VACIO, SOLO_MXN]
    assert _errores(c.post("/api/portafolios", json={"divisa_base": "MXN"})) == [
        {"campo": "nombre", "regla": "—", "mensaje": "Falta este dato."}
    ]
    assert _errores(_crear(c, "Otro", usuario_id=1)) == [
        {"campo": "usuario_id", "regla": "—", "mensaje": "Este dato no se puede enviar."}
    ]

    assert _portafolios(dueno) == [
        (retiro.json()["id"], cuenta.usuario_id, "Retiro", "MXN"),
        (ahorro_id, cuenta.usuario_id, "ahorro", "MXN"),
    ]
    # Orden por nombre sin distinguir mayúsculas.
    assert c.get("/api/portafolios").json() == [
        {"id": ahorro_id, "nombre": "ahorro", "divisa_base": "MXN"},
        {"id": retiro.json()["id"], "nombre": "Retiro", "divisa_base": "MXN"},
    ]
    vista = c.get(f"/api/portafolios/{ahorro_id}")
    assert vista.status_code == 200
    assert vista.json() == {"id": ahorro_id, "nombre": "ahorro", "divisa_base": "MXN"}


def test_nombre_unico_sin_mayusculas_ni_espacios(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    a = nueva_cuenta().cliente
    b = nueva_cuenta()

    _id(_crear(a, "Retiro"))
    for nombre in (" retiro ", "RETIRO", "retiro", "Retiro"):
        duplicado = _crear(a, nombre)
        assert duplicado.status_code == 409
        assert duplicado.json() == NOMBRE_DUPLICADO

    for nombre in ("", "   "):
        assert _errores(_crear(a, nombre)) == [NOMBRE_VACIO]
    assert _errores(_crear(a, "x" * 121)) == [
        {"campo": "nombre", "regla": "RD-03", "mensaje": "El nombre admite a lo más 120 caracteres."}
    ]
    assert _errores(_crear(a, "Re\ttiro")) == [
        {"campo": "nombre", "regla": "RD-03", "mensaje": "El nombre no puede tener caracteres de control."}
    ]
    assert _errores(_crear(a, 5)) == [{"campo": "nombre", "regla": "—", "mensaje": "Dato inválido."}]
    # Un sustituto suelto: JSON lo admite, pero PostgreSQL no lo puede guardar.
    sustituto = a.post(
        "/api/portafolios", content=b'{"nombre": "Re\\ud800tiro"}', headers={"Content-Type": "application/json"}
    )
    assert _errores(sustituto) == [
        {"campo": "nombre", "regla": "RD-03", "mensaje": "El nombre tiene caracteres no válidos."}
    ]

    # El nombre se guarda tal como se capturó (RD-14), y otra cuenta sí puede usar «Retiro».
    con_espacios = _crear(a, "  Mi Ahorro ")
    assert con_espacios.status_code == 201 and con_espacios.json()["nombre"] == "  Mi Ahorro "
    assert _crear(a, "mi ahorro").status_code == 409
    otra = _crear(b.cliente, "Retiro")
    assert otra.status_code == 201 and otra.json()["nombre"] == "Retiro"

    assert [nombre for _, usuario, nombre, _ in _portafolios(dueno) if usuario == b.usuario_id] == ["Retiro"]
    assert _conteo(dueno, "portafolio") == 3
    assert [p["nombre"] for p in b.cliente.get("/api/portafolios").json()] == ["Retiro"]


def test_renombrar_solo_cambia_el_nombre(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    c = nueva_cuenta().cliente
    retiro = _id(_crear(c, "Retiro"))
    _id(_crear(c, "Ahorro"))
    ruta = f"/api/portafolios/{retiro}"

    for divisa in ("USD", "MXN", None):
        assert _errores(c.patch(ruta, json={"nombre": "Retiro", "divisa_base": divisa})) == [SOLO_NOMBRE]
    assert _errores(c.patch(ruta, json={"nombre": "Retiro", "id": 9})) == [
        {"campo": "id", "regla": "—", "mensaje": "Este dato no se puede enviar."}
    ]
    assert _errores(c.patch(ruta, json={})) == [{"campo": "nombre", "regla": "—", "mensaje": "Falta este dato."}]
    assert _errores(c.patch(ruta, json={"nombre": " "})) == [NOMBRE_VACIO]
    duplicado = c.patch(ruta, json={"nombre": " ahorro"})
    assert duplicado.status_code == 409 and duplicado.json() == NOMBRE_DUPLICADO
    assert c.get(ruta).json()["nombre"] == "Retiro"

    # Cambiar solo mayúsculas del propio nombre no choca consigo mismo.
    assert c.patch(ruta, json={"nombre": "RETIRO"}).json() == {"id": retiro, "nombre": "RETIRO", "divisa_base": "MXN"}
    renombrado = c.patch(ruta, json={"nombre": "Jubilación"})
    assert renombrado.status_code == 200
    assert renombrado.json() == {"id": retiro, "nombre": "Jubilación", "divisa_base": "MXN"}
    assert c.get(ruta).json() == renombrado.json()
    assert [(n, d) for i, _, n, d in _portafolios(dueno) if i == retiro] == [("Jubilación", "MXN")]


def _preparar_con_transacciones(c: ClientePrueba) -> tuple[int, int, int]:
    """Portafolios «Retiro» (2 transacciones) y «Otro» (1), con «Casa A»; devuelve sus ids."""
    retiro = _id(_crear(c, "Retiro"))
    otro = _id(_crear(c, "Otro"))
    casa = _id(c.post("/api/intermediarios", json={"nombre": "Casa A"}))
    demoacc = next(i["id"] for i in c.get("/api/instrumentos").json() if i["clave"] == "DEMOACC")
    for portafolio, fecha in ((retiro, "2026-09-11"), (retiro, "2026-09-14"), (otro, "2026-09-11")):
        _id(
            c.post(
                f"/api/portafolios/{portafolio}/transacciones",
                json={
                    "intermediario_id": casa,
                    "instrumento_id": demoacc,
                    "tipo": "compra",
                    "fecha_concertacion": fecha,
                    "cantidad": "10",
                    "precio": "100.00",
                    "importe_comisiones": "2.90",
                },
            )
        )
    return retiro, otro, casa


def test_eliminar_con_confirmacion_borra_sus_transacciones_y_conserva_intermediarios(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any]
) -> None:
    c = nueva_cuenta().cliente
    retiro, otro, casa = _preparar_con_transacciones(c)
    antes = _portafolios(dueno)
    assert _conteo(dueno, "transaccion") == 3

    sin_cuerpo = _eliminar(c, retiro)
    assert sin_cuerpo.status_code == 422 and sin_cuerpo.json()["codigo"] == "datos_invalidos"
    assert _errores(_eliminar(c, retiro, {})) == [
        {"campo": "confirmacion", "regla": "—", "mensaje": "Falta este dato."}
    ]
    assert _errores(_eliminar(c, retiro, {"confirmacion": 5})) == [
        {"campo": "confirmacion", "regla": "—", "mensaje": "Dato inválido."}
    ]
    for confirmacion in ("Otro", "", "Retiro2", "Re tiro", "Retiro\u0000", "\ud800"):
        if confirmacion == "\ud800":
            respuesta = c.request(
                "DELETE",
                f"/api/portafolios/{retiro}",
                content=b'{"confirmacion": "\\ud800"}',
                headers={"Content-Type": "application/json"},
            )
        else:
            respuesta = _eliminar(c, retiro, {"confirmacion": confirmacion})
        assert respuesta.status_code == 422, confirmacion
        assert respuesta.json() == CONFIRMACION_INVALIDA
    assert _portafolios(dueno) == antes
    assert _conteo(dueno, "transaccion") == 3

    # La confirmación se compara como RD-03: sin mayúsculas ni espacios en los extremos.
    borrado = _eliminar(c, retiro, {"confirmacion": "  RETIRO "})
    assert borrado.status_code == 204 and borrado.content == b""
    assert c.get(f"/api/portafolios/{retiro}").status_code == 404
    assert [p["id"] for p in c.get("/api/portafolios").json()] == [otro]
    fila = dueno.execute(
        "SELECT count(*) FILTER (WHERE portafolio_id = %s), count(*) FILTER (WHERE portafolio_id = %s) "
        "FROM transaccion",
        (retiro, otro),
    ).fetchone()
    assert fila == (0, 1)
    assert c.get("/api/intermediarios").json() == [{"id": casa, "nombre": "Casa A"}]

    otra_vez = _eliminar(c, retiro, {"confirmacion": "Retiro"})
    assert otra_vez.status_code == 404 and otra_vez.json() == NO_EXISTE_PORTAFOLIO


def test_lo_ajeno_da_el_mismo_404_que_lo_inexistente(
    nueva_cuenta: Callable[..., CuentaPrueba], dueno: psycopg.Connection[Any], cliente: ClientePrueba
) -> None:
    a = nueva_cuenta().cliente
    b = nueva_cuenta().cliente
    ajeno = _id(_crear(b, "Retiro"))
    _id(_crear(a, "Propio"))
    antes = _portafolios(dueno)

    for portafolio_id in (ajeno, ID_INEXISTENTE):
        ruta = f"/api/portafolios/{portafolio_id}"
        respuestas = [
            a.get(ruta),
            a.patch(ruta, json={"nombre": "Mío"}),
            a.patch(ruta, json={"nombre": ""}),  # el 404 va antes que la forma del cuerpo
            _eliminar(a, portafolio_id, {"confirmacion": "Retiro"}),
            _eliminar(a, portafolio_id),
            a.get(f"{ruta}/transacciones"),
            a.post(f"{ruta}/transacciones", json={}),
        ]
        for respuesta in respuestas:
            assert respuesta.status_code == 404
            assert respuesta.content == respuestas[0].content
        assert respuestas[0].json() == NO_EXISTE_PORTAFOLIO
    assert _portafolios(dueno) == antes
    assert [p["nombre"] for p in a.get("/api/portafolios").json()] == ["Propio"]

    # Sin sesión: 401, antes que la propiedad.
    for respuesta in (
        cliente.get("/api/portafolios"),
        cliente.post("/api/portafolios", json={"nombre": "X"}),
        cliente.get(f"/api/portafolios/{ajeno}"),
        cliente.patch(f"/api/portafolios/{ajeno}", json={"nombre": "X"}),
        _eliminar(cliente, ajeno, {"confirmacion": "Retiro"}),
    ):
        assert respuesta.status_code == 401
        assert respuesta.json()["codigo"] == "sesion_requerida"
    assert _portafolios(dueno) == antes
