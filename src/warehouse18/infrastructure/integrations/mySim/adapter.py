from __future__ import annotations

from typing import Any, Optional, List, Dict

from .client import MySimClient, rows_normalized
from warehouse18.application.mySim.movement_request import MovementRequest

# ---------------------------------------------------------
# Mapping interno dominio → IDs reales de mySim
#
# Esto permite usar:
#   --type "Good issue"
# en vez de:
#   --movement-type-id 58
# ---------------------------------------------------------
MYSIM_MOVEMENT_TYPE_IDS_BY_LABEL = {
    "Good issue": 58,      # GI
    "Good receipt": 57,    # GR
    "Good transfer": 59,   # GT
    "Good tracking": 234,  # Good Tracking
}


class MySimAdapter:
    """
    Adaptador de infraestructura entre tu dominio (warehouse18)
    y la API pública de mySim (/api/v1/pub).
    """

    def __init__(self, client: MySimClient):
        self.client = client

    # =========================================================
    # USERS (accounts)
    # =========================================================

    def get_all_users(self, *, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Uso:
            mysim users list --limit 100
        """
        return rows_normalized(self.client.get(entity="accounts", limit=limit))

    def get_user_by_id(self, user_id: int | str) -> Optional[Dict[str, Any]]:
        """
        Uso:
            mysim users get --id 123
        """
        rows = rows_normalized(self.client.get(entity="accounts", id=user_id, limit=1))
        return rows[0] if rows else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Uso:
            mysim users get --email user@company.com
        """
        safe = email.replace("'", "''")
        rows = rows_normalized(
            self.client.get(entity="accounts", extra_query=f"t.email = '{safe}'", limit=1)
        )
        return rows[0] if rows else None

    # =========================================================
    # LOCATIONS
    # =========================================================

    def get_all_locations(self, *, entity: str = "location", limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Devuelve localizaciones desde mySim.

        En este mySim la entidad real es 'location' (singular).
        Normaliza keys a un formato consistente para el resto de la app:
        - code, name, fullName, description
        """
        rows = rows_normalized(self.client.get(entity=entity, limit=limit))
        return [self._normalize_location_row(r) for r in rows]


    @staticmethod
    def _normalize_location_row(r: Dict[str, Any]) -> Dict[str, Any]:
        """
        mySim puede devolver campos tipo locationCode/locationName/etc.
        Aquí los homogeneizamos a code/name/fullName/description.
        """
        return {
            "id": r.get("id"),
            "code": r.get("locationCode") or r.get("code"),
            #"name": r.get("locationName") or r.get("name"),
            #"fullName": r.get("locationFullName") or r.get("fullName"),
            #"description": r.get("description") or r.get("locationDescription"),
            # por si quieres acceder al raw:
            #"_raw": r,
        }

    # =========================================================
    # PARTS
    # =========================================================

    def get_part_id_by_part_code(self, part_id: str) -> Optional[int]:
        """
        Uso interno:
            Convierte partCode → ID interno mySim.

        Se usa automáticamente cuando llamas:
            mysim parts upload-movement --part-code 235-0839
        """
        safe = part_id.replace("'", "''")
        resp = self.client.get(
            entity="parts",
            extra_query=f"t.partId='{safe}'",
            fields="id",
            limit=1,
        )
        rows = rows_normalized(resp)
        if not rows:
            return None

        val = rows[0].get("id")
        try:
            return int(val) if val is not None else None
        except Exception:
            return None

    def get_part_by_id(self, part_db_id: int) -> Optional[Dict[str, Any]]:
        """
        Uso:
            mysim parts get --part-db-id 3342
        """
        rows = rows_normalized(
            self.client.get(
                entity="parts",
                extra_query=f"t.id='{part_db_id}'",
                limit=1,
            )
        )
        return rows[0] if rows else None

    def get_part_by_part_code(self, part_code: str) -> Optional[Dict[str, Any]]:
        """
        Uso:
            mysim parts get --part-code 235-0839
        """
        safe = part_code.replace("'", "''")
        rows = rows_normalized(
            self.client.get(
                entity="parts",
                extra_query=f"t.partId='{safe}'",
                limit=1,
            )
        )
        return rows[0] if rows else None

    # =========================================================
    # MOVEMENTS (CONSULTA)
    # =========================================================

    def get_item_movements(
        self,
        *,
        item_id: int | str,
        item_entity: str = "Parts",
        limit: int = 200,
        newest_first: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Uso:
            mysim parts movements --part-code 235-0839
            mysim parts movements --part-code 235-0839 --limit 10
            mysim parts movements --part-code 235-0839 --no-newest-first
        """
        safe_item_id = str(item_id).replace("'", "''")
        safe_entity = item_entity.replace("'", "''")
        extra = f"t.idCol='{safe_item_id}' AND t.entity='{safe_entity}'"

        resp = self.client.get(
            entity="movement",
            extra_query=extra,
            order_by="t.lastUpdated",
            order_type="DESC" if newest_first else "ASC",
            limit=limit,
        )
        return rows_normalized(resp)

    def get_last_item_movement(self, *, item_id: int | str, item_entity: str = "Parts") -> Optional[Dict[str, Any]]:
        """
        Uso:
            mysim parts last-movement --part-code 235-0839
        """
        rows = self.get_item_movements(item_id=item_id, item_entity=item_entity, limit=1)
        return rows[0] if rows else None

    # =========================================================
    # MOVEMENTS (CREACIÓN)
    # =========================================================

    def create_movement(self, req: MovementRequest) -> Dict[str, Any]:
        """
        Crea un movimiento usando:
            POST /api/v1/pub/set?entity=movement

        Uso CLI normal:
            mysim parts upload-movement \
              --part-code 235-0839 \
              --type "Good issue" \
              --dest 1 \
              --done-by 5628

        Uso CLI con uninstall/install:
            mysim parts upload-movement \
              --part-code 235-0839 \
              --type "Good issue" \
              --dest 1 \
              --uninstall-part-code 2806 \
              --dest-uninstalled-part 6 \
              --uninstalled-by 5628 \
              --why-uninstalled "Maintenance"
        """

        req.validate()

        # -----------------------------------------------------
        # 1) Convertir MovementType de dominio → ID mySim
        # -----------------------------------------------------
        movement_type_id = None

        if getattr(req, "movement_type_id", None) is not None:
            movement_type_id = int(req.movement_type_id)
        else:
            label = req.movement_type.value
            movement_type_id = MYSIM_MOVEMENT_TYPE_IDS_BY_LABEL.get(label)

        if movement_type_id is None:
            raise ValueError(f"MovementType no mapeado a ID mySim: {req.movement_type}")

        # -----------------------------------------------------
        # 2) Construir row plano (lo que espera /set)
        # -----------------------------------------------------
        row: Dict[str, Any] = {
            "id": 0,
            "entity": "Parts",
            "idCol": int(req.part_db_id),
            "movementType": movement_type_id,
            "quantity": int(getattr(req, "quantity", 1) or 1),
            "movementDescription": req.description or "",
        }

        if req.origin:
            row["sourceLocation"] = int(req.origin)

        if req.destination:
            row["destinationLocation"] = int(req.destination)

        if req.done_by:
            row["doneBy"] = int(req.done_by)

        if req.date:
            row["date"] = req.date

        # -----------------------------------------------------
        # 3) Uninstall/install flow (opcional)
        # -----------------------------------------------------
        uninstall_part_id = getattr(req, "uninstall_part_id", None)

        # Compatibilidad con tu antiguo typo
        if uninstall_part_id is None and getattr(req, "unistall_part", None) is not None:
            raw = str(req.unistall_part)
            if raw.isdigit():
                uninstall_part_id = int(raw)
            else:
                uninstall_part_id = self.get_part_id_by_part_code(raw)

        if uninstall_part_id is not None:
            row["uninstallPart"] = int(uninstall_part_id)
            row["unistallPart"] = int(uninstall_part_id)

            if req.dest_uninstalled_part is not None:
                row["destUninstalledPart"] = int(req.dest_uninstalled_part)

            if req.uninstalled_by is not None:
                row["uninstalledBy"] = int(req.uninstalled_by)

            if req.why_is_it_uninstalled:
                row["whyIsItUninstalled"] = req.why_is_it_uninstalled

        # -----------------------------------------------------
        # 4) Enviar vía SET
        # -----------------------------------------------------
        print("ROW SENT TO MYSIM /set:", row)
        return self.client.set(entity="movement", objects=[row])