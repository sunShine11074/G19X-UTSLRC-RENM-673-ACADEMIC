"""Configuración de la aplicación, leída desde variables de entorno."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str
    cors_origins: str = "http://localhost:5173"

    @property
    def lista_origenes(self) -> list[str]:
        """Convierte la cadena de orígenes permitidos en lista."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
