from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import User
from warehouse18.presentation.api.schemas import UserCreateIn, UserOut, UserUpdateIn  # <-- esto faltaba

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut)
def create_user(body: UserCreateIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="User already exists")

    if body.email and db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    u = User(**body.model_dump())
    db.add(u)
    db.commit()
    db.refresh(u)

    return UserOut(
        id=u.id,
        username=u.username,
        full_name=u.full_name,
        email=u.email,
        role=u.role,
        department=u.department,
        is_active=u.is_active,
        auth_provider=u.auth_provider,
        last_login_at=u.last_login_at,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )

@router.get("/", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    rows = db.query(User).order_by(User.id.asc()).all()
    return [
        UserOut(
            id=u.id,
            username=u.username,
            full_name=u.full_name,
            email=u.email,
            role=u.role,
            department=u.department,
            is_active=u.is_active,
            auth_provider=u.auth_provider,
            last_login_at=u.last_login_at,
            created_at=u.created_at,
            updated_at=u.updated_at,
        )
        for u in rows
    ]

@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, body: UserUpdateIn, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=409, detail="User not found")

    data = body.model_dump(exclude_unset=True)  # <- CLAVE

    # Si quieres permitir "email": null para borrar email, esto lo permite.
    # Si NO quieres permitirlo, lo bloqueas aquí.
    if "email" in data and data["email"] is not None and data["email"] != u.email:
        if db.query(User).filter(User.email == data["email"]).first():
            raise HTTPException(status_code=409, detail="Email already exists")

    for k, v in data.items():
        setattr(u, k, v)

    if hasattr(u, "updated_at"):
        u.updated_at = func.now()

    db.commit()
    db.refresh(u)

    return UserOut(
        id=u.id,
        username=u.username,
        full_name=u.full_name,
        email=u.email,
        role=u.role,
        department=u.department,
        is_active=u.is_active,
        auth_provider=u.auth_provider,
        last_login_at=getattr(u, "last_login_at", None),
        created_at=u.created_at,
        updated_at=u.updated_at,
    )

@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=409, detail="User not found")

    u.is_active = False
    if hasattr(u, "updated_at"):
        u.updated_at = func.now()

    db.commit()
    return {"status": "ok"}