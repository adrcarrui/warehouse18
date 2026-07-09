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
    quantity: int = 1

    # Device-specific cuando destination es Device
    unistall_part: Optional[str] = None          # API field: "unistallPart"
    why_is_it_uninstalled: Optional[str] = None  # API field: "whyIsItUninstalled"
    dest_uninstalled_part: Optional[int] = None  # API field: "destUninstalledPart"
    uninstalled_by: Optional[int] = None         # API field: "uninstalledBy"

    def validate(self) -> None:
        if self.quantity < 1:
            raise ValueError("quantity debe ser >= 1.")

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

        is_device_destination = (
            str(self.destination or "").strip().lower() == "device"
            or str(self.destination or "").strip() == "1"
        )

        has_device_workflow_data = any(
            value is not None
            for value in (
                self.unistall_part,
                self.why_is_it_uninstalled,
                self.dest_uninstalled_part,
                self.uninstalled_by,
            )
        )

        if is_device_destination or has_device_workflow_data:
            missing = []

            if not self.unistall_part:
                missing.append("unistall_part")

            if not self.why_is_it_uninstalled:
                missing.append("why_is_it_uninstalled")

            if self.dest_uninstalled_part is None:
                missing.append("dest_uninstalled_part")

            if self.uninstalled_by is None:
                missing.append("uninstalled_by")

            if missing:
                raise ValueError(f"Device workflow requiere: {', '.join(missing)}")