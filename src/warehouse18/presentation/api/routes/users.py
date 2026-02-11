from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select
from warehouse18.infrastructure.db import get_db
from warehouse18.domain.models import User
from warehouse18.presentation.api.schemas import UserCreateIn, UserOut, UserUpdateIn, PageOut
from sqlalchemy.exc import IntegrityError

from warehouse18.presentation.api.paging import paginate
from warehouse18.presentation.api.pagination_headers import set_pagination_headers

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut)
def create_user(body: UserCreateIn, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="User already exists")

    if body.email and db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")

    u = User(**body.model_dump())
    db.add(u)
    try:
        db.commit()
        db.refresh(u)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))

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

@router.get("/", response_model=PageOut[UserOut])
def list_users(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    q: str | None = Query(None, max_length=200),
    role: str | None = None,
    department: str | None = None,
    is_active: bool | None = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    stmt = select(User)

    # Filtro activo por defecto (pero permite is_active=None para "no filtrar")
    if is_active is not None:
        stmt = stmt.where(User.is_active.is_(is_active))

    if role:
        stmt = stmt.where(User.role == role)

    if department:
        stmt = stmt.where(User.department == department)

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                User.username.ilike(like),
                User.full_name.ilike(like),
                User.email.ilike(like),
            )
        )

    # Orden estable para paginación
    stmt = stmt.order_by(User.id.asc())

    items, total, pages = paginate(db, stmt, page=page, page_size=page_size)

    # Headers útiles
    set_pagination_headers(
        request=request,
        response=response,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

    return PageOut[UserOut](
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        pages=pages,
    )

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

    try:
        db.commit()
        db.refresh(u)
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))

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

    try:
        db.commit()
        return {"status": "ok"}
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e.orig))