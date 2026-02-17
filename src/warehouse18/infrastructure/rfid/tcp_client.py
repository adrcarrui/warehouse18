# src/warehouse18/infrastructure/rfid/tcp_client.py

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Iterator, Optional

from warehouse18.infrastructure.rfid.ddct_protocol import (
    build_frame,
    iter_frames_from_bytes,
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
    Cliente TCP simple:
    - conecta a host:port
    - send_cmd() envía tramas DDCT
    - frames() produce frames completos (ya reensamblados) usando Len+checksum
    """

    def __init__(self, cfg: TCPConnectionConfig):
        self.cfg = cfg
        self._sock: Optional[socket.socket] = None

    @property
    def is_connected(self) -> bool:
        return self._sock is not None

    def connect(self) -> None:
        if self._sock:
            return
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.cfg.connect_timeout)
        s.connect((self.cfg.host, self.cfg.port))
        s.settimeout(1.0)  # timeout lectura
        self._sock = s


    def close(self) -> None:
        if not self._sock:
            return
        try:
            self._sock.close()
        finally:
            self._sock = None

    def send_cmd(self, cmd: int, data: bytes = b"", addr: int = 0xFF) -> None:
        if not self._sock:
            raise RuntimeError("RFIDReaderTCP no está conectado")
        frame = build_frame(cmd=cmd, data=data, addr=addr)
        self._sock.sendall(frame)

    def _recv_chunks(self) -> Iterator[bytes]:
        if not self._sock:
            raise RuntimeError("RFIDReaderTCP no está conectado")
        while True:
            chunk = self._sock.recv(self.cfg.recv_size)
            if not chunk:
                raise ConnectionError("Socket cerrado por el lector")
            yield chunk

    def frames(self) -> Iterator[bytes]:
        """
        Itera frames completos verificados.
        """
        return iter_frames_from_bytes(self._recv_chunks())
