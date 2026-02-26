import time
from dataclasses import dataclass
from sqlalchemy.orm import Session
from warehouse18.infrastructure.repositories.app_settings_repo import AppSettingsRepo

RFID_CREATE_MOVEMENTS_KEY = "rfid.create_movements"

@dataclass
class CachedValue:
    value: bool
    expires_at: float

class SettingsService:
    def __init__(self, ttl_seconds: int = 2):
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, CachedValue] = {}

    def get_rfid_create_movements(self, db: Session) -> bool:
        now = time.time()
        c = self._cache.get(RFID_CREATE_MOVEMENTS_KEY)
        if c and c.expires_at > now:
            return c.value

        repo = AppSettingsRepo(db)
        v = repo.get(RFID_CREATE_MOVEMENTS_KEY, True)
        v = bool(v)

        self._cache[RFID_CREATE_MOVEMENTS_KEY] = CachedValue(v, now + self.ttl_seconds)
        return v

    def set_rfid_create_movements(self, db: Session, enabled: bool) -> bool:
        repo = AppSettingsRepo(db)
        v = repo.set(RFID_CREATE_MOVEMENTS_KEY, bool(enabled))
        # invalida cache
        self._cache.pop(RFID_CREATE_MOVEMENTS_KEY, None)
        return bool(v)