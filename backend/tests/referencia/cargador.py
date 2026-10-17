"""Carga el conjunto de referencia (5.2) por la API, como lo haría un usuario (CPNF-01 nivel 2; AC-04).

Lo usan las pruebas de la API y de referencia con un `TestClient`, y sirve para preparar la
demostración de AC-04 contra la API en marcha:

    cd backend
    uv run python -m tests.referencia.cargador --url http://localhost:8000 --origen http://localhost:5173

La contraseña de la cuenta de demostración se pide sin mostrarla y nunca se imprime (RNF-05).
Las transacciones T01 a T16 se registran en el orden de `ref`, con las cifras como texto, y
cada una debe dar 201 con el costo o ingreso por título de `esperados/` (RF-05 crit. 1).
"""

from __future__ import annotations

import argparse
import getpass
import sys
from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import httpx

from app.motor import presentar_por_titulo
from tests.comparacion_5_2 import leer_csv

CORREO_ORACULO = "oraculo@example.com"  # usuarios.csv (datos ficticios, S-04)


class ErrorCarga(AssertionError):
    """La API no respondió lo que 5.2 espera; el mensaje no lleva contraseñas ni cookies."""


@dataclass(frozen=True)
class Escenario52:
    """Ids que asignó la base al cargar 5.2 por la API, por llave natural."""

    cliente: httpx.Client  # con la sesión de la cuenta del oráculo
    portafolios: dict[str, int]  # nombre → id
    intermediarios: dict[str, int]  # nombre → id
    instrumentos: dict[str, int]  # clave → id
    refs: dict[str, int]  # T01 a T16 → id de la transacción
    vistas: dict[str, dict[str, Any]]  # T01 a T16 → TransaccionVista de E18


def _exigir(respuesta: httpx.Response, estado: int, que: str) -> Any:
    if respuesta.status_code != estado:
        try:
            codigo = respuesta.json().get("codigo")
        except ValueError:
            codigo = None
        raise ErrorCarga(f"{que}: se esperaba {estado} y la API respondió {respuesta.status_code} ({codigo}).")
    return respuesta.json() if respuesta.content else None


def abrir_cuenta(cliente: httpx.Client, correo: str, contrasena: str) -> None:
    """Registra la cuenta con el aviso vigente (E02, E03) e inicia sesión (E04); la cookie queda en el cliente."""
    aviso = _exigir(cliente.get("/api/aviso-privacidad"), 200, "E02")
    _exigir(
        cliente.post(
            "/api/cuentas",
            json={"correo": correo, "contrasena": contrasena, "consentimiento": True, "version_aviso_id": aviso["id"]},
        ),
        201,
        "E03",
    )
    _exigir(cliente.post("/api/sesion", json={"correo": correo, "contrasena": contrasena}), 200, "E04")


def cuerpo_transaccion(
    fila: dict[str, str], intermediarios: dict[str, int], instrumentos: dict[str, int]
) -> dict[str, Any]:
    """Cuerpo de E18 para un renglón de `transacciones.csv` o `rechazos_rf28.csv`; cifras como texto (RD-12)."""
    return {
        "intermediario_id": intermediarios[fila["intermediario_nombre"]],
        "instrumento_id": instrumentos[fila["instrumento_clave"]],
        "tipo": fila["tipo"],
        "fecha_concertacion": fila["fecha_concertacion"],
        "cantidad": fila["cantidad"],
        "precio": fila["precio"],
        "importe_comisiones": fila["importe_comisiones"],
    }


def cargar_5_2(cliente: httpx.Client) -> Escenario52:
    """Crea los portafolios y los intermediarios de 5.2 y registra T01 a T16 con la sesión del cliente."""
    portafolios = {
        f["nombre"]: _exigir(
            cliente.post("/api/portafolios", json={"nombre": f["nombre"], "divisa_base": f["divisa_base"]}),
            201,
            f"E13 {f['nombre']}",
        )["id"]
        for f in leer_csv("portafolios", "entradas")
    }
    intermediarios = {
        f["nombre"]: _exigir(
            cliente.post("/api/intermediarios", json={"nombre": f["nombre"]}), 201, f"E11 {f['nombre']}"
        )["id"]
        for f in leer_csv("intermediarios", "entradas")
    }
    instrumentos = {i["clave"]: i["id"] for i in _exigir(cliente.get("/api/instrumentos"), 200, "E08")}
    esperados = {f["ref"]: f for f in leer_csv("transacciones")}

    refs: dict[str, int] = {}
    vistas: dict[str, dict[str, Any]] = {}
    for fila in sorted(leer_csv("transacciones", "entradas"), key=lambda f: f["ref"]):
        ref = fila["ref"]
        vista = _exigir(
            cliente.post(
                f"/api/portafolios/{portafolios[fila['portafolio_nombre']]}/transacciones",
                json=cuerpo_transaccion(fila, intermediarios, instrumentos),
            ),
            201,
            f"E18 {ref}",
        )
        columna = "costo_por_titulo" if fila["tipo"] == "compra" else "ingreso_por_titulo"
        esperado = presentar_por_titulo(Decimal(esperados[ref][columna]))
        if vista[columna] != esperado:
            raise ErrorCarga(f"{ref}: {columna} = {vista[columna]!r}; se esperaba {esperado!r} (RF-05 crit. 1).")
        refs[ref] = int(vista["id"])
        vistas[ref] = vista
    return Escenario52(
        cliente=cliente,
        portafolios=portafolios,
        intermediarios=intermediarios,
        instrumentos=instrumentos,
        refs=refs,
        vistas=vistas,
    )


def main(
    argumentos: list[str] | None = None,
    *,
    abrir_cliente: Callable[..., httpx.Client] = httpx.Client,
    pedir_contrasena: Callable[[str], str] = getpass.getpass,
) -> int:
    """Carga 5.2 en la API en marcha (demostración de AC-04); imprime solo conteos.

    `abrir_cliente` y `pedir_contrasena` solo se sustituyen en las pruebas.
    """
    parser = argparse.ArgumentParser(description="Carga el conjunto de referencia (5.2) por la API.")
    parser.add_argument("--url", default="http://localhost:8000", help="URL base de la API")
    parser.add_argument("--origen", default="http://localhost:5173", help="un origen de CORS_ORIGINS")
    parser.add_argument("--correo", default=CORREO_ORACULO, help="correo de la cuenta de demostración")
    opciones = parser.parse_args(argumentos)
    contrasena = pedir_contrasena("Contraseña para la cuenta de demostración (15 caracteres o más; no se muestra): ")
    with abrir_cliente(base_url=opciones.url, headers={"Origin": opciones.origen}, timeout=60) as cliente:
        try:
            abrir_cuenta(cliente, opciones.correo, contrasena)
            escenario = cargar_5_2(cliente)
        except ErrorCarga as error:
            print(f"No se completó la carga: {error}", file=sys.stderr)
            return 1
    print(
        f"Listo: {len(escenario.refs)} transacciones, {len(escenario.portafolios)} portafolios y "
        f"{len(escenario.intermediarios)} intermediarios para {opciones.correo}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
