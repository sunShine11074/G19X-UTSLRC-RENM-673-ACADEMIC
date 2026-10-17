"""CPNF-01, nivel 2: la base y el servicio de cálculo contra el conjunto de referencia de 5.2 (RNF-01; §8.4).

1. Las semillas que cargó 04 son las entradas del oráculo, por llave natural y con `Decimal`.
2. 5.2 se carga por la API (`cargador.py`): cuenta, portafolios, intermediarios y T01 a T16,
   cada una con 201 y el costo o ingreso por título de `esperados/`.
3. Con `cargar_historial` y `cargar_mercado` desde la base, como app_077 (la ruta de cálculo de
   E19 y E20), las cifras de los 7 archivos de `esperados/` quedan dentro de tolerancia.
4. N1 a N6 por E18 y N7 y N8 por E20 dan el código y los datos de §4.4; quedan 16
   transacciones, y al recalcular todo sale idéntico.
5. C1: T11 y T12 se aceptaron (compras antes que ventas).
6. Corre sin red (anticipo de RNF-08).
7. Evidencia: cpnf01_diferencias.csv, cpnf01_resumen.csv y cpnf01_versiones.csv en la carpeta de
   resultados (tests/resultados/AAAA-MM-DD/ con --registro-resultados; si no, una temporal).
"""

from __future__ import annotations

import csv
import secrets
import subprocess
from collections.abc import Callable
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import httpx
import psycopg
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.datos.consultas import cargar_historial, intervalo_semillas, leer_instrumentos
from app.datos.mercado_sql import cargar_mercado
from tests.comparacion_5_2 import ARCHIVOS_ESPERADOS, Comparador, comparar_5_2, leer_csv
from tests.conftest import ORIGEN_PRUEBAS, RUTA_BACKEND, URL_BASE_PRUEBAS, CuentaPrueba
from tests.referencia import cargador
from tests.referencia.cargador import CORREO_ORACULO, Escenario52, cargar_5_2, cuerpo_transaccion

pytestmark = [pytest.mark.bd, pytest.mark.referencia]

HOY = date(2026, 10, 16)
COMMIT_ORACULO = "11097f8"
CODIGO_POR_REGLA = {
    "criterio 3 de RF-09: fecha final anterior a la inicial": "periodo_invertido",
    "criterio 3 de RF-09: fechas fuera de las semillas": "periodo_fuera_de_intervalo",
}


# ---------------------------------------------------------------------------
# 1. Las semillas son las entradas
# ---------------------------------------------------------------------------


def _filas(dueno: psycopg.Connection[Any], consulta: str) -> list[tuple[Any, ...]]:
    return [tuple(f) for f in dueno.execute(consulta).fetchall()]


def _nulo(texto: str) -> str | None:
    return texto or None


def _booleano(texto: str) -> bool:
    assert texto in ("true", "false"), texto
    return texto == "true"


