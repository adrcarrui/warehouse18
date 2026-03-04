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
import os
import httpx

from warehouse18.config import settings
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
            object.__setattr__(self, "ants", list(range(1, 3)))


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
        inventory_every_s = float(os.getenv("WAREHOUSE18_RFID_INVENTORY_EVERY_S", "0.5"))
        last_inventory_ts = 0.0  # forzar primer envío inmediato

        # --- Inventory RAW frame (exacto como rfid_simple_test.py) ---
        frame_hex = settings.rfid_8a_frame_hex.strip().replace(" ", "")
        if not frame_hex:
            raise RuntimeError("Missing WAREHOUSE18_RFID_8A_FRAME_HEX in .env")
        inv_frame = bytes.fromhex(frame_hex)

        self._reader = RFIDReaderTCP(TCPConnectionConfig(host=self.cfg.host, port=self.cfg.port))
        self._reader.connect()
        log.info("RFID TCP connected")
        self._status("connected", f"{self.cfg.host}:{self.cfg.port}")

        log.info("Sending inventory RAW frame=%s", frame_hex.upper())
        self._reader.send_raw(inv_frame)

        # --- Forward a /rfid/ingest (opcional, para demo) ---
        forward_to_ingest = os.getenv("WAREHOUSE18_RFID_FORWARD_TO_INGEST", "0") == "1"
        ingest_url = os.getenv("WAREHOUSE18_RFID_INGEST_URL", "http://127.0.0.1:8000/api/rfid/ingest")
        http_client = httpx.Client(timeout=1.0) if forward_to_ingest else None
        if forward_to_ingest:
            log.info("Forwarding RFID tags to ingest_url=%s", ingest_url)

        try:
            while not self._stop.is_set():
                try:
                    # Re-disparo del inventario (modo demo)
                    now_ts = time.time()
                    if (now_ts - last_inventory_ts) >= inventory_every_s:
                        self._reader.send_raw(inv_frame)
                        last_inventory_ts = now_ts

                    got_any = False
                    if int(time.time()) % 2 == 0:
                        log.debug("RFID loop alive, waiting frames…")
                    for chunk in self._reader.recv_chunks(window_s=3.0):
                        got_any = True
                        log.debug(
                            "RFID raw frame len=%s hex_head=%s",
                            len(chunk),
                            chunk[:12].hex().upper(),
                        )

                        fr = decode_frame(chunk)
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
                            raw=chunk.hex().upper(),
                        )

                        # 1) SSE / monitor
                        self._publish_from_thread({"type": "tag", **ev.to_dict()})

                        # 2) Forward al endpoint ingest (para que se ejecute la lógica real de user/item)
                        if http_client is not None:
                            try:
                                http_client.post(
                                    ingest_url,
                                    json={"epc": ev.epc, "antenna": ev.antenna, "rssi": ev.rssi},
                                )
                            except Exception:
                                pass

                    if not got_any:
                        continue

                except TimeoutError:
                    continue
                except (ConnectionError, OSError) as e:
                    self._status("disconnected", str(e))
                    try:
                        self._reader.close()
                    except Exception:
                        pass
                    raise
        finally:
            if http_client is not None:
                http_client.close()