from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class MySimConfig:
    base_url: str
    token: str
    timeout: Tuple[int, int] = (5, 30)  # (connect, read)
    max_retries: int = 3
    backoff_factor: float = 0.4

    @staticmethod
    def from_env() -> "MySimConfig":
        base_url = os.getenv("MYSIM_BASE_URL", "https://tests.simeng.es/api/v1/pub").rstrip("/")
        token = os.getenv("MYSIM_TOKEN", "")
        if not token:
            raise ValueError("Falta MYSIM_TOKEN en el entorno (o en .env).")
        return MySimConfig(base_url=base_url, token=token)
