"""Fecha y hora de la Ciudad de México (RD-15; §3.3).

`hoy_cdmx` y `ahora_epoch` son dependencias de FastAPI: las pruebas las sustituyen con
`app.dependency_overrides` (fixture `reloj`).
"""

import time
from datetime import date, datetime
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("America/Mexico_City")  # tzdata llega con psycopg en win32 (D-31)


def hoy_cdmx() -> date:
    """Fecha de hoy en la Ciudad de México."""
    return datetime.now(ZONA).date()


def ahora_epoch() -> int:
    """Segundos de época UTC, enteros."""
    return int(time.time())


def momento_iso(dt: datetime) -> str:
    """Momento en ISO 8601 con el desfase de la Ciudad de México, p. ej. 2026-10-16T00:00:00-06:00."""
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("El momento no tiene zona horaria.")
    return dt.astimezone(ZONA).isoformat()


def epoch_iso(s: int) -> str:
    """Segundos de época en ISO 8601 con el desfase de la Ciudad de México, sin fracción."""
    return datetime.fromtimestamp(s, ZONA).isoformat(timespec="seconds")