@pytest.mark.usefixtures("bd_limpia")
def test_semillas_son_las_entradas(dueno: psycopg.Connection[Any]) -> None:
    # Instrumentos y emisiones de CETES.
    en_base = {
        f[0]: f[1:]
        for f in _filas(
            dueno,
            "SELECT i.clave, i.nombre, i.clase_activo, i.divisa, i.de_demostracion, e.vencimiento, e.valor_nominal "
            "FROM instrumento i LEFT JOIN emision_cetes e ON e.instrumento_id = i.id",
        )
    }
    entradas = {
        f["clave"]: (
            f["nombre"],
            f["clase_activo"],
            f["divisa"],
            _booleano(f["de_demostracion"]),
            date.fromisoformat(f["vencimiento"]) if f["vencimiento"] else None,
            Decimal(f["valor_nominal"]) if f["valor_nominal"] else None,
        )
        for f in leer_csv("instrumentos", "entradas")
    }
    assert en_base == entradas

    # Fuentes y versiones de licencia.
    assert {
        f[0]: f[1:] for f in _filas(dueno, "SELECT nombre, direccion, de_demostracion FROM fuente_datos")
    } == {
        f["nombre"]: (_nulo(f["direccion"]), _booleano(f["de_demostracion"]))
        for f in leer_csv("fuentes_datos", "entradas")
    }
    assert {
        (f[0], f[1]): f[2:]
        for f in _filas(
            dueno,
            "SELECT d.nombre, l.version, l.usos_permitidos, l.obligacion_suprimir, l.atribucion "
            "FROM version_licencia l JOIN fuente_datos d ON d.id = l.fuente_id",
        )
    } == {
        (f["fuente_nombre"], f["version"]): (
            f["usos_permitidos"],
            _nulo(f["obligacion_suprimir"]),
            _nulo(f["atribucion"]),
        )
        for f in leer_csv("versiones_licencia", "entradas")
    }

    # Cargas: resultado «completa» = 'exitosa' y valores_sustituidos {} = []; obtenida_en no se compara (04).
    cargas_base = {
        (f[0], f[1], f[2], f[3]): f[4:]
        for f in _filas(
            dueno,
            "SELECT d.nombre, l.version, c.fecha_inicial, c.fecha_final, c.origen, c.resultado, "
            "c.observaciones_incorporadas, c.observaciones_omitidas, c.valores_sustituidos "
            "FROM carga_datos c JOIN fuente_datos d ON d.id = c.fuente_id "
            "JOIN version_licencia l ON l.id = c.version_licencia_id",
        )
    }
    cargas_entradas = leer_csv("cargas_datos", "entradas")
    assert cargas_base == {
        (
            f["fuente_nombre"],
            f["version"],
            date.fromisoformat(f["fecha_inicial"]),
            date.fromisoformat(f["fecha_final"]),
        ): (
            f["origen"],
            {"completa": "exitosa"}[f["resultado"]],
            int(f["observaciones_incorporadas"]),
            int(f["observaciones_omitidas"]),
            [] if f["valores_sustituidos"] == "{}" else f["valores_sustituidos"],
        )
        for f in cargas_entradas
    }
    carga_por_nombre = {f["carga"]: (f["fuente_nombre"], f["fecha_inicial"], f["fecha_final"]) for f in cargas_entradas}

    # Precios: el mismo Decimal y el mismo texto (RD-14), con su fuente y su carga.
    precios_base = {
        (f[0], f[1]): f[2:]
        for f in _filas(
            dueno,
            "SELECT i.clave, p.fecha, p.precio, d.nombre, dc.nombre, c.fecha_inicial, c.fecha_final "
            "FROM precio_cierre p JOIN instrumento i ON i.id = p.instrumento_id "
            "JOIN carga_datos c ON c.id = p.carga_id JOIN fuente_datos d ON d.id = p.fuente_id "
            "JOIN fuente_datos dc ON dc.id = c.fuente_id",
        )
    }
    precios_entradas = leer_csv("precios", "entradas")
    assert set(precios_base) == {(f["instrumento_clave"], date.fromisoformat(f["fecha"])) for f in precios_entradas}
    for f in precios_entradas:
        llave = (f["instrumento_clave"], date.fromisoformat(f["fecha"]))
        precio, fuente, fuente_carga, inicial, final = precios_base[llave]
        assert (precio, format(precio, "f"), fuente) == (Decimal(f["precio"]), f["precio"], f["fuente_nombre"]), f
        nombre, inicial_csv, final_csv = carga_por_nombre[f["carga"]]
        assert (fuente_carga, inicial.isoformat(), final.isoformat()) == (nombre, inicial_csv, final_csv), f

    # Tasas: por plazo y fecha de colocación, con su fuente (la de su carga).
    tasas_base = {
        (f[0], f[1]): f[2:]
        for f in _filas(
            dueno,
            "SELECT t.plazo_nominal, t.fecha_colocacion, t.valor, t.unidad, t.plazo_efectivo, d.nombre "
            "FROM tasa_referencia t JOIN carga_datos c ON c.id = t.carga_id JOIN fuente_datos d ON d.id = c.fuente_id",
        )
    }
    tasas_entradas = {
        (int(f["plazo_nominal"]), date.fromisoformat(f["fecha_colocacion"])): f for f in leer_csv("tasas", "entradas")
    }
    assert tasas_base == {
        llave: (Decimal(f["valor"]), f["unidad"], int(f["plazo_efectivo"]), f["fuente_nombre"])
        for llave, f in tasas_entradas.items()
    }
    assert {llave: format(v[0], "f") for llave, v in tasas_base.items()} == {
        llave: f["valor"] for llave, f in tasas_entradas.items()
    }


# ---------------------------------------------------------------------------
# 2 a 7. Carga por la API, cálculo, rechazos y evidencia
# ---------------------------------------------------------------------------


def _calcular(app: FastAPI, usuario_id: int, e: Escenario52) -> Comparador:
    """La ruta de cálculo de E19 y E20, desde la base como app_077, contra `esperados/`."""
    with app.state.fabrica_sesiones() as sesion:
        historiales = {nombre: cargar_historial(sesion, usuario_id, pid) for nombre, pid in e.portafolios.items()}
        ids = {i for h in historiales.values() for i in h.instrumentos}
        mercado = cargar_mercado(sesion, ids, intervalo_semillas(sesion).fin)
        claves = {i: r.clave for i, r in leer_instrumentos(sesion).items()}
    nombres = {i: nombre for nombre, i in e.intermediarios.items()}
    return comparar_5_2(historiales, mercado, claves, nombres, e.refs)


