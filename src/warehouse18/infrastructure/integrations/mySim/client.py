from __future__ import annotations

import base64
import json
from typing import Any, Dict, List, Optional, Union

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import MySimConfig
from .errors import MySimError


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


def rows_normalized(resp: Any) -> List[Dict[str, Any]]:
    """
    Normaliza respuestas típicas de mySim a List[dict].
    Muchas veces viene como {"data": {"data": [...]}}.
    """
    if resp is None:
        return []

    if isinstance(resp, dict):
        d = resp.get("data", resp)
        if isinstance(d, dict):
            rows = d.get("data") or d.get("rows") or d.get("items") or d.get("list")
            if isinstance(rows, list):
                return [r if isinstance(r, dict) else {"value": r} for r in rows]
        if isinstance(d, list):
            return [r if isinstance(r, dict) else {"value": r} for r in d]

    if isinstance(resp, list):
        return [r if isinstance(r, dict) else {"value": r} for r in resp]

    return []


class MySimClient:
    """
    Cliente REST de mySim (spec):
    - Header: X-AUTH-TOKEN
    - Endpoints: /get, /set, /delete, /get-change-crud
    """

    def __init__(self, cfg: MySimConfig):
        self.cfg = cfg

        s = requests.Session()
        retries = Retry(
            total=cfg.max_retries,
            connect=cfg.max_retries,
            read=cfg.max_retries,
            status=cfg.max_retries,
            allowed_methods=frozenset(["GET", "POST", "DELETE"]),
            status_forcelist=(429, 500, 502, 503, 504),
            backoff_factor=cfg.backoff_factor,
            raise_on_status=False,
        )
        s.mount("https://", HTTPAdapter(max_retries=retries))
        s.mount("http://", HTTPAdapter(max_retries=retries))
        self.s = s

    def _headers(self) -> Dict[str, str]:
        h = {
            "Accept": "application/json",
            "Content-Type": "application/json; charset=utf-8",
            "X-AUTH-TOKEN": self.cfg.token,
        }
        # Debug rápido (si te molesta, lo pasamos a logger)
        print("TOKEN present:", bool(self.cfg.token), "len:", len(self.cfg.token))
        return h

    def _parse(self, r: requests.Response) -> Any:
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text}

        body_status = data.get("status") if isinstance(data, dict) else None

        # Error por HTTP real
        if r.status_code >= 400:
            raise MySimError(f"HTTP {r.status_code} en mySim", status_code=r.status_code, payload=data)

        # Error "interno" mySim (a veces devuelve HTTP 200 con status=404 en JSON)
        if isinstance(body_status, int) and body_status >= 400:
            raise MySimError(f"mySim status {body_status}", status_code=body_status, payload=data)

        return data

    def get(
        self,
        *,
        entity: str,
        id: Optional[Union[int, str]] = None,
        extra_query: Optional[str] = None,  # sin b64
        order_by: Optional[str] = None,     # sin b64
        order_type: Optional[str] = None,   # ASC/DESC
        limit: Optional[int] = None,
        **params: Any,
    ) -> Any:
        """
        Uso:
            client.get(entity="parts", extra_query="t.partId='235-0839'", limit=1)
        """
        url = f"{self.cfg.base_url}/get"
        q: Dict[str, Any] = {"entity": entity, **params}

        if id is not None:
            q["id"] = id
        if extra_query:
            q["extraQuery"] = b64(extra_query)
        if order_by:
            q["orderBy"] = b64(order_by)
        if order_type:
            q["orderType"] = order_type
        if limit is not None:
            q["limit"] = str(limit)

        r = self.s.get(url, headers=self._headers(), params=q, timeout=self.cfg.timeout)
        return self._parse(r)

    def set(self, *, entity: str, objects: list[dict]) -> Any:
        """
        Endpoint correcto para crear/editar entidades en mySim:
            POST /set?entity=<entity>
        Body:
            [ { ... }, { ... } ]

        Uso:
            client.set(entity="movement", objects=[{...row...}])
        """
        url = f"{self.cfg.base_url}/set"
        r = self.s.post(
            url,
            headers=self._headers(),
            params={"entity": entity},
            data=json.dumps(objects),
            timeout=self.cfg.timeout,
            allow_redirects=False,
        )

        # Debug útil
        print("HTTP:", r.status_code)
        print("REQ URL:", r.request.url)
        print("Location:", r.headers.get("Location"))
        print("Content-Type:", r.headers.get("Content-Type"))

        # Si intentan mandarte al login, mejor enterarte aquí
        if r.status_code in (301, 302, 303, 307, 308):
            raise MySimError(
                f"Redirect to {r.headers.get('Location')} (token no aceptado o sesión requerida)",
                status_code=r.status_code,
                payload={"location": r.headers.get("Location"), "body_head": r.text[:200]},
            )

        # Si aún así te devuelven HTML “ok”… (login camuflado)
        ct = (r.headers.get("Content-Type") or "").lower()
        if "text/html" in ct:
            raise MySimError(
                "mySim devolvió HTML (login) en vez de JSON. Token no está aplicando a este endpoint.",
                status_code=r.status_code,
                payload={"body_head": r.text[:200]},
            )

        return self._parse(r)

    def delete(self, *, entity: str, id: Union[int, str]) -> Any:
        """
        Uso:
            client.delete(entity="slots", id=123)
        """
        url = f"{self.cfg.base_url}/delete"
        r = self.s.delete(
            url,
            headers=self._headers(),
            params={"entity": entity, "id": id},
            timeout=self.cfg.timeout,
        )
        return self._parse(r)

    def get_change_crud(self, *, entity: str, from_datetime: str, exclude_tcms: bool = True) -> Any:
        """
        Uso:
            client.get_change_crud(entity="parts", from_datetime="2026-02-20 00:00:00")
        """
        url = f"{self.cfg.base_url}/get-change-crud"
        q = {
            "entity": entity,
            "fromDateTime": b64(from_datetime),
            "excluseTCMS": "true" if exclude_tcms else "false",  # typo real en spec
        }
        r = self.s.get(url, headers=self._headers(), params=q, timeout=self.cfg.timeout)
        return self._parse(r)

    # -------------------------------------------------------
    # LEGACY / NO USAR (en tu entorno "Method not exists")
    # -------------------------------------------------------
    def create(self, *, entity: str, obj: dict) -> Any:
        """
        En tu entorno parece NO existir /create:
            {"msg":"Method not exists","status":404,...}

        Mantengo el método por compatibilidad, pero úsalo solo si
        confirmas que tu mySim lo soporta.
        """
        url = f"{self.cfg.base_url}/create"
        r = self.s.post(
            url,
            headers=self._headers(),
            params={"entity": entity},
            data=json.dumps(obj),
            timeout=self.cfg.timeout,
            allow_redirects=False,
        )

        print("HTTP:", r.status_code)
        print("REQ URL:", r.request.url)
        print("Location:", r.headers.get("Location"))
        print("Content-Type:", r.headers.get("Content-Type"))

        if r.status_code in (301, 302, 303, 307, 308):
            raise MySimError(
                f"Redirect to {r.headers.get('Location')} (token no aceptado o sesión requerida)",
                status_code=r.status_code,
                payload={"location": r.headers.get("Location"), "body_head": r.text[:200]},
            )

        ct = (r.headers.get("Content-Type") or "").lower()
        if "text/html" in ct:
            raise MySimError(
                "mySim devolvió HTML (login) en vez de JSON en CREATE.",
                status_code=r.status_code,
                payload={"body_head": r.text[:200]},
            )

        return self._parse(r)

    # -------------------------------------------------------
    # Helper: movimiento vía set (atajo)
    # -------------------------------------------------------
    def create_movement_via_set(self, movement_row: dict) -> Any:
        """
        Helper por si quieres llamar directo sin pasar por adapter.

        movement_row debe ser el objeto plano que espera mySim en /set,
        NO el wrapper {"entity":..., "data":...}.

        Ejemplo:
            client.create_movement_via_set({
                "id": 0,
                "entity": "Parts",
                "idCol": 1234,
                "movementType": 58,
                "quantity": 1,
                "destinationLocation": 1,
                "doneBy": 5628,
                "date": "2026-02-20 07:19",
            })
        """
        return self.set(entity="movement", objects=[movement_row])