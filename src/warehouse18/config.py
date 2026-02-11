from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]  # .../warehouse18 (raíz del repo)

class Settings(BaseSettings):
    dsn: str
    cors_origins: str = ""
    debug: bool = False
    api_prefix: str = "/api"

    model_config = SettingsConfigDict(
        env_prefix="WAREHOUSE18_",
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
