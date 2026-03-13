from __future__ import annotations

import base64
import json
from typing import Optional, Any

import requests
import typer
from dotenv import load_dotenv
from rich import print as rprint
from rich.console import Console
from rich.table import Table

from warehouse18.infrastructure.integrations.mySim import MySimClient, MySimConfig
from warehouse18.infrastructure.integrations.mySim.adapter import MySimAdapter
from warehouse18.infrastructure.integrations.mySim.errors import MySimError

from warehouse18.application.mySim.movement_types import MovementType, SpecialLocation
from warehouse18.application.mySim.movement_request import MovementRequest

app = typer.Typer(
    name="mysim",
    help="CLI para mySim (test/prod por env vars).",
    add_completion=False,
)

users_app = typer.Typer(help="Operaciones sobre usuarios (accounts).")
parts_app = typer.Typer(help="Operaciones sobre parts y movimientos.")
locations_app = typer.Typer(help="Operaciones sobre localizaciones.")
movements_app = typer.Typer(help="Operaciones sobre movimientos (entity=movement).")

app.add_typer(users_app, name="users")
app.add_typer(parts_app, name="parts")
app.add_typer(locations_app, name="locations")
app.add_typer(movements_app, name="movements")

console = Console()


def _json(obj: Any) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def _bootstrap() -> MySimAdapter:
    # Carga .env si existe (si no existe, seguirá tirando de env del sistema)
    load_dotenv()
    cfg = MySimConfig.from_env()
    client = MySimClient(cfg)
    return MySimAdapter(client)


def _print_table(rows: list[dict], columns: list[str], title: str = "") -> None:
    table = Table(title=title)
    for col in columns:
        table.add_column(col)

    for r in rows:
        table.add_row(*[str(r.get(c, "")) for c in columns])

    console.print(table)


def _resolve_part_db_id(api: MySimAdapter, part_db_id: Optional[int], part_code: Optional[str]) -> int:
    if part_db_id is not None:
        return part_db_id
    if part_code:
        pid = api.get_part_id_by_part_code(part_code)
        if pid is None:
            raise typer.BadParameter(f"No se encontró partId={part_code} en mySim.")
        return pid
    raise typer.BadParameter("Debes indicar --part-db-id o --part-code (ej GEN-010838).")


def _b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def _cfg_pick_attr(cfg: object, candidates: list[str]) -> str | None:
    """
    Devuelve el valor del primer atributo existente (y truthy) en cfg.
    """
    for name in candidates:
        if hasattr(cfg, name):
            val = getattr(cfg, name)
            if val:
                return str(val)
    return None


def _cfg_debug_attrs(cfg: object) -> str:
    """
    Lista "bonita" de attrs públicos para debug.
    """
    names = sorted([n for n in dir(cfg) if not n.startswith("_")])
    # no imprimimos métodos (callable) para no ensuciar demasiado
    filtered = []
    for n in names:
        try:
            v = getattr(cfg, n)
            if callable(v):
                continue
            filtered.append(n)
        except Exception:
            continue
    return ", ".join(filtered)

def _movement_type_to_mysim_id(mt: MovementType) -> int:
    """
    IDs de movementType en mySim.
    Ajusta aquí si cambian en tu entorno.
    """
    mapping = {
        MovementType.GOOD_RECEIPT: 57,
        MovementType.GOOD_ISSUE: 58,
        MovementType.GOOD_TRANSFER: 59,
        MovementType.GOOD_TRACKING: 234,
    }
    try:
        return mapping[mt]
    except KeyError:
        raise typer.BadParameter(f"No hay mapping mySim para movement type: {mt}")


def _movement_type_to_mysim_name(mt: MovementType) -> str:
    """
    Nombre de movementType en mySim.
    """
    mapping = {
        MovementType.GOOD_RECEIPT: "Good Receipt",
        MovementType.GOOD_ISSUE: "Good Issue",
        MovementType.GOOD_TRANSFER: "Good Transfer",
        MovementType.GOOD_TRACKING: "Good Tracking",
    }
    try:
        return mapping[mt]
    except KeyError:
        raise typer.BadParameter(f"No hay mapping mySim name para movement type: {mt}")


