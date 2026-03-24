from typing import List
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BASE_DIR.parent / ".env"


class Settings(BaseSettings):
    dsn: str
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    debug: bool = False
    sql_echo: bool = False
    api_prefix: str = "/api"
    root_path: str = ""

    rfid_internal_enable: bool = False
    rfid_host: str = "192.168.0.178"
    rfid_port: int = 4001
    rfid_8a_frame_hex: str = ""
    rfid_log_level: str = "WARNING"

    # Seguridad básica RFID
    rfid_api_key: str = Field(default="", validation_alias="WAREHOUSE18_RFID_API_KEY")
    rfid_internal_enable: bool = Field(default=True, validation_alias="WAREHOUSE18_RFID_INTERNAL_ENABLE")
    rfid_ingest_url: str = Field(default="http://127.0.0.1:8000/api/rfid/ingest", validation_alias="WAREHOUSE18_RFID_INGEST_URL")
    rfid_forward_to_ingest: bool = Field(default=True, validation_alias="WAREHOUSE18_RFID_FORWARD_TO_INGEST")
    rfid_8a_frame_hex: str = Field(default="", validation_alias="WAREHOUSE18_RFID_8A_FRAME_HEX")
    rfid_emit_enable: bool = False

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
print("DBG RFID API KEY SETTINGS =", repr(settings.rfid_api_key))
print("DBG BASE_DIR =", BASE_DIR)
print("DBG ENV FILE =", BASE_DIR / ".env")
print("DBG ENV EXISTS =", (BASE_DIR / ".env").exists())
print("DBG RFID API KEY SETTINGS =", repr(settings.rfid_api_key))