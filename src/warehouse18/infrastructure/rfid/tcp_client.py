# src/warehouse18/infrastructure/rfid/tcp_client.py

from __future__ import annotations

import socket
import time
from dataclasses import dataclass
from typing import Iterator, Optional

from warehouse18.infrastructure.rfid.ddct_protocol import (
    HEAD,
    expected_total_len,
    verify_frame,
    build_frame,
)

DEFAULT_RECV_SIZE = 4096


@dataclass
class TCPConnectionConfig:
    host: str
    port: int
    connect_timeout: float = 3.0
    recv_size: int = DEFAULT_RECV_SIZE


class RFIDReaderTCP:
    """
    Cliente TCP:
    - connect()
    - send_cmd()
    - recv_frames(window_s): lee bytes durante una ventana y devuelve frames completos
      usando buffer persistente (NO se suicida por timeout)
    """

    def __init__(self, cfg: TCPConnectionConfig):
        self.cfg = cfg
        self._sock: Optional[socket.socket] = None
        self._rx_buf = bytearray()

    @property
    def is_connected(self) -> bool:
        return self._sock is not None

    def connect(self) -> None:
        if self._sock:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.cfg.connect_timeout)
        s.connect((self.cfg.host, self.cfg.port))
        s.settimeout(0.2)  # timeout corto para polling
        self._sock = s

    def close(self) -> None:
        if not self._sock:
            return
        try:
            self._sock.close()
        finally:
            self._sock = None
            self._rx_buf.clear()

    def send_cmd(self, cmd: int, data: bytes = b"", addr: int = 0xFF) -> None:
        if not self._sock:
            raise RuntimeError("RFIDReaderTCP no está conectado")
        frame = build_frame(cmd=cmd, data=data, addr=addr)
        self._sock.sendall(frame)

    def _pop_frames_from_buffer(self) -> list[bytes]:
        frames: list[bytes] = []

        while True:
            # buscar HEAD
            try:
                i = self._rx_buf.index(HEAD)
            except ValueError:
                self._rx_buf.clear()
                break

            # tirar basura previa
            if i > 0:
                del self._rx_buf[:i]

            total = expected_total_len(self._rx_buf)
            if total is None:
                break
            if len(self._rx_buf) < total:
                break

            frame = bytes(self._rx_buf[:total])
            del self._rx_buf[:total]

            if verify_frame(frame):
                frames.append(frame)
            else:
                # checksum malo: re-sincroniza buscando el siguiente HEAD
                continue

        return frames

    def recv_frames(self, window_s: float = 0.8) -> Iterator[bytes]:
        """
        Lee del socket durante window_s y va devolviendo frames completos.
        Importante: mantiene buffer entre llamadas.
        """
        if not self._sock:
            raise RuntimeError("RFIDReaderTCP no está conectado")

        end = time.monotonic() + window_s

        while time.monotonic() < end:
            try:
                chunk = self._sock.recv(self.cfg.recv_size)
            except socket.timeout:
                # no hay más datos ahora mismo
                break

            if not chunk:
                raise ConnectionError("Socket cerrado por el lector")

            self._rx_buf.extend(chunk)

            for fr in self._pop_frames_from_buffer():
                yield fr