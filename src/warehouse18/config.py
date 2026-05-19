from typing import List
from pathlib import Path
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    dsn: str
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    debug: bool = False
    sql_echo: bool = False
    api_prefix: str = "/api"
    root_path: str = ""

    rfid_internal_enable: bool = True
    rfid_host: str = "192.168.0.178"
    rfid_port: int = 4001
    rfid_8a_frame_hex: str = ""
    rfid_log_level: str = "WARNING"
    rfid_api_key: str = ""
    rfid_ingest_url: str = "http://127.0.0.1:8000/api/rfid/ingest"
    rfid_forward_to_ingest: bool = True
    rfid_emit_enable: bool = False

    email_enabled: bool = False
    email_smtp_host: str = ""
    email_smtp_port: int = 587
    email_smtp_user: str = ""
    email_smtp_password: str = ""
    email_from: str = ""
    email_to_alerts: str = ""
    email_use_tls: bool = True
    email_use_ssl: bool = False
    
    email_timeout_seconds: int = 10
    model_config = SettingsConfigDict(
        env_prefix="WAREHOUSE18_",
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

print("DBG os.getenv RFID API KEY =", repr(os.getenv("WAREHOUSE18_RFID_API_KEY")))
settings = Settings()

print("DBG BASE_DIR =", BASE_DIR)
print("DBG ENV FILE =", BASE_DIR / ".env")
print("DBG ENV EXISTS =", (BASE_DIR / ".env").exists())
print("DBG RFID API KEY SETTINGS =", repr(settings.rfid_api_key))