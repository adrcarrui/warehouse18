from __future__ import annotations

import logging
import socket
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional

log = logging.getLogger("warehouse18.rfid.low_level")


@dataclass(frozen=True)
class LowLevelTagRead:
    epc: str
    antenna: int
    rssi_raw: int
    seen_at: datetime
    cmd: int
    raw: bytes
    freq_ant: int
    ant_in_block: int
    step_val: int


class LowLevelRFIDReader:
    """
    Reader TCP de bajo nivel para fast inventory 0x8A con secuencia:
      6C01 -> 8A
      6C00 -> 8A

    Regla práctica validada en tus pruebas:
    - step 0x01 -> bloque físico 9..16
    - step 0x00 -> bloque físico 1..8
    """

    def __init__(
        self,
        *,
        host: str,
        port: int,
        addr: int = 0x01,
        recv_timeout: float = 0.20,
        read_window_s: float = 0.35,
        step_delay_s: float = 0.03,
        loop_sleep_s: float = 0.12,
    ) -> None:
        self.host = host
        self.port = port
        self.addr = addr
        self.recv_timeout = recv_timeout
        self.read_window_s = read_window_s
        self.step_delay_s = step_delay_s
        self.loop_sleep_s = loop_sleep_s

        self._sock: Optional[socket.socket] = None
        self._rx = bytearray()

    # --------------------------
    # socket lifecycle
    # --------------------------

    def connect(self) -> None:
        self.close()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.recv_timeout)
        sock.connect((self.host, self.port))
        self._sock = sock
        self._rx.clear()

    def close(self) -> None:
        if self._sock is not None:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None
        self._rx.clear()

    # --------------------------
    # public loop
    # --------------------------

    def read_cycle(self) -> list[LowLevelTagRead]:
        if self._sock is None:
            raise RuntimeError("Reader not connected")

        out: list[LowLevelTagRead] = []
        out.extend(self._do_step(0x01))
        out.extend(self._do_step(0x00))
        return out

    def iter_forever(self) -> Iterator[LowLevelTagRead]:
        while True:
            for read in self.read_cycle():
                yield read
            time.sleep(self.loop_sleep_s)

    # --------------------------
    # protocol helpers
    # --------------------------

    def _checksum(self, frame_wo_check: bytes) -> int:
        return (~sum(frame_wo_check) + 1) & 0xFF

    def _build_cmd(self, cmd: int, data: bytes = b"") -> bytes:
        length = len(data) + 3
        frame = bytearray([0xA0, length, self.addr, cmd])
        frame.extend(data)
        frame.append(self._checksum(frame))
        return bytes(frame)

    def _cmd_6c(self, val: int) -> bytes:
        return self._build_cmd(0x6C, bytes([val]))

    def _cmd_inventory(self) -> bytes:
        data = bytes([
            0x00, 0x01,
            0x01, 0x01,
            0x02, 0x01,
            0x03, 0x01,
            0x04, 0x01,
            0x05, 0x01,
            0x06, 0x01,
            0x07, 0x01,
            0x00,
            0x01,
        ])
        return self._build_cmd(0x8A, data)

    def _extract_frames(self) -> list[bytes]:
        frames: list[bytes] = []
        i = 0

        while True:
            while i < len(self._rx) and self._rx[i] != 0xA0:
                i += 1

            if i >= len(self._rx):
                del self._rx[:]
                return frames

            if len(self._rx) - i < 2:
                if i > 0:
                    del self._rx[:i]
                return frames

            length = self._rx[i + 1]
            total = 2 + length

            if len(self._rx) - i < total:
                if i > 0:
                    del self._rx[:i]
                return frames

            frames.append(bytes(self._rx[i:i + total]))
            i += total

    def _verify(self, frame: bytes) -> bool:
        return len(frame) >= 5 and self._checksum(frame[:-1]) == frame[-1]

    # --------------------------
    # antenna math
    # --------------------------

    @staticmethod
    def _ant_in_block(freq_ant: int, rssi_raw: int) -> int:
        antenna_id_base = freq_ant & 0x03
        upper_half = 1 if (rssi_raw & 0x80) else 0
        if upper_half == 0:
            return 1 + antenna_id_base
        return 5 + antenna_id_base

    @staticmethod
    def _physical_antenna_from_step(step_val: int, ant_in_block: int) -> int:
        # Validado por tus pruebas actuales
        if step_val == 0x01:
            return 8 + ant_in_block  # 9..16
        return ant_in_block          # 1..8

    # --------------------------
    # reading
    # --------------------------

    def _do_step(self, step_val: int) -> list[LowLevelTagRead]:
        assert self._sock is not None

        self._rx.clear()

        self._sock.sendall(self._cmd_6c(step_val))
        time.sleep(self.step_delay_s)
        self._sock.sendall(self._cmd_inventory())

        out: list[LowLevelTagRead] = []
        t0 = time.time()

        while time.time() - t0 < self.read_window_s:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    break
                self._rx.extend(chunk)

                for frame in self._extract_frames():
                    if not self._verify(frame):
                        continue

                    parsed = self._parse_8a(step_val, frame)
                    if parsed is not None:
                        out.append(parsed)

            except socket.timeout:
                break

        return out

    def _parse_8a(self, step_val: int, frame: bytes) -> Optional[LowLevelTagRead]:
        if len(frame) < 5 or frame[0] != 0xA0 or frame[3] != 0x8A:
            return None

        # paquete resumen final del comando
        if frame[1] == 0x0A:
            return None

        payload = frame[4:-1]
        if len(payload) < 6:
            return None

        freq_ant = payload[0]
        epc = payload[3:-1].hex().upper()
        rssi_raw = payload[-1]

        if len(epc) < 4:
            return None

        ant_in_block = self._ant_in_block(freq_ant, rssi_raw)
        physical_antenna = self._physical_antenna_from_step(step_val, ant_in_block)

        return LowLevelTagRead(
            epc=epc,
            antenna=physical_antenna,
            rssi_raw=rssi_raw & 0x7F,
            seen_at=datetime.now(timezone.utc),
            cmd=0x8A,
            raw=frame,
            freq_ant=freq_ant,
            ant_in_block=ant_in_block,
            step_val=step_val,
        )