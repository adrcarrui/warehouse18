from __future__ import annotations

from fastapi import Request, Response


def set_pagination_headers(
    *,
    request: Request,
    response: Response,
    page: int,
    page_size: int,
    total: int,
    pages: int,
) -> None:
    """
    Añade headers estándar de paginación:
    - X-Total-Count
    - X-Page
    - X-Page-Size
    - X-Total-Pages
    - Link (rel="prev"/"next")
    """

    # Headers básicos
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Page"] = str(page)
    response.headers["X-Page-Size"] = str(page_size)
    response.headers["X-Total-Pages"] = str(pages)

    # Construcción del header Link (prev / next)
    links: list[str] = []

    if page > 1:
        prev_url = str(
            request.url.include_query_params(
                page=page - 1,
                page_size=page_size,
            )
        )
        links.append(f'<{prev_url}>; rel="prev"')

    if pages > 0 and page < pages:
        next_url = str(
            request.url.include_query_params(
                page=page + 1,
                page_size=page_size,
            )
        )
        links.append(f'<{next_url}>; rel="next"')

    if links:
        response.headers["Link"] = ", ".join(links)
