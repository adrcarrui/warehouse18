from __future__ import annotations

import json
from typing import Optional, Any

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
app.add_typer(users_app, name="users")
app.add_typer(parts_app, name="parts")
app.add_typer(locations_app, name="locations")

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

        # muestra columnas típicas (ajusta si tu payload usa otros nombres)
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

        # intentamos adivinar columnas típicas
        if not rows:
            rprint("[yellow]No hay localizaciones[/yellow]")
            return

        # usa las claves reales del primer row
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
def parts_upload_movement(
    part_db_id: int | None = typer.Option(None, "--part-db-id", help="ID interno (db id) del part."),
    part_code: str | None = typer.Option(None, "--part-code", help="Código partId (ej 235-0839)."),

    # Tu enum interno (GI/GR/GT etc)
    movement_type: MovementType = typer.Option(..., "--type", help="Tipo de movimiento (lógica warehouse18)."),
    # Override directo a mySim (p.ej. 58) para flows especiales como uninstall-install
    movement_type_id: int | None = typer.Option(
        None,
        "--movement-type-id",
        help="Sobrescribe movementType con el ID numérico de mySim (ej 58).",
    ),

    dest: str | None = typer.Option(None, "--dest", help="destinationLocation (obligatorio según tipo)."),
    origin: str | None = typer.Option(None, "--origin", help="sourceLocation (obligatorio para Good receipt)."),
    desc: str = typer.Option("", "--desc", help="movementDescription (obligatorio para Good tracking)."),

    # Si quieres forzar el uso de localizaciones especiales, puedes pasar estas opciones
    dest_special: SpecialLocation | None = typer.Option(None, "--dest-special", help="Destino como localización especial."),
    origin_special: SpecialLocation | None = typer.Option(None, "--origin-special", help="Origen como localización especial."),

    done_by: str | None = typer.Option(None, "--done-by", help="doneBy (opcional)."),
    date: str | None = typer.Option(None, "--date", help="YYYY-MM-DD HH:MM (o HH:MM:SS) (opcional)."),
    as_json: bool = typer.Option(True, "--json/--no-json", help="Imprimir respuesta JSON."),

    # --- Uninstall/install flow (mySim) ---
    uninstall_part_db_id: int | None = typer.Option(
        None,
        "--uninstall-part-db-id",
        help="ID interno del part a desinstalar (mySim).",
    ),
    uninstall_part_code: str | None = typer.Option(
        None,
        "--uninstall-part-code",
        help="Código del part a desinstalar (ej 2806 o 235-0839).",
    ),

    # Aliases para compatibilidad (typo incluido)
    uninstall_part: str | None = typer.Option(
        None,
        "--uninstall-part",
        help="Alias: código del part a desinstalar (equivalente a --uninstall-part-code).",
    ),
    unistall_part: str | None = typer.Option(
        None,
        "--unistall-part",
        help="(deprecated) Alias mal escrito de --uninstall-part. Se mantiene por compatibilidad.",
    ),

    why_uninstalled: str | None = typer.Option(
        None,
        "--why-uninstalled",
        help="Razón (API: whyIsItUninstalled). Obligatorio si desinstalas.",
    ),
    dest_uninstalled_part: int | None = typer.Option(
        None,
        "--dest-uninstalled-part",
        help="Location ID destino de la pieza desinstalada (API: destUninstalledPart).",
    ),
    uninstalled_by: int | None = typer.Option(
        None,
        "--uninstalled-by",
        help="User ID de quien desinstala (API: uninstalledBy).",
    ),
):
    """
    Crea/sube un movimiento para un part, aplicando reglas del almacén.

    Soporta el flow uninstall-install de mySim:
    - movementType (id numérico) opcional via --movement-type-id
    - uninstallPart (id interno) resuelto via --uninstall-part-db-id o --uninstall-part-code
    - whyIsItUninstalled / destUninstalledPart / uninstalledBy
    """
    api = _bootstrap()

    # 1) Resolver part principal (el "instalado" / el que recibe el movement)
    pid = _resolve_part_db_id(api, part_db_id, part_code)

    # 2) Resolver destinos/orígenes con especiales
    final_dest = dest_special.value if dest_special else dest
    final_origin = origin_special.value if origin_special else origin

    # 3) Resolver uninstall part: puede venir como id o como código (o alias typo)
    final_uninstall_code = uninstall_part_code or uninstall_part or unistall_part

    uninstall_part_id: int | None = None
    if uninstall_part_db_id is not None:
        uninstall_part_id = uninstall_part_db_id
    elif final_uninstall_code:
        found = api.get_part_id_by_part_code(final_uninstall_code)
        if found is None:
            raise typer.BadParameter(f"No se encontró uninstall partCode={final_uninstall_code} en mySim.")
        uninstall_part_id = found

    # 4) Validación mínima del flow uninstall-install
    if uninstall_part_id is not None:
        missing = []
        if not why_uninstalled:
            missing.append("--why-uninstalled")
        if dest_uninstalled_part is None:
            missing.append("--dest-uninstalled-part")
        if uninstalled_by is None:
            missing.append("--uninstalled-by")
        if missing:
            raise typer.BadParameter(
                "Para desinstalar debes indicar también: " + ", ".join(missing)
            )

    # 5) Construir MovementRequest (tu dominio)
    #    Nota: aquí usamos campos "correctos" (uninstall_part_id, movement_type_id).
    #    Si tu MovementRequest todavía no los tiene, tendrás que añadirlos (te indico abajo).
    req = MovementRequest(
        part_db_id=pid,
        movement_type=movement_type,
        destination=final_dest,
        origin=final_origin,
        description=desc,
        done_by=done_by,
        date=date,

        # COMPAT: MovementRequest actual usa 'unistall_part'
        unistall_part=str(uninstall_part_id) if uninstall_part_id is not None else None,

        why_is_it_uninstalled=why_uninstalled,
        dest_uninstalled_part=dest_uninstalled_part,
        uninstalled_by=uninstalled_by,
    )

    # 6) Ejecutar
    try:
        resp = api.create_movement(req)
    except ValueError as ve:
        rprint(f"[red]Validación[/red]: {ve}")
        raise typer.Exit(code=2)
    except MySimError as e:
        rprint(f"[red]MySimError[/red] status={e.status_code}")
        if e.payload:
            print(_json(e.payload))
        raise typer.Exit(code=1)

    # 7) Imprimir
    if as_json:
        print(_json(resp))
    else:
        rprint("[green]OK[/green] movimiento creado")

def main():
    app()


if __name__ == "__main__":
    main()
