"""Consulta de artículo, último movimiento mySim y movimientos locales en outbox.
Hasta tres intentos por consulta mySim; transacción local de solo lectura. Solo lectura.
Pausas de 2 y 4 segundos ante timeout, conexión o status 408/500/502/503/504.

Guardar en scripts/ y ejecutar desde la raíz del proyecto:
    python scripts/warehouse-sync-check-item.py --part-code "GEN-010838"
Usa MYSIM_BASE_URL y MYSIM_TOKEN de la configuración existente.
Códigos de salida: 0 encontrado, 1 sin coincidencias, 2 error.
"""
from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import requests

# Permite ejecutarlo sin instalar el paquete warehouse18.
for parent in Path(__file__).resolve().parents:
    if (parent / "src" / "warehouse18").is_dir():
        sys.path.insert(0, str(parent / "src"))
        break
from warehouse18.infrastructure.integrations.mySim.config import MySimConfig


class LookupError(RuntimeError):
    pass


class TransientLookupError(LookupError):
    pass


TRANSIENT_STATUSES = {408, 500, 502, 503, 504}


def parse_rows(response: requests.Response) -> list[dict[str, Any]]:
    # Un 404 puede indicar un endpoint o entidad incorrectos. Es un error,
    # no una confirmación de que el artículo no existe.
    if response.status_code in TRANSIENT_STATUSES:
        raise TransientLookupError(f"HTTP {response.status_code}")
    if not 200 <= response.status_code < 300:
        raise LookupError(f"Respuesta HTTP {response.status_code}; existencia no determinada.")
    try:
        body = response.json()
    except ValueError as exc:
        raise LookupError("mySim no devolvió JSON; existencia no determinada.") from exc
    if not isinstance(body, dict):
        raise LookupError("Formato de respuesta inesperado.")
    try:
        status = int(body["status"])
    except (KeyError, ValueError, TypeError) as exc:
        raise LookupError("Respuesta sin un status válido.") from exc
    if status in TRANSIENT_STATUSES:
        raise TransientLookupError(f"mySim status {status}")
    if status != 200:
        raise LookupError(f"mySim devolvió status {status}; existencia no determinada.")
    data = body.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("data"), list):
        raise LookupError("Se esperaba data.data como lista; existencia no determinada.")
    rows = data["data"]
    if any(not isinstance(row, dict) for row in rows):
        raise LookupError("La respuesta contiene registros inválidos.")
    return rows


def query_with_retries(cfg: MySimConfig, params: dict) -> list[dict[str, Any]]:
    # Tres intentos totales, sin reintentos internos del adaptador HTTP.
    for attempt in range(1, 4):
        stamp = datetime.now().astimezone().isoformat(timespec="seconds")
        print(f"{stamp} | intento={attempt}/3 | consultando...", flush=True)
        started = time.perf_counter()
        http = "-"
        try:
            with requests.Session() as session:
                response = session.get(
                    f"{cfg.base_url.rstrip('/')}/get",
                    params=params,
                    headers={"X-AUTH-TOKEN": cfg.token, "Accept": "application/json"},
                    timeout=cfg.timeout,
                    allow_redirects=False,
                )
            http = str(response.status_code)
            rows = parse_rows(response)
        except requests.exceptions.SSLError:
            print(f"  {time.perf_counter() - started:.3f}s | ERROR TLS; sin reintento", flush=True)
            raise LookupError("Error de certificado/TLS; existencia no determinada.") from None
        except (requests.Timeout, requests.ConnectionError, TransientLookupError) as exc:
            reason = str(exc) if isinstance(exc, TransientLookupError) else type(exc).__name__
            print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | {reason}", flush=True)
            if attempt == 3:
                raise LookupError("Tres intentos fallidos; existencia no determinada. Sincronización pendiente de comprobar.") from None
            delay = 2 ** attempt
            print(f"  Reintento en {delay}s", flush=True)
            time.sleep(delay)
            continue
        except (LookupError, requests.RequestException) as exc:
            print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | ERROR; sin reintento", flush=True)
            if isinstance(exc, LookupError):
                raise
            raise LookupError(f"{type(exc).__name__}; existencia no determinada.") from None
        print(f"  {time.perf_counter() - started:.3f}s | HTTP={http} | consulta válida | registros={len(rows)}", flush=True)
        return rows
    raise AssertionError("Bucle de consulta agotado")


