"""Aislamiento del motor único: análisis con `ast` de `app/motor` (RNF-10; AC-03; RD-12; §5.1 del diseño).

- Solo importa la biblioteca estándar permitida y sus propios módulos.
- No usa `float(`, literales de punto flotante, `round(`, `getcontext` ni modifica el contexto global.
- No menciona el oráculo ni sus archivos (el motor es independiente de 5.2).
- Toda función pública lleva `@calculo`.
"""

import ast
import json
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

pytestmark = pytest.mark.motor

RUTA_BACKEND = Path(__file__).resolve().parents[2]
RUTA_MOTOR = RUTA_BACKEND / "app" / "motor"

MODULOS_DISENO = {
    "__init__", "contexto", "modelos", "errores", "mercado", "importes",
    "kardex", "cetes", "valuacion", "serie", "presentacion",
}
IMPORTACIONES_PERMITIDAS = {
    "decimal", "datetime", "dataclasses", "typing", "collections.abc",
    "bisect", "enum", "functools", "itertools",
}
LLAMADAS_PROHIBIDAS = {"float", "round", "open", "eval", "exec", "compile", "__import__"}
NOMBRES_PROHIBIDOS = {"getcontext", "setcontext", "DefaultContext", "from_float"}
TEXTOS_PROHIBIDOS = (
    "oraculo", "esperados", "calcula_oraculo", "compara_vias", "genera_libro", "chequeo_diseno", "xlsx", "tests",
)
BASES_EXENTAS = {"Protocol", "Exception", "StrEnum", "Enum"}


def _archivos() -> list[Path]:
    return sorted(RUTA_MOTOR.glob("*.py"))


def _arbol(ruta: Path) -> ast.Module:
    return ast.parse(ruta.read_text(encoding="utf-8"), filename=str(ruta))


def _nombre(nodo: ast.expr) -> str | None:
    if isinstance(nodo, ast.Name):
        return nodo.id
    if isinstance(nodo, ast.Attribute):
        return nodo.attr
    if isinstance(nodo, ast.Call):
        return _nombre(nodo.func)
    return None


def _sin_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def test_estan_los_modulos_del_diseno() -> None:
    assert MODULOS_DISENO <= {ruta.stem for ruta in _archivos()}


@pytest.mark.parametrize("ruta", _archivos(), ids=lambda r: r.name)
def test_solo_importa_la_biblioteca_estandar_permitida(ruta: Path) -> None:
    for nodo in ast.walk(_arbol(ruta)):
        if isinstance(nodo, ast.Import):
            for alias in nodo.names:
                assert alias.name in IMPORTACIONES_PERMITIDAS or alias.name.startswith("app.motor"), (
                    f"{ruta.name}:{nodo.lineno} importa {alias.name}"
                )
        elif isinstance(nodo, ast.ImportFrom):
            if nodo.level >= 1:  # importación relativa: solo dentro de app.motor
                assert nodo.level == 1, f"{ruta.name}:{nodo.lineno} sale de app.motor"
                continue
            modulo = nodo.module or ""
            assert modulo in IMPORTACIONES_PERMITIDAS or modulo.startswith("app.motor"), (
                f"{ruta.name}:{nodo.lineno} importa {modulo}"
            )


@pytest.mark.parametrize("ruta", _archivos(), ids=lambda r: r.name)
def test_sin_punto_flotante_round_ni_contexto_global(ruta: Path) -> None:
    for nodo in ast.walk(_arbol(ruta)):
        if isinstance(nodo, ast.Constant):
            assert not isinstance(nodo.value, float | complex), f"{ruta.name}:{nodo.lineno} literal {nodo.value!r}"
        if isinstance(nodo, ast.Call) and isinstance(nodo.func, ast.Name):
            assert nodo.func.id not in LLAMADAS_PROHIBIDAS, f"{ruta.name}:{nodo.lineno} llama a {nodo.func.id}("
        if isinstance(nodo, ast.Name):
            assert nodo.id not in NOMBRES_PROHIBIDOS, f"{ruta.name}:{nodo.lineno} usa {nodo.id}"
        if isinstance(nodo, ast.Attribute):
            assert nodo.attr not in NOMBRES_PROHIBIDOS, f"{ruta.name}:{nodo.lineno} usa .{nodo.attr}"
        if isinstance(nodo, ast.alias):
            assert nodo.name not in NOMBRES_PROHIBIDOS, f"{ruta.name} importa {nodo.name}"