def _post_movement_direct(
    cfg: MySimConfig,
    row: dict[str, Any],
    *,
    allow_redirects: bool = False,
) -> dict[str, Any]:
    """
    Replica el script manual que sí funciona:
      POST /set?entity=movement&extraQuery=BASE64("t.idCol='X' AND t.entity='Parts'")
    """
    extra_query_expr = f"t.idCol='{row['idCol']}' AND t.entity='Parts'"
    extra_query = _b64(extra_query_expr)

    url = f"{cfg.base_url.rstrip('/')}/set"
    params = {
        "entity": "movement",
        "extraQuery": extra_query,
    }
    headers = {
        "Accept": "application/json",
        "X-AUTH-TOKEN": cfg.token,
    }

    rprint(f"[cyan]ROW SENT TO MYSIM /set[/cyan]: {row}")
    resp = requests.post(
        url,
        headers=headers,
        params=params,
        json=[row],
        timeout=60,
        allow_redirects=allow_redirects,
    )

    if not resp.ok:
        payload: dict[str, Any] = {
            "status_code": resp.status_code,
            "location": resp.headers.get("Location"),
            "body_head": resp.text[:500],
        }
        raise MySimError(status_code=resp.status_code, payload=payload)

    try:
        return resp.json()
    except ValueError:
        return {"status_code": resp.status_code, "text": resp.text[:2000]}
# -----------------------------
# MOVEMENTS (direct mySim query by movementId via extraQuery)
# -----------------------------
@movements_app.command("get")
def movements_get(
    movement_id: str = typer.Option(..., "--movement-id", "-m", help="Ej: M2020-051544"),
    as_json: bool = typer.Option(True, "--json/--no-json", help="Imprimir JSON (por defecto sí)."),
):
    """
    Recupera un movimiento de mySim por movementId usando extraQuery (Base64).

    Hace:
      POST /get?entity=movement&extraQuery=BASE64("t.movementId='M2020-051544'")
    """
    load_dotenv()
    cfg = MySimConfig.from_env()

    # Intenta detectar nombres típicos (sin asumir nada)
    base_url = _cfg_pick_attr(cfg, ["base_url", "BASE_URL", "url", "host", "endpoint"])
    token = _cfg_pick_attr(cfg, ["token", "api_token", "auth_token", "x_auth_token", "X_AUTH_TOKEN", "key", "apiKey"])

    if not base_url or not token:
        rprint("[red]No puedo construir la llamada a mySim porque faltan datos en MySimConfig.[/red]")
        rprint(f"base_url detectado: {base_url!r}")
        rprint(f"token detectado: {('***' if token else None)!r}")
        rprint(f"Atributos disponibles en cfg: {_cfg_debug_attrs(cfg)}")
        raise typer.Exit(code=2)

    url = f"{base_url.rstrip('/')}/get"

    # filtro tipo: t.movementId='M2020-051544'
    filter_expr = f"t.movementId='{movement_id}'"
    extra_query = _b64(filter_expr)

    headers = {
        "Accept": "application/json",
        "X-AUTH-TOKEN": token,
    }

    params = {
        "entity": "movement",
        "extraQuery": extra_query,
    }

    try:
        resp = requests.post(url, headers=headers, params=params, timeout=30)
    except requests.RequestException as re:
        rprint(f"[red]Request error[/red] {re}")
        raise typer.Exit(code=1)

    if not resp.ok:
        rprint(f"[red]HTTP {resp.status_code}[/red]")
        print(resp.text[:2000])
        raise typer.Exit(code=1)

    try:
        data = resp.json()
    except ValueError:
        rprint("[red]La respuesta no es JSON[/red]")
        print(resp.text[:2000])
        raise typer.Exit(code=1)

    if as_json:
        print(_json(data))
    else:
        rprint("[green]OK[/green]")