def find_item(cfg: MySimConfig, part_code: str) -> dict[str, Any] | None:
    if not part_code.strip():
        raise LookupError("El código del artículo no puede estar vacío.")
    # Conservar guiones, barras y otros caracteres del código original.
    safe_code = part_code.replace("\\", "\\\\").replace("'", "''")
    query = f"t.partId = '{safe_code}'"
    params = {
        "entity": "parts",
        "extraQuery": base64.b64encode(query.encode("utf-8")).decode("ascii"),
        "limit": "2",  # Dos registros bastan para detectar una ambigüedad.
    }
    print(f"Artículo: {part_code} | timeout={cfg.timeout}", flush=True)
    rows = query_with_retries(cfg, params)
    if not rows:
        return None
    if len(rows) > 1:
        raise LookupError("Hay varias coincidencias para el código. Revisar antes de sincronizar.")
    item = rows[0]
    if item.get("partId") != part_code:
        raise LookupError("El código devuelto no coincide exactamente con el solicitado.")
    item_id = item.get("id")
    if isinstance(item_id, bool) or not str(item_id).isdigit() or int(item_id) <= 0:
        raise LookupError("El artículo no tiene un ID interno válido.")
    return item


def get_last_movement(cfg: MySimConfig, item_id: int) -> dict[str, Any] | None:
    """Último por fecha del movimiento; no por fecha de edición.

    Si hay movimientos con la misma fecha máxima, mySim puede devolver
    cualquiera de ellos: todavía no se aplica un desempate por ID.
    """
    query = f"t.idCol = '{int(item_id)}' AND t.entity = 'Parts'"
    params = {
        "entity": "movement",
        "extraQuery": base64.b64encode(query.encode("utf-8")).decode("ascii"),
        "orderBy": base64.b64encode(b"t.date").decode("ascii"),
        "orderType": "DESC",
        "limit": "1",
    }
    print(f"\nConsultando último movimiento de Parts id={item_id} (date DESC)", flush=True)
    rows = query_with_retries(cfg, params)
    if not rows:
        return None
    if len(rows) != 1:
        raise LookupError("mySim no respetó el límite de movimientos.")
    movement = rows[0]
    if str(movement.get("idCol")) != str(item_id) or movement.get("entity") != "Parts":
        raise LookupError("El movimiento devuelto no pertenece al artículo solicitado.")
    if not movement.get("date") or not movement.get("id"):
        raise LookupError("El movimiento devuelto no tiene fecha o ID válido.")
    return movement


