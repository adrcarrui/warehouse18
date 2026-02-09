import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

DSN = os.environ.get("WAREHOUSE18_DSN")
if not DSN:
    raise RuntimeError("WAREHOUSE18_DSN env var is required")

# SQLAlchemy 2.0 style
engine = create_engine(
    DSN,
    pool_pre_ping=True,
)

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
