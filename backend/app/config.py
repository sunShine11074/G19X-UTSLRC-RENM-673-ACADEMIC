"""Configuración de la aplicación, leída de variables de entorno o de backend/.env (§3.1; §6.7).

Nunca se imprime ni se registra un objeto Settings (RNF-05). No hay una instancia
global: la crea `crear_app` (app.main) y la guarda en `app.state.config`.
"""

import re
from pathlib import Path

from fastapi import Request
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RUTA_BACKEND = Path(__file__).resolve().parents[1]

# Origen exacto: esquema, host y puerto opcional; sin «*», ruta ni barra final (D-42).
_PATRON_ORIGEN = re.compile(r"https?://[A-Za-z0-9.-]+(:[0-9]{1,5})?")
_LARGO_MINIMO_CLAVE = 32


def _separar_origenes(valor: str) -> list[str]:
    return [o.strip() for o in valor.split(",") if o.strip()]


class Settings(BaseSettings):
    """Variables de la aplicación. `hide_input_in_errors` evita que un error repita un secreto."""

    model_config = SettingsConfigDict(
        env_file=RUTA_BACKEND / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: SecretStr  # DATABASE_URL, obligatoria; rol app_077, nunca postgres
    cors_origins: str = "http://localhost:5173"  # CORS_ORIGINS, separados por coma
    sesion_clave: SecretStr  # SESION_CLAVE, obligatoria y sin valor por omisión
    sesion_duracion_minutos: int = Field(default=480, ge=5, le=1440)  # SESION_DURACION_MINUTOS
    sesion_cookie_segura: bool = False  # SESION_COOKIE_SEGURA; true solo con HTTPS

    @field_validator("sesion_clave")
    @classmethod
    def _validar_clave(cls, valor: SecretStr) -> SecretStr:
        if len(valor.get_secret_value()) < _LARGO_MINIMO_CLAVE:
            raise ValueError("SESION_CLAVE debe tener al menos 32 caracteres.")
        return valor

    @field_validator("cors_origins")
    @classmethod
    def _validar_origenes(cls, valor: str) -> str:
        origenes = _separar_origenes(valor)
        if not origenes:
            raise ValueError("CORS_ORIGINS debe tener al menos un origen.")
        for origen in origenes:
            if not _PATRON_ORIGEN.fullmatch(origen):
                raise ValueError(
                    "Cada origen de CORS_ORIGINS debe tener la forma http(s)://host[:puerto], "
                    "sin «*», ruta ni barra final."
                )
        return valor

    @property
    def lista_origenes(self) -> list[str]:
        """Convierte la cadena de orígenes permitidos en lista."""
        return _separar_origenes(self.cors_origins)

    @property
    def clave_sesion_bytes(self) -> bytes:
        """Clave de firma de la cookie de sesión, en bytes UTF-8."""
        return self.sesion_clave.get_secret_value().encode("utf-8")


def cargar_config() -> Settings:
    """Lee la configuración del entorno y de backend/.env. Solo la usa la `app` perezosa de main.py."""
    return Settings()  # type: ignore[call-arg]


def config_actual(request: Request) -> Settings:
    """Dependencia de FastAPI: la configuración con la que se creó la aplicación."""
    return request.app.state.config