@pytest.mark.parametrize("ruta", _archivos(), ids=lambda r: r.name)
def test_no_menciona_el_oraculo(ruta: Path) -> None:
    texto = _sin_acentos(ruta.read_text(encoding="utf-8")).lower()
    for prohibido in TEXTOS_PROHIBIDOS:
        assert prohibido not in texto, f"{ruta.name} menciona «{prohibido}»"


def _clases_exentas(arbol: ast.Module) -> set[str]:
    """Dataclasses, protocolos, enumeraciones y excepciones: no calculan en sus métodos públicos."""
    exentas: set[str] = set()
    excepciones = {"Exception"}
    for nodo in arbol.body:
        if not isinstance(nodo, ast.ClassDef):
            continue
        bases = {_nombre(b) for b in nodo.bases}
        if bases & excepciones:
            excepciones.add(nodo.name)
        es_dataclass = any(_nombre(d) == "dataclass" for d in nodo.decorator_list)
        if es_dataclass or bases & (BASES_EXENTAS | excepciones | {"ErrorMotor"}):
            exentas.add(nodo.name)
    return exentas


@pytest.mark.parametrize("ruta", _archivos(), ids=lambda r: r.name)
def test_toda_funcion_publica_lleva_calculo(ruta: Path) -> None:
    arbol = _arbol(ruta)
    exentas = _clases_exentas(arbol)
    sin_calculo: list[str] = []
    for nodo in arbol.body:
        if isinstance(nodo, ast.FunctionDef | ast.AsyncFunctionDef):
            if nodo.name.startswith("_") or (ruta.stem == "contexto" and nodo.name == "calculo"):
                continue
            if "calculo" not in {_nombre(d) for d in nodo.decorator_list}:
                sin_calculo.append(nodo.name)
        elif isinstance(nodo, ast.ClassDef):
            for metodo in nodo.body:
                if not isinstance(metodo, ast.FunctionDef | ast.AsyncFunctionDef) or metodo.name.startswith("_"):
                    continue
                decoradores = {_nombre(d) for d in metodo.decorator_list}
                if nodo.name in exentas:
                    # En dataclasses y protocolos solo se admiten propiedades o firmas sin cálculo.
                    es_protocolo = "Protocol" in {_nombre(b) for b in nodo.bases}
                    assert es_protocolo or "property" in decoradores, f"{ruta.name}: {nodo.name}.{metodo.name}"
                elif "calculo" not in decoradores:
                    sin_calculo.append(f"{nodo.name}.{metodo.name}")
    assert not sin_calculo, f"{ruta.name}: sin @calculo: {sin_calculo}"


def test_importar_el_motor_no_carga_paquetes_externos() -> None:
    """En un intérprete aislado, `import app.motor` solo carga la biblioteca estándar (RNF-10)."""
    programa = (
        "import json, sys\n"
        "antes = set(sys.modules)\n"
        "import app.motor\n"
        "nuevos = sorted(set(sys.modules) - antes)\n"
        "externos = [n for n in nuevos if 'site-packages' in (getattr(sys.modules[n], '__file__', None) or '')]\n"
        "print(json.dumps({'nuevos': nuevos, 'externos': externos}))\n"
    )
    salida = subprocess.run(
        [sys.executable, "-I", "-c", f"import sys; sys.path.insert(0, {str(RUTA_BACKEND)!r})\n{programa}"],
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    )
    resultado = json.loads(salida.stdout)
    assert resultado["externos"] == []
    propios = [n for n in resultado["nuevos"] if n == "app" or n.startswith("app.")]
    assert all(n == "app" or n.startswith("app.motor") for n in propios), propios
