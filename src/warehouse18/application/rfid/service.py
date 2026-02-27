# src/warehouse18/infrastructure/rfid/service.py

"""RFID reader service (TCP -> events).

Objetivo (MVP):
  - Conectar a un lector RFID por TCP (protocolo DDCT)
  - Enviar un comando de inventario (0x8A) al iniciar
  - Leer frames, parsear tags y publicar eventos a un callback (normalmente SSE)

No toca base de datos. Solo genera eventos para la UI/monitor.
"""

from __future__ import annotations
import logging
log = logging.getLogger("warehouse18.rfid.service")
import asyncio
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from warehouse18.domain.rfid import RFIDReadEvent, ReaderStatusEvent
from warehouse18.infrastructure.rfid.commands import build_8a_fast_switch_inventory_payload
from warehouse18.infrastructure.rfid.parser import decode_frame, try_parse_tag_from_inventory
from warehouse18.infrastructure.rfid.tcp_client import RFIDReaderTCP, TCPConnectionConfig

Publisher = Callable[[dict[str, Any]], Any]


@dataclass(frozen=True)
class RFIDServiceConfig:
    reader_id: str = "reader-1"
    host: str = "127.0.0.1"
    port: int = 4001
    ants: list[int] | None = None  # 1..16
    repeat: int = 0x01
    reconnect_seconds: float = 2.0
    inventory_cmd: int = 0x8A

    def __post_init__(self):
        if self.ants is None:
            object.__setattr__(self, "ants", list(range(1, 17)))


class RFIDReaderService:
    """Servicio en background (thread) para leer el lector y publicar eventos."""

    def __init__(
        self,
        cfg: RFIDServiceConfig,
        *,
        publish: Publisher,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        self.cfg = cfg
        self._publish = publish
        self._loop = loop
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._reader: Optional[RFIDReaderTCP] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="RFIDReaderService", daemon=True)
        self._thread.start()

    def stop(self, *, timeout: float = 2.0) -> None:
        self._stop.set()
        try:
            if self._reader:
                self._reader.close()
        except Exception:
            pass
        if self._thread:
            self._thread.join(timeout=timeout)

    def _publish_from_thread(self, payload: dict[str, Any]) -> None:
        try:
            out = self._publish(payload)
            if asyncio.iscoroutine(out):
                if self._loop is None:
                    asyncio.run(out)
                else:
                    asyncio.run_coroutine_threadsafe(out, self._loop)
        except Exception:
            # MVP: no matamos el hilo por un fallo de publish
            pass

    def _status(self, status: str, message: str | None = None) -> None:
        ev = ReaderStatusEvent(
            reader_id=self.cfg.reader_id,
            status=status,
            at=datetime.now(timezone.utc),
            message=message,
        )
        self._publish_from_thread({"type": "reader_status", **ev.to_dict()})

    def _run(self) -> None:
        backoff = self.cfg.reconnect_seconds
        while not self._stop.is_set():
            try:
                log.info("RFID loop: connecting… host=%s port=%s", self.cfg.host, self.cfg.port)
                self._connect_and_loop()
            except Exception as e:
                log.exception("RFID loop crashed, will retry in %.1fs", backoff)
                self._status("error", str(e))
                time.sleep(backoff)
        self._status("disconnected", "stopped")

    def _connect_and_loop(self) -> None:
        self._reader = RFIDReaderTCP(TCPConnectionConfig(host=self.cfg.host, port=self.cfg.port))
        self._reader.connect()
        log.info("RFID TCP connected")
        self._status("connected", f"{self.cfg.host}:{self.cfg.port}")

        payload = build_8a_fast_switch_inventory_payload(
            ants=list(self.cfg.ants or []),
            repeat=self.cfg.repeat,
        )
        log.info("Sending inventory cmd=0x%02X ants=%s repeat=%s", self.cfg.inventory_cmd, self.cfg.ants, self.cfg.repeat)
        self._reader.send_cmd(self.cfg.inventory_cmd, payload)

        while not self._stop.is_set():
            try:
                for raw in self._reader.frames():
                    fr = decode_frame(raw)
                    tag = try_parse_tag_from_inventory(fr)
                    if not tag:
                        continue

                    ev = RFIDReadEvent(
                        epc=tag.epc,
                        reader_id=self.cfg.reader_id,
                        antenna=tag.antenna,
                        rssi=float(tag.rssi_raw) if tag.rssi_raw is not None else None,
                        seen_at=tag.seen_at,
                        protocol="DDCT",
                        raw=raw.hex().upper(),
                    )
                    self._publish_from_thread({"type": "tag", **ev.to_dict()})
                    break  # salir del for para poder parar rápido

            except TimeoutError:
                continue
            except (ConnectionError, OSError) as e:
                self._status("disconnected", str(e))
                try:
                    self._reader.close()
                except Exception:
                    pass
                raise