def list_pending_movements(part_code: str) -> list[dict[str, Any]]:
    """Lee la cola del artículo sin reclamar trabajos ni cambiar estados.

    to_jsonb permite leer item_key incluso con el esquema antiguo adjunto,
    que todavía no contiene esa columna.
    """
    from sqlalchemy import text
    from warehouse18.infrastructure.db import SessionLocal

    statement = text("""
        SELECT o.id AS outbox_id, o.status AS outbox_status, o.retries,
               o.next_retry_at, o.created_at AS outbox_created_at,
               o.entity_id AS movement_id,
               m.created_at AS movement_date,
               m.item_id AS local_item_id,
               COALESCE(NULLIF(to_jsonb(m)->>'item_key', ''),
                        NULLIF(o.payload_json->>'item_key', ''), i.item_code) AS part_code,
               mt.code AS movement_type,
               m.quantity, m.from_location_id, m.to_location_id,
               m.user_id, m.notes,
               to_jsonb(src) AS source_location_data,
               to_jsonb(dst) AS destination_location_data,
               COALESCE((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.id)
                         FROM public.location_external_refs r
                         WHERE r.location_id = m.from_location_id
                           AND lower(trim(r.source_system)) = 'mysim'), '[]'::jsonb) AS source_external_refs,
               COALESCE((SELECT jsonb_agg(to_jsonb(r) ORDER BY r.id)
                         FROM public.location_external_refs r
                         WHERE r.location_id = m.to_location_id
                           AND lower(trim(r.source_system)) = 'mysim'), '[]'::jsonb) AS destination_external_refs,
               to_jsonb(m) AS movement_data,
               o.payload_json,
               (m.id IS NOT NULL) AS movement_exists,
               (o.next_retry_at IS NULL OR o.next_retry_at <= now()) AS retry_due
        FROM public.integration_outbox AS o
        LEFT JOIN public.movements AS m ON m.id = o.entity_id
        LEFT JOIN public.items AS i ON i.id = m.item_id
        LEFT JOIN public.movement_types AS mt ON mt.id = m.movement_type_id
        LEFT JOIN public.locations AS src ON src.id = m.from_location_id
        LEFT JOIN public.locations AS dst ON dst.id = m.to_location_id
        WHERE o.direction = 'outbound'
          AND o.target_system = 'mysim'
          AND o.entity_type = 'movement'
          AND o.action = 'sync'
          AND o.status IN ('pending', 'error', 'processing', 'failed')
          AND COALESCE(NULLIF(to_jsonb(m)->>'item_key', ''),
                       NULLIF(o.payload_json->>'item_key', ''), i.item_code) = :part_code
        ORDER BY m.created_at ASC NULLS LAST, o.entity_id ASC, o.id ASC
    """)
    with SessionLocal() as db:
        try:
            db.execute(text("SET TRANSACTION READ ONLY"))
            rows = [dict(row) for row in db.execute(statement, {"part_code": part_code}).mappings()]
        finally:
            db.rollback()
    return rows


def positive_id(value: Any) -> bool:
    return not isinstance(value, bool) and str(value).isdigit() and int(value) > 0


def validate_movement(row: dict[str, Any]) -> dict[str, Any]:
    """Validaciones locales. No presupone equivalencia de IDs con mySim."""
    issues = []
    pending = []
    waits = []
    data = row.get("movement_data") or {}
    if not row.get("movement_exists"):
        issues.append("El movimiento local no existe")
    if not row.get("part_code"):
        issues.append("Falta el código del artículo")
    if not row.get("movement_date"):
        issues.append("Falta la fecha del movimiento")
    else:
        try:
            stamp = row['movement_date']
            if not isinstance(stamp, datetime):
                stamp = datetime.fromisoformat(str(stamp))
            if stamp.tzinfo is None or stamp.utcoffset() is None:
                issues.append("Fecha sin zona horaria; falta definir la conversión a mySim")
        except (ValueError, TypeError):
            issues.append("Fecha de movimiento inválida")
    if data.get("review_status") != "confirmed":
        issues.append("La revisión del movimiento no está confirmada")
    if not positive_id(data.get("mysim_user_id")):
        issues.append("Falta un mysim_user_id válido para el autor; no se sustituye por el revisor")
    else:
        pending.append(f"Comprobar usuario {data['mysim_user_id']} en mySim")
    # IDs de tipos ya utilizados por el adaptador del proyecto.
    type_ids = {"GR": 57, "GI": 58, "GT": 59}
    movement_type = row.get("movement_type")
    if movement_type not in type_ids:
        issues.append(f"Tipo de movimiento sin correspondencia definida: {movement_type}")
    try:
        raw_quantity = row.get("quantity")
        if isinstance(raw_quantity, bool):
            raise ValueError()
        quantity = Decimal(str(raw_quantity))
        if not quantity.is_finite() or quantity <= 0:
            raise ValueError()
        if quantity != quantity.to_integral_value():
            pending.append("Confirmar que mySim acepta la cantidad fraccionaria; no redondear")
    except (InvalidOperation, ValueError, TypeError):
        issues.append("Cantidad ausente o no positiva/finita")
    # Requisitos preliminares para GR/GI/GT; no generan un payload de envío.
    required = {"GR": {"destination"}, "GI": {"source", "destination"}, "GT": {"source", "destination"}}
    for side, id_field, data_field, label in (
        ("source", "from_location_id", "source_location_data", "origen"),
        ("destination", "to_location_id", "destination_location_data", "destino"),
    ):
        location_id = row.get(id_field)
        if location_id is None:
            if side in required.get(movement_type, set()):
                issues.append(f"Falta ubicación de {label}")
            continue
        if not positive_id(location_id):
            issues.append(f"ID local de {label} inválido")
            continue
        location = row.get(data_field)
        if not isinstance(location, dict) or str(location.get('id')) != str(location_id):
            issues.append(f"La ubicación local de {label} {location_id} no existe")
        elif location.get('is_active') is False:
            issues.append(f"La ubicación local de {label} {location_id} está inactiva")
        pending.append(f"Resolver ubicación local de {label} {location_id} a ID mySim y comprobarla")
    if movement_type == "GT" and row.get('from_location_id') == row.get('to_location_id') and row.get('from_location_id') is not None:
        issues.append("Transferencia con el mismo origen y destino")
    if data.get('mysim_movement_id') or data.get('mysim_synced_at') or data.get('mysim_sync_status') in {'sent', 'synced'}:
        issues.append("Hay indicios de sincronización previa; conciliar para evitar duplicados")
    if row.get('outbox_status') == 'processing':
        waits.append("Entrada en procesamiento; revisar quién la tiene reclamada")
    if row.get('outbox_status') == 'failed':
        waits.append("Estado failed; falta definir su recuperación")
    if not row.get('retry_due', True):
        waits.append("Todavía no se ha cumplido next_retry_at")
    pending.append("Comprobar duplicados en el historial mySim; el último movimiento solo no basta")
    return {
        'issues': issues, 'pending': pending, 'waits': waits,
        'local_data_ok': not issues,
        'mysim_movement_type_id': type_ids.get(movement_type),
    }


