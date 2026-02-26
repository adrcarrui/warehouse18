from sqlalchemy.orm import Session
from warehouse18.domain.models import AppSetting

class AppSettingsRepo:
    def __init__(self, db: Session):
        self.db = db

    def get(self, key: str, default):
        row = self.db.get(AppSetting, key)
        return row.value if row else default

    def set(self, key: str, value):
        row = self.db.get(AppSetting, key)
        if row:
            row.value = value
        else:
            row = AppSetting(key=key, value=value)
            self.db.add(row)
        self.db.commit()
        return row.value