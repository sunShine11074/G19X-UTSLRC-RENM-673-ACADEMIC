"""CPNF-05: ninguna credencial aparece en el repositorio, el cliente compilado ni los registros (RNF-05; §8.4).

Lo ejecuta Ramon a mano, porque lee backend/.env; ninguna prueba ni ningún agente lo ejecuta.

    cd backend
    uv run python tests/inspeccion/cpnf05_credenciales.py

Qué hace, sin imprimir nunca una credencial ni dónde apareció (solo conteos):
1. Toma en memoria la contraseña de DATABASE_URL, SESION_CLAVE y BANXICO_TOKEN de backend/.env.
2. Busca cada una, como texto fijo, con `git grep -F -c -f <archivo temporal>`:
   - en todo el historial (`git rev-list --all`, por lotes);
   - en el índice y en el árbol de trabajo (sin los archivos ignorados, como backend/.env).
   El archivo temporal se borra al terminar.
3. Las busca también en frontend/dist y en los registros (*.log y tests/resultados).
4. Comprueba que git ignore backend/.env y que ningún commit lo haya incluido.

Termina con código 0 si todo cumple y con 1 si no.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from urllib.parse import unquote, urlsplit

RUTA_BACKEND = Path(__file__).resolve().parents[2]
RUTA_REPO = RUTA_BACKEND.parent
ARCHIVO_ENV = RUTA_BACKEND / ".env"
VARIABLES = ("SESION_CLAVE", "BANXICO_TOKEN")
LARGO_MINIMO = 8  # un valor más corto daría coincidencias falsas
LOTE_COMMITS = 50
CARPETAS_EXCLUIDAS = {".git", "node_modules", ".venv", "venv", "__pycache__", "6th quarter (Estadías)"}


def _leer_env(ruta: Path) -> dict[str, str]:
    """Variables de backend/.env; usa python-dotenv si está instalado."""
    try:
        from dotenv import dotenv_values
    except ImportError:
        valores: dict[str, str] = {}
        for linea in ruta.read_text(encoding="utf-8").splitlines():
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            llave, _, valor = linea.partition("=")
            valores[llave.strip()] = valor.strip().strip("'\"")
        return valores
    return {k: v for k, v in dotenv_values(ruta).items() if v is not None}


def _credenciales(variables: dict[str, str]) -> list[str]:
    """La contraseña de DATABASE_URL (codificada y sin codificar), SESION_CLAVE y BANXICO_TOKEN."""
    encontradas: list[str] = []
    url = variables.get("DATABASE_URL", "")
    if url:
        cruda = urlsplit(url).password or ""
        encontradas.extend({cruda, unquote(cruda)})
    encontradas.extend(variables.get(nombre, "") for nombre in VARIABLES)
    unicas = []
    for valor in encontradas:
        if len(valor) >= LARGO_MINIMO and "\n" not in valor and valor not in unicas:
            unicas.append(valor)
    return unicas


def _git(*argumentos: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(RUTA_REPO), *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdin=subprocess.DEVNULL,
        timeout=600,
    )


def _sumar_conteos(salida: str) -> int:
    """Suma los conteos de `git grep -c` («[rev:]ruta:conteo» por renglón)."""
    total = 0
    for renglon in salida.splitlines():
        _, _, conteo = renglon.rpartition(":")
        if conteo.isdigit():
            total += int(conteo)
    return total


def _git_grep(archivo_patrones: str, *alcance: str) -> int:
    resultado = _git("grep", "-F", "-c", "-I", "-f", archivo_patrones, *alcance)
    if resultado.returncode not in (0, 1):  # 1 = sin coincidencias
        raise RuntimeError(f"git grep terminó con el código {resultado.returncode}.")
    return _sumar_conteos(resultado.stdout)


def _lotes(elementos: list[str], tamano: int) -> Iterator[list[str]]:
    for inicio in range(0, len(elementos), tamano):
        yield elementos[inicio : inicio + tamano]


def _archivos(raiz: Path, sufijo: str = "") -> Iterator[Path]:
    """Archivos bajo `raiz` que terminan en `sufijo`, sin entrar en .git, node_modules ni .venv."""
    for carpeta, subcarpetas, nombres in os.walk(raiz):
        subcarpetas[:] = [s for s in subcarpetas if s not in CARPETAS_EXCLUIDAS]
        for nombre in nombres:
            if nombre.endswith(sufijo):
                yield Path(carpeta) / nombre


def _contar_en_archivos(archivos: Iterable[Path], credenciales: list[str]) -> tuple[int, int]:
    """(archivos revisados, coincidencias), leyendo cada archivo como bytes."""
    buscadas = [c.encode("utf-8") for c in credenciales]
    revisados = coincidencias = 0
    for ruta in archivos:
        try:
            contenido = ruta.read_bytes()
        except OSError:
            continue
        revisados += 1
        coincidencias += sum(contenido.count(b) for b in buscadas)
    return revisados, coincidencias


def main() -> int:
    if not ARCHIVO_ENV.is_file():
        print("No existe backend/.env; no hay credenciales que buscar.", file=sys.stderr)
        return 1
    credenciales = _credenciales(_leer_env(ARCHIVO_ENV))
    print(f"Credenciales buscadas: {len(credenciales)}")
    if not credenciales:
        print("backend/.env no tiene DATABASE_URL con contraseña, SESION_CLAVE ni BANXICO_TOKEN.", file=sys.stderr)
        return 1

    descriptor, archivo_patrones = tempfile.mkstemp(prefix="cpnf05_", suffix=".txt")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(credenciales) + "\n")

        commits = _git("rev-list", "--all").stdout.split()
        en_historial = sum(_git_grep(archivo_patrones, *lote) for lote in _lotes(commits, LOTE_COMMITS))
        en_indice = _git_grep(archivo_patrones, "--cached")
        en_arbol = _git_grep(archivo_patrones, "--untracked")
    finally:
        os.remove(archivo_patrones)

    dist_revisados, en_dist = _contar_en_archivos(_archivos(RUTA_REPO / "frontend" / "dist"), credenciales)
    registros = [*_archivos(RUTA_REPO, ".log"), *_archivos(RUTA_BACKEND / "tests" / "resultados")]
    registros_revisados, en_registros = _contar_en_archivos(registros, credenciales)

    env_ignorado = _git("check-ignore", "-q", "backend/.env").returncode == 0
    commits_con_env = len(_git("log", "--all", "--format=%H", "--", "backend/.env").stdout.split())

    print(f"Coincidencias en el historial de git ({len(commits)} commits): {en_historial}")
    print(f"Coincidencias en el índice: {en_indice}")
    print(f"Coincidencias en el árbol de trabajo (sin ignorados): {en_arbol}")
    print(f"Coincidencias en frontend/dist ({dist_revisados} archivos): {en_dist}")
    print(f"Coincidencias en los registros ({registros_revisados} archivos): {en_registros}")
    print(f"backend/.env ignorado por git: {'sí' if env_ignorado else 'no'}")
    print(f"Commits que incluyen backend/.env: {commits_con_env}")

    cumple = (
        en_historial == en_indice == en_arbol == en_dist == en_registros == 0 and env_ignorado and commits_con_env == 0
    )
    print(f"CPNF-05: {'cumple' if cumple else 'NO cumple'}")
    return 0 if cumple else 1


if __name__ == "__main__":
    sys.exit(main())