class ReferenceResolver:
    """Consulta referencias una vez por ejecución. No persiste correspondencias."""
    def __init__(self, cfg: MySimConfig):
        self.cfg = cfg
        self.cache = {}

    def lookup(self, entity: str, params: dict, expected_field: str, expected_value: Any) -> dict:
        key = (entity, expected_field, str(expected_value))
        if key in self.cache:
            return self.cache[key]
        try:
            rows = query_with_retries(self.cfg, {"entity": entity, "limit": "2", **params})
            if not rows:
                result = {'status': 'SIN_COINCIDENCIAS'}
            elif len(rows) != 1:
                result = {'status': 'AMBIGUO'}
            elif str(rows[0].get(expected_field)) != str(expected_value) or not positive_id(rows[0].get('id')):
                result = {'status': 'RESPUESTA_NO_COINCIDE'}
            elif rows[0].get('enabled') is False or str(rows[0].get('deleted', 0)) == '1':
                result = {'status': 'INACTIVO'}
            else:
                result = {'status': 'VERIFICADO', 'id': int(rows[0]['id']), 'row': rows[0]}
        except LookupError as exc:
            result = {'status': 'NO_DETERMINADO', 'detail': str(exc)}
        self.cache[key] = result
        return result

    def user(self, user_id: Any) -> dict:
        print(f"  Verificando autor mySim id={user_id}", flush=True)
        return self.lookup('accounts', {'id': str(user_id)}, 'id', user_id)

    def location(self, local: dict, refs: list) -> dict:
        metadata = {'local_id': local.get('id'), 'local_code': local.get('code')}
        ref, error = select_location_reference(local.get('id'), refs)
        if error:
            return {**metadata, 'status': error}
        external_id = str(ref.get('external_id') or '').strip()
        metadata.update(reference_id=ref.get('id'), external_id=external_id)
        if not positive_id(external_id):
            return {**metadata, 'status': 'EXTERNAL_ID_INVALIDO'}
        print(f"  Verificando ubicación local={local['id']} -> mySim id={external_id}", flush=True)
        result = self.lookup('location', {'id': str(int(external_id))}, 'id', int(external_id))
        expected_code = ref.get('external_code') or local.get('code')
        if result['status'] == 'VERIFICADO':
            actual_code = result['row'].get('locationCode')
            metadata.update(external_code=expected_code, actual_code=actual_code)
            if not expected_code:
                result = {**result, 'status': 'FALTA_CODIGO_PARA_CONTRASTAR'}
            elif actual_code != expected_code:
                result = {**result, 'status': 'CODIGO_NO_COINCIDE',
                          'detail': f"Código esperado={expected_code}; código mySim={actual_code}"}
        return {**result, **metadata}