# -----------------------------
# USERS
# -----------------------------
@users_app.command("list")
def users_list(
    limit: int = typer.Option(50, help="Número máximo de usuarios a traer."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir JSON completo."),
):
    """
    Lista usuarios (accounts).
    """
    api = _bootstrap()
    try:
        rows = api.get_all_users(limit=limit)
        rprint(f"[green]OK[/green] usuarios={len(rows)}")

        if as_json:
            print(_json(rows))
            return

        cols = ["id", "fullName", "email", "acronym"]
        _print_table(rows, cols, title=f"Users (limit={limit})")

    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)


@users_app.command("get")
def users_get(
    user_id: Optional[str] = typer.Option(None, "--id", help="ID del usuario."),
    email: Optional[str] = typer.Option(None, "--email", help="Email del usuario."),
    as_json: bool = typer.Option(True, "--json/--no-json", help="Imprimir JSON (por defecto sí)."),
):
    """
    Obtiene info de 1 usuario por ID o email.
    """
    if not user_id and not email:
        raise typer.BadParameter("Indica --id o --email.")

    api = _bootstrap()
    try:
        user = api.get_user_by_id(user_id) if user_id else api.get_user_by_email(email or "")
        if not user:
            rprint("[yellow]No encontrado[/yellow]")
            raise typer.Exit(code=2)

        if as_json:
            print(_json(user))
        else:
            cols = ["id", "fullName", "email", "acronym"]
            _print_table([user], cols, title="User")

    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)


# -----------------------------
# LOCATIONS
# -----------------------------
@locations_app.command("list")
def locations_list(
    entity: str = typer.Option("location", help="Nombre de la entidad de localizaciones en mySim."),
    limit: int = typer.Option(100, help="Número máximo de localizaciones a traer."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir JSON completo."),
):
    """
    Lista localizaciones (entity configurable porque mySim puede llamarlo distinto).
    """
    api = _bootstrap()
    try:
        rows = api.get_all_locations(entity=entity, limit=limit)
        rprint(f"[green]OK[/green] locations={len(rows)} (entity={entity})")

        if as_json:
            print(_json(rows))
            return

        if not rows:
            rprint("[yellow]No hay localizaciones[/yellow]")
            return

        cols = list(rows[0].keys())
        _print_table(rows, cols, title=f"Locations (entity={entity}, limit={limit})")

    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)


# -----------------------------
# PARTS / MOVEMENTS
# -----------------------------
@parts_app.command("get")
def parts_get(
    part_db_id: int | None = typer.Option(None, "--part-db-id", help="ID interno del part."),
    part_code: str | None = typer.Option(None, "--part-code", help="Código partId (ej 235-0839)."),
):
    """
    Devuelve la información completa de un part.
    """
    api = _bootstrap()

    if not part_db_id and not part_code:
        rprint("[red]Debes indicar --part-db-id o --part-code[/red]")
        raise typer.Exit(code=2)

    if part_db_id:
        part = api.get_part_by_id(part_db_id)
    else:
        part = api.get_part_by_part_code(part_code)

    if not part:
        rprint("[yellow]Part no encontrado[/yellow]")
        raise typer.Exit(code=1)

    print(_json(part))


@parts_app.command("movements")
def parts_movements(
    part_db_id: Optional[int] = typer.Option(None, "--part-db-id", help="ID interno (db id) del part."),
    part_code: Optional[str] = typer.Option(None, "--part-code", help="Código partId (ej GEN-010838)."),
    limit: int = typer.Option(50, help="Número máximo de movimientos."),
    newest_first: bool = typer.Option(True, help="Ordenar por fecha DESC."),
    as_json: bool = typer.Option(False, "--json", help="Imprimir JSON completo."),
):
    """
    Lista movimientos de un part.
    """
    api = _bootstrap()
    try:
        pid = _resolve_part_db_id(api, part_db_id, part_code)
        rows = api.get_item_movements(item_id=pid, item_entity="Parts", limit=limit, newest_first=newest_first)
        rprint(f"[green]OK[/green] movements={len(rows)} part_id={pid}")

        if as_json:
            print(_json(rows))
            return

        cols = ["id", "movementId", "date", "type", "movementType", "entity", "idCol"]
        _print_table(rows, cols, title=f"Movements (part_id={pid}, limit={limit})")

    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)