def _transacciones_en_base(dueno: psycopg.Connection[Any], usuario_id: int) -> dict[int, tuple[Any, ...]]:
    return {
        f[0]: (*f[1:5], f[5].isoformat(), *f[6:])
        for f in dueno.execute(
            "SELECT t.id, p.nombre, m.nombre, i.clave, t.tipo, t.fecha_concertacion, t.cantidad::text, "
            "t.precio::text, t.importe_comisiones::text FROM transaccion t "
            "JOIN portafolio p ON p.id = t.portafolio_id JOIN intermediario m ON m.id = t.intermediario_id "
            "JOIN instrumento i ON i.id = t.instrumento_id WHERE t.usuario_id = %s",
            (usuario_id,),
        ).fetchall()
    }


def _git(*argumentos: str) -> str:
    try:
        resultado = subprocess.run(
            ["git", *argumentos], capture_output=True, text=True, timeout=60, cwd=RUTA_BACKEND, stdin=subprocess.DEVNULL
        )
    except (OSError, subprocess.SubprocessError):
        return "no disponible"
    return resultado.stdout.strip() if resultado.returncode == 0 else "no disponible"


def _escribir_versiones(carpeta: Path) -> None:
    """Hashes de HEAD y del commit que congeló el oráculo (D-32)."""
    with (carpeta / "cpnf01_versiones.csv").open("w", encoding="utf-8", newline="") as fh:
        escritor = csv.writer(fh)
        escritor.writerow(["referencia", "commit"])
        escritor.writerow(["HEAD", _git("rev-parse", "HEAD")])
        escritor.writerow([COMMIT_ORACULO, _git("rev-parse", f"{COMMIT_ORACULO}^{{commit}}")])


def _huella_texto(c: httpx.Client, e: Escenario52) -> list[bytes]:
    """Texto de E19 y E20 por omisión de cada portafolio."""
    textos = []
    for pid in e.portafolios.values():
        for ruta in (f"/api/portafolios/{pid}/posiciones", f"/api/portafolios/{pid}/tablero"):
            respuesta = c.get(ruta)
            assert respuesta.status_code == 200, (ruta, respuesta.status_code)
            textos.append(respuesta.content)
    return textos


