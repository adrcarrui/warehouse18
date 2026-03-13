from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal, Optional

Side = Literal["A", "B"]
Route = tuple[Side, Side]


@dataclass(frozen=True)
class DummyDoorConfig:
    door_id: str
    antenna_a: int
    antenna_b: int
    movement_map: dict[Route, str]
    cross_window_seconds: int = 3
    cooldown_seconds: int = 3

    def side_for_antenna(self, antenna: int) -> Optional[Side]:
        if antenna == self.antenna_a:
            return "A"
        if antenna == self.antenna_b:
            return "B"
        return None


@dataclass
class DoorCrossState:
    ref_key: str
    last_side: Side
    first_seen_at: datetime
    last_seen_at: datetime
    cooldown_until: Optional[datetime] = None


@dataclass(frozen=True)
class DoorDecision:
    movement_code: str
    route: Route
    first_side: Side
    second_side: Side
    completed_at: datetime


class DummyDoorEngine:
    def __init__(self, cfg: DummyDoorConfig):
        self.cfg = cfg

    def process(
        self,
        *,
        state_by_ref: dict[str, DoorCrossState],
        ref_key: str,
        antenna: int,
        now: datetime,
    ) -> Optional[DoorDecision]:
        side = self.cfg.side_for_antenna(antenna)
        if side is None:
            return None

        st = state_by_ref.get(ref_key)
        if st is None:
            state_by_ref[ref_key] = DoorCrossState(
                ref_key=ref_key,
                last_side=side,
                first_seen_at=now,
                last_seen_at=now,
            )
            return None

        if st.cooldown_until is not None and now < st.cooldown_until:
            return None

        window = timedelta(seconds=self.cfg.cross_window_seconds)
        if now - st.last_seen_at > window:
            state_by_ref[ref_key] = DoorCrossState(
                ref_key=ref_key,
                last_side=side,
                first_seen_at=now,
                last_seen_at=now,
            )
            return None

        if st.last_side == side:
            st.last_seen_at = now
            return None

        route: Route = (st.last_side, side)
        movement_code = self.cfg.movement_map.get(route)
        if not movement_code:
            st.last_side = side
            st.last_seen_at = now
            return None

        state_by_ref[ref_key] = DoorCrossState(
            ref_key=ref_key,
            last_side=side,
            first_seen_at=now,
            last_seen_at=now,
            cooldown_until=now + timedelta(seconds=self.cfg.cooldown_seconds),
        )

        return DoorDecision(
            movement_code=movement_code,
            route=route,
            first_side=route[0],
            second_side=route[1],
            completed_at=now,
        )