def select_location_reference(local_id: Any, refs: list) -> tuple[dict | None, str | None]:
    # Una principal única tiene prioridad. Sin principal, debe haber un solo vínculo.
    candidates = [ref for ref in refs if isinstance(ref, dict)
                  and str(ref.get('location_id')) == str(local_id)
                  and str(ref.get('source_system', '')).strip().lower() == 'mysim']
    if not candidates:
        return None, 'SIN_VINCULO_MYSIM'
    primary = [ref for ref in candidates if ref.get('is_primary') is True]
    if len(primary) > 1:
        return None, 'VARIOS_VINCULOS_PRINCIPALES'
    if len(primary) == 1:
        return primary[0], None
    if len(candidates) == 1:
        return candidates[0], None
    return None, 'VARIOS_VINCULOS_SIN_PRINCIPAL'


def resolve_references(row: dict, resolver: ReferenceResolver) -> dict:
    references = {}
    data = row.get('movement_data') or {}
    user_id = data.get('mysim_user_id')
    if positive_id(user_id):
        references['user'] = resolver.user(user_id)
    else:
        references['user'] = {'status': 'FALTA_ID'}
    for side, field in [('source', 'source_location_data'), ('destination', 'destination_location_data')]:
        location = row.get(field)
        if not isinstance(location, dict):
            references[side] = {'status': 'SIN_UBICACION_LOCAL'}
        else:
            references[side] = resolver.location(location, row.get(side + '_external_refs') or [])
    return references