@pytest.mark.usefixtures("sin_red", "bd_limpia")
def test_cpnf01_nivel_2(
    nueva_cuenta: Callable[..., CuentaPrueba],
    dueno: psycopg.Connection[Any],
    reloj: Any,
    app_pruebas: FastAPI,
    carpeta_resultados: Path,
) -> None:
    reloj.fijar_hoy(HOY)

    # 2. Carga por la API, en el orden de ref (cada una 201 con su costo o ingreso por título).
    cuenta = nueva_cuenta(CORREO_ORACULO)
    e = cargar_5_2(cuenta.cliente)
    c = e.cliente
    assert sorted(e.refs) == [f"T{n:02d}" for n in range(1, 17)]
    en_base = _transacciones_en_base(dueno, cuenta.usuario_id)
    assert en_base == {
        e.refs[f["ref"]]: (
            f["portafolio_nombre"],
            f["intermediario_nombre"],
            f["instrumento_clave"],
            f["tipo"],
            f["fecha_concertacion"],
            f["cantidad"],
            f["precio"],
            f["importe_comisiones"],
        )
        for f in leer_csv("transacciones", "entradas")
    }

    # 3. Cálculo desde la base: los 7 archivos de esperados/ dentro de tolerancia.
    comparador = _calcular(app_pruebas, cuenta.usuario_id, e)
    comparador.escribir(carpeta_resultados)
    _escribir_versiones(carpeta_resultados)
    for archivo in ("cpnf01_diferencias.csv", "cpnf01_resumen.csv", "cpnf01_versiones.csv"):
        assert (carpeta_resultados / archivo).is_file(), archivo
    por_archivo: dict[str, set[str]] = {}
    for d in comparador.diferencias:
        por_archivo.setdefault(d.archivo, set()).add(d.llave)
    for archivo in ARCHIVOS_ESPERADOS:
        assert len(por_archivo.get(archivo, set())) == len(leer_csv(archivo)), archivo
    comparador.verificar()
    textos_antes = _huella_texto(c, e)

    # 4. Rechazos de §4.4: N1 a N6 por E18 y N7 y N8 por E20; ninguno registra nada.
    rechazos = {f["id"]: f for f in leer_csv("rechazos_rf28", "")}
    assert sorted(rechazos) == [f"N{n}" for n in range(1, 9)]
    for ref, f in sorted(rechazos.items()):
        portafolio = e.portafolios[f["portafolio_nombre"]]
        if f["caso"] == "periodo":
            periodo = {"inicio": f["periodo_inicio"], "fin": f["periodo_fin"]}
            respuesta = c.get(f"/api/portafolios/{portafolio}/tablero", params=periodo)
            assert (respuesta.status_code, respuesta.json()["codigo"]) == (422, CODIGO_POR_REGLA[f["regla"]]), ref
            assert respuesta.json()["regla"] == "RF-09", ref
            continue
        respuesta = c.post(
            f"/api/portafolios/{portafolio}/transacciones", json=cuerpo_transaccion(f, e.intermediarios, e.instrumentos)
        )
        cuerpo = respuesta.json()
        if f["fecha_saldo_negativo"]:  # N1 a N3 (RF-28)
            assert (respuesta.status_code, cuerpo["codigo"], cuerpo["regla"]) == (409, "saldo_negativo", "RF-28"), ref
            assert cuerpo["datos"] == {
                "fecha_saldo_negativo": f["fecha_saldo_negativo"],
                "saldo_resultante": f["saldo_resultante"],
            }, ref
        elif "RF-26a" in f["regla"]:  # N4
            assert (respuesta.status_code, cuerpo["codigo"]) == (422, "fecha_en_o_despues_del_vencimiento"), ref
        else:  # N5 y N6 (RD-07 y criterio 3 de RF-05)
            assert "RD-07" in f["regla"], ref
            assert (respuesta.status_code, cuerpo["codigo"], cuerpo["regla"]) == (
                422,
                "fecha_fuera_de_intervalo",
                "RD-07",
            ), ref
    fila = dueno.execute("SELECT count(*) FROM transaccion").fetchone()
    assert fila is not None and fila[0] == 16
    assert _transacciones_en_base(dueno, cuenta.usuario_id) == en_base

    # Se recalcula todo: idéntico, cifra por cifra y en el texto de E19 y E20.
    recalculado = _calcular(app_pruebas, cuenta.usuario_id, e)
    assert [(d.archivo, d.llave, d.columna, d.obtenido) for d in recalculado.diferencias] == [
        (d.archivo, d.llave, d.columna, d.obtenido) for d in comparador.diferencias
    ]
    assert _huella_texto(c, e) == textos_antes

    # 5. C1: T11 y T12 se aceptaron; el saldo de DEMOETF con Casa B queda en 100 + 60 − 120 = 40.
    positivo = leer_csv("casos_positivos", "")[0]
    assert positivo["refs"] == "T11 y T12" and {"T11", "T12"} <= set(e.refs)
    al_25 = c.get(
        f"/api/portafolios/{e.portafolios[positivo['portafolio_nombre']]}/posiciones",
        params={"fecha_corte": positivo["fecha_concertacion"]},
    )
    assert al_25.status_code == 200
    titulos = {p["instrumento"]["clave"]: p["titulos"] for p in al_25.json()["posiciones"]}
    assert titulos[positivo["instrumento_clave"]] == positivo["saldo_resultante"] == "40"


@pytest.mark.usefixtures("bd_limpia")
def test_cargador_por_linea_de_comandos(
    app_pruebas: FastAPI, dueno: psycopg.Connection[Any], reloj: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    """El modo de la demostración de AC-04 carga lo mismo y nunca imprime la contraseña."""
    reloj.fijar_hoy(HOY)
    contrasena = secrets.token_urlsafe(18)

    def abrir(**opciones: Any) -> httpx.Client:
        assert opciones == {"base_url": URL_BASE_PRUEBAS, "headers": {"Origin": ORIGEN_PRUEBAS}, "timeout": 60}
        return TestClient(app_pruebas, base_url=opciones["base_url"], headers=opciones["headers"])

    assert cargador.main([], abrir_cliente=abrir, pedir_contrasena=lambda _: contrasena) == 0
    salida = capsys.readouterr()
    assert salida.out.strip() == (
        f"Listo: 16 transacciones, 2 portafolios y 2 intermediarios para {CORREO_ORACULO}."
    )
    fila = dueno.execute("SELECT count(*) FROM transaccion").fetchone()
    assert fila is not None and fila[0] == 16

    # Otra vez con la misma cuenta: E03 da 409 y no se registra nada más.
    assert cargador.main([], abrir_cliente=abrir, pedir_contrasena=lambda _: contrasena) == 1
    repetida = capsys.readouterr()
    assert "E03: se esperaba 201 y la API respondió 409 (correo_registrado)" in repetida.err
    assert contrasena not in salida.out + salida.err + repetida.out + repetida.err
    fila = dueno.execute("SELECT count(*) FROM transaccion").fetchone()
    assert fila is not None and fila[0] == 16
