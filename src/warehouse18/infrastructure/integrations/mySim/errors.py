from __future__ import annotations
from typing import Any, Optional


class MySimError(RuntimeError):
    def __init__(self, message: str, *, status_code: Optional[int] = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload
