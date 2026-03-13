from dataclasses import dataclass
from typing import Optional

from .movement_types import MovementType


@dataclass(frozen=True)
class MovementRequest:
    part_db_id: int
    movement_type: MovementType
    destination: Optional[str] = None
    origin: Optional[str] = None
    description: str = ""

    done_by: Optional[str] = None
    date: Optional[str] = None  

    # Device-specific (when destination is Device)
    unistall_part: Optional[str] = None          # API field: "unistallPart"
    why_is_it_uninstalled: Optional[str] = None  # API field: "whyIsItUninstalled"
    dest_uninstalled_part: Optional[int] = None  # API field: "destUninstalledPart"
    uninstalled_by: Optional[int] = None         # API field: "uninstalledBy"

    def validate(self) -> None:
        if self.movement_type == MovementType.GOOD_RECEIPT:
            if not self.origin or not self.destination:
                raise ValueError("Good receipt requiere origin y destination.")

        elif self.movement_type in (
            MovementType.GOOD_ISSUE,
            MovementType.GOOD_TRANSFER,
        ):
            if not self.destination:
                raise ValueError(f"{self.movement_type.value} requiere destination.")

        elif self.movement_type == MovementType.GOOD_TRACKING:
            if not self.description.strip():
                raise ValueError("Good tracking requiere description.")

        if self.dest_uninstalled_part is not None or self.unistall_part is not None:
        # Si empiezas a usar estos campos, exige todos los obligatorios del workflow
            missing = []
            if not self.unistall_part:
                missing.append("unistall_part")
            if not self.why_is_it_uninstalled:
                missing.append("why_is_it_uninstalled")
            if not self.dest_uninstalled_part:
                missing.append("dest_uninstalled_part")
            if not self.uninstalled_by:
                missing.append("uninstalled_by")

            if missing:
                raise ValueError(f"Device workflow requiere: {', '.join(missing)}")