@parts_app.command("last-movement")
def parts_last_movement(
    part_db_id: Optional[int] = typer.Option(None, "--part-db-id", help="ID interno (db id) del part."),
    part_code: Optional[str] = typer.Option(None, "--part-code", help="Código partId (ej GEN-010838)."),
):
    """
    Saca el último movimiento de un part.
    """
    api = _bootstrap()
    try:
        pid = _resolve_part_db_id(api, part_db_id, part_code)
        last = api.get_last_item_movement(item_id=pid, item_entity="Parts")
        if not last:
            rprint("[yellow]No hay movimientos[/yellow]")
            raise typer.Exit(code=2)

        print(_json(last))

    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)


@parts_app.command("upload-movement")
@parts_app.command("upload-movement")
def parts_upload_movement(
    part_db_id: int | None = typer.Option(None, "--part-db-id", help="ID interno (db id) del part."),
    part_code: str | None = typer.Option(None, "--part-code", help="Código partId (ej 235-0839)."),

    movement_type: MovementType = typer.Option(..., "--type", help="Tipo de movimiento (lógica warehouse18)."),

    dest: str | None = typer.Option(None, "--dest", help="destinationLocation (obligatorio según tipo)."),
    origin: str | None = typer.Option(None, "--origin", help="sourceLocation (obligatorio para Good receipt)."),
    desc: str = typer.Option("", "--desc", help="movementDescription (obligatorio para Good tracking)."),

    dest_special: SpecialLocation | None = typer.Option(None, "--dest-special", help="Destino como localización especial."),
    origin_special: SpecialLocation | None = typer.Option(None, "--origin-special", help="Origen como localización especial."),

    done_by: str | None = typer.Option(None, "--done-by", help="doneBy (opcional)."),
    date: str | None = typer.Option(None, "--date", help="YYYY-MM-DD HH:MM (o HH:MM:SS) (opcional)."),
    quantity: int = typer.Option(1, "--qty", help="quantity."),
    parent_record: str | None = typer.Option(None, "--parent-record", help="parentRecord (opcional)."),
    version_installed: str | None = typer.Option(None, "--version-installed", help="versionInstalled (opcional)."),

    as_json: bool = typer.Option(True, "--json/--no-json", help="Imprimir respuesta JSON."),
):
    """
    Crea/sube un movimiento para un part usando POST directo a:
      /set?entity=movement&extraQuery=...
    igual que el script manual que sí funciona.
    """
    load_dotenv()
    cfg = MySimConfig.from_env()
    api = _bootstrap()

    pid = _resolve_part_db_id(api, part_db_id, part_code)

    final_dest = dest_special.value if dest_special else dest
    final_origin = origin_special.value if origin_special else origin

    # Validación funcional básica
    req = MovementRequest(
        part_db_id=pid,
        movement_type=movement_type,
        destination=final_dest,
        origin=final_origin,
        description=desc,
        done_by=done_by,
        date=date,
    )

    try:
        req.validate()
    except ValueError as ve:
        rprint(f"[red]Validación[/red]: {ve}")
        raise typer.Exit(code=2)

    movement_type_id = _movement_type_to_mysim_id(movement_type)
    movement_type_name = _movement_type_to_mysim_name(movement_type)

    row: dict[str, Any] = {
        "id": 0,
        "entity": "Parts",
        "idCol": pid,
        "movementType": movement_type_id,
        "movementType.name": movement_type_name,
        "quantity": quantity,
        "movementDescription": desc,
    }

    if done_by is not None:
        try:
            row["doneBy"] = int(done_by)
        except ValueError:
            row["doneBy"] = done_by

    if date:
        row["date"] = date

    if final_origin:
        row["sourceLocation"] = final_origin

    if final_dest:
        row["destinationLocation"] = final_dest

    # Para parecerse más al script manual que te funciona
    if parent_record:
        row["parentRecord"] = parent_record
    elif part_code:
        row["parentRecord"] = part_code

    if version_installed is not None:
        row["versionInstalled"] = version_installed

    try:
        resp = _post_movement_direct(cfg, row)
    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)

    if as_json:
        print(_json(resp))
    else:
        rprint("[green]OK[/green] movimiento creado")


def main():
    app()


if __name__ == "__main__":
    main()