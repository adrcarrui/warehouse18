from math import ceil
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

def paginate(
    db: Session,
    stmt: Select,
    page: int,
    page_size: int,
):
    # Total: cuenta sobre el statement sin ORDER BY
    count_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.execute(count_stmt).scalar_one()

    pages = ceil(total / page_size) if total else 0
    offset = (page - 1) * page_size

    items = db.execute(stmt.limit(page_size).offset(offset)).scalars().all()
    return items, total, pages
