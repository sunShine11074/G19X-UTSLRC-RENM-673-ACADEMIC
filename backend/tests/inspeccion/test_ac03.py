"""AC-03: el motor es independiente del oráculo de 5.2 (§8.4; nota c.3 del borrador de 5.2).

Marca «inspeccion»: no corre por omisión. Se ejecuta con

    uv run --directory backend pytest -m inspeccion tests/inspeccion/test_ac03.py

Comprueba con git, sin modificar nada:
- el commit que congeló el oráculo (11097f8) es ancestro de HEAD;
- en ese commit todavía no existía `backend/app/motor`, así que el motor se programó después;
- `backend/tests/oraculo` no cambió desde ese commit.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.inspeccion

RUTA_REPO = Path(__file__).resolve().parents[3]
COMMIT_ORACULO = "11097f8"
RUTA_ORACULO = "backend/tests/oraculo"


def _git(*argumentos: str) -> subprocess.CompletedProcess[str]:
    if shutil.which("git") is None:
        pytest.fail("No se encontró git en el PATH.", pytrace=False)
    return subprocess.run(
        ["git", "-C", str(RUTA_REPO), *argumentos],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        stdin=subprocess.DEVNULL,
    )


def test_el_oraculo_congelado_es_ancestro_de_head() -> None:
    assert _git("cat-file", "-e", f"{COMMIT_ORACULO}^{{commit}}").returncode == 0, "No existe el commit del oráculo."
    assert _git("merge-base", "--is-ancestor", COMMIT_ORACULO, "HEAD").returncode == 0


def test_el_motor_no_existia_al_congelar_el_oraculo() -> None:
    archivos = _git("ls-tree", "-r", "--name-only", COMMIT_ORACULO)
    assert archivos.returncode == 0
    lista = archivos.stdout.splitlines()
    assert f"{RUTA_ORACULO}/esperados/indicadores.csv" in lista  # el oráculo sí estaba
    assert not [a for a in lista if a.startswith("backend/app/motor")]


def test_el_oraculo_no_cambio_desde_que_se_congelo() -> None:
    diferencia = _git("diff", "--quiet", COMMIT_ORACULO, "--", RUTA_ORACULO)
    assert diferencia.returncode == 0, "backend/tests/oraculo cambió desde 11097f8 (RD-21; AC-03)."
