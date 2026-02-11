from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from warehouse18.config import settings

engine = create_engine(settings.dsn, echo=settings.debug)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
