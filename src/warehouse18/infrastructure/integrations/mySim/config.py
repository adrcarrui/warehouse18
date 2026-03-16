from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv


@dataclass(frozen=True)
class MySimConfig:
    base_url: str
    token: str
    timeout: Tuple[int, int] = (5, 30)  # (connect, read)
    max_retries: int = 3
    backoff_factor: float = 0.4

    @staticmethod
    def from_env() -> "MySimConfig":
        # Cargar .env del repo de forma explícita y robusta
        # config.py está en:
        # src/warehouse18/infrastructure/integrations/mySim/config.py
        # parents[0] = mySim
        # parents[1] = integrations
        # parents[2] = infrastructure
        # parents[3] = warehouse18
        # parents[4] = src
        # parents[5] = raíz repo
        repo_root = Path(__file__).resolve().parents[5]
        env_path = repo_root / ".env"
        load_dotenv(env_path)

        base_url = os.getenv("MYSIM_BASE_URL", "https://tests.simeng.es/api/v1/pub").strip().strip('"').rstrip("/")
        token = os.getenv("MYSIM_TOKEN", "").strip().strip('"')

        if not token:
            raise ValueError(
                f"Falta MYSIM_TOKEN en el entorno (o en .env). "
                f"Se intentó cargar desde: {env_path}"
            )

        return MySimConfig(base_url=base_url, token=token)