def show_pending_movements(part_code: str, cfg: MySimConfig, details: bool = False) -> None:
    print(f"\nOUTBOX: movimientos sin sincronizar de {part_code} (fecha ASC)", flush=True)
    rows = list_pending_movements(part_code)
    if not rows:
        print("No hay entradas pendientes para este código con action=sync y target_system=mysim.", flush=True)
        return
    print(f"Entradas: {len(rows)} | movimientos distintos: {len({r['movement_id'] for r in rows})}", flush=True)
    print("VALIDACIÓN PRELIMINAR: no hay envíos ni cambios de estado. Se usan vínculos location_external_refs y se verifican ID y código en mySim.", flush=True)
    counts = {}
    for row in rows:
        counts[row['movement_id']] = counts.get(row['movement_id'], 0) + 1
    resolver = ReferenceResolver(cfg)
    references_ok = 0
    local_ok = 0
    first = rows[0]['movement_id']
    for index, row in enumerate(rows, 1):
        validation = validate_movement(row)
        if counts[row['movement_id']] > 1:
            validation['issues'].append("Varias entradas de outbox para el mismo movimiento; revisar duplicación")
            validation['local_data_ok'] = False
        if validation['local_data_ok']:
            local_ok += 1
        state = "DATOS_LOCALES_OK" if validation['local_data_ok'] else "FALTAN_DATOS_O_REVISION"
        print(f"\n[{index}] outbox={row['outbox_id']} | movimiento={row['movement_id']} | estado={row['outbox_status']} | {state}", flush=True)
        print(f"  Fecha: {row['movement_date']} | tipo={row['movement_type']} (mySim={validation['mysim_movement_type_id']}) | cantidad={row['quantity']}", flush=True)
        print(f"  Item local={row['local_item_id']} | origen={row['from_location_id']} | destino={row['to_location_id']} | autor mySim={(row.get('movement_data') or {}).get('mysim_user_id')}", flush=True)
        print(f"  Reintentos históricos={row['retries']} | próximo reintento={row['next_retry_at']}", flush=True)
        for issue in validation['issues']:
            print(f"  REVISAR: {issue}", flush=True)
        for wait in validation['waits']:
            print(f"  ESPERA: {wait}", flush=True)
        references = resolve_references(row, resolver)
        all_verified = references['user']['status'] == 'VERIFICADO'
        for side, label, id_field in [('source', 'origen', 'from_location_id'), ('destination', 'destino', 'to_location_id')]:
            ref = references[side]
            if row.get(id_field) is None:
                continue
            if ref['status'] != 'VERIFICADO':
                all_verified = False
            print(f"  UBICACIÓN {label}: local={row[id_field]} | código={ref.get('local_code')} | mySim={ref.get('id')} | {ref['status']}", flush=True)
            if ref.get('detail'):
                print(f"    {ref['detail']}", flush=True)
        user_ref = references['user']
        user_name = (user_ref.get('row') or {}).get('fullName')
        print(f"  AUTOR: mySim={user_ref.get('id')} | nombre={user_name} | {user_ref['status']}", flush=True)
        if user_ref.get('detail'):
            print(f"    {user_ref['detail']}", flush=True)
        if all_verified and validation['local_data_ok']:
            references_ok += 1
        for pending in validation['pending']:
            if pending.startswith(('Comprobar usuario', 'Resolver ubicación')):
                continue
            print(f"  COMPROBACIÓN PENDIENTE: {pending}", flush=True)
        if index > 1:
            print(f"  SECUENCIA: espera hasta resolver las entradas anteriores; primera={first}", flush=True)
        else:
            print("  SECUENCIA: primera entrada a resolver; todavía no preparada para envío", flush=True)
        if details:
            print(json.dumps(row, ensure_ascii=False, indent=2, default=str), flush=True)
    print(f"\nRESUMEN: {local_ok}/{len(rows)} entradas con datos locales completos; {len(rows)-local_ok} requieren revisión.", flush=True)
    print(f"Datos locales y referencias guardadas verificados: {references_ok}/{len(rows)}.", flush=True)
    print("Preparadas para envío: 0. Falta comprobar duplicados y construir el payload; el envío sigue desactivado.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Paso 1: comprobar un artículo en mySim (solo lectura).")
    parser.add_argument("--part-code", required=True, help="Código exacto del artículo (partId).")
    parser.add_argument("--details", action="store_true", help="Mostrar también el JSON completo de cada entrada local.")
    args = parser.parse_args()
    try:
        cfg = MySimConfig.from_env()
        item = find_item(cfg, args.part_code)
    except requests.RequestException as exc:
        # No imprimir la excepción completa: puede contener detalles de la petición.
        print(f"ERROR: Fallo de conexión ({type(exc).__name__}); existencia no determinada.", file=sys.stderr)
        return 2
    except (LookupError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    if item is None:
        print("SIN COINCIDENCIAS: mySim respondió correctamente y no devolvió el artículo.")
        return 1
    print(f"ENCONTRADO: partId={item['partId']} | mySim id={item['id']}")
    print(json.dumps(item, ensure_ascii=False, indent=2), flush=True)
    try:
        movement = get_last_movement(cfg, int(item["id"]))
    except LookupError as exc:
        print(f"ERROR AL CONSULTAR MOVIMIENTOS: {exc}", file=sys.stderr)
        return 2
    if movement is None:
        print("SIN MOVIMIENTOS: consulta válida sin resultados para este artículo.", flush=True)
    else:
        print(f"ÚLTIMO MOVIMIENTO: id={movement['id']} | fecha={movement['date']}", flush=True)
        print(json.dumps(movement, ensure_ascii=False, indent=2), flush=True)
    try:
        show_pending_movements(args.part_code, cfg, details=args.details)
    except Exception as exc:
        # SQLAlchemy puede incluir credenciales/parámetros en errores completos.
        print(f"ERROR AL LEER OUTBOX: {type(exc).__name__}. Revisar conexión y esquema local. No se modificó la cola.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\nConsulta detenida por el usuario.", flush=True)
        raise SystemExit(130)
