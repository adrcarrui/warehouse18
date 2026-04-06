from sqlalchemy import String, Boolean, Column, BigInteger, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .base import Base
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    email: Mapped[str | None] = mapped_column(String(200), unique=True, index=True, nullable=True)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="User")
    department: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    auth_provider: Mapped[str] = mapped_column(String(30), nullable=False, default="local")

    last_login_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    mysim_id = Column(BigInteger, nullable=True, unique=True, index=True)
    
    movements = relationship("Movement", back_populates="user")