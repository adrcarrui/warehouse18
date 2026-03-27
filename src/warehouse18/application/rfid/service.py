from __future__ import annotations

from dotenv import load_dotenv

import asyncio
import inspect
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

import httpx

from warehouse18.config import settings
from warehouse18.domain.rfid import RFIDReadEvent, ReaderStatusEvent
from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.infrastructure.rfid.low_level_reader import LowLevelRFIDReader

log = logging.getLogger("warehouse18.rfid.service")
log.warning("RFID MODULE LOADED FROM: %s", __file__)

Publisher = Callable[[dict[str, Any]], Any]

REPO_ROOT = Path(__file__).resolve().parents[5]
load_dotenv(REPO_ROOT / ".env")


@dataclass(frozen=True)
class RFIDServiceConfig:
    reader_id: str = "reader-1"
    host: str = "127.0.0.1"
    port: int = 4001
    ants: list[int] | None = None
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
        log.warning("RFID CLASS SOURCE FILE = %s", inspect.getsourcefile(self.__class__))
        log.warning("RFID SERVICE VERSION = LOW_LEVEL_READER_16_ANTS")
        log.warning("RFID SERVICE CLASS FILE = %s", __file__)

        self.cfg = cfg
        self._publish = publish
        self._loop = loop
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._reader: Optional[LowLevelRFIDReader] = None

        root = Path(__file__).resolve().parents[4]
        schema_path = root / "config" / "epc_schema.json"
        self._epc_schema: EPCSchema | None = None
        try:
            self._epc_schema = load_epc_schema(schema_path)
            log.info("EPC schema loaded | path=%s", schema_path)
        except Exception:
            log.exception("Failed to load EPC schema from %s", schema_path)
            raise

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
            log.exception("RFID publish failed")

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

    def _quick_reject_epc(self, epc: str) -> str | None:
        epc = (epc or "").strip().upper()
        if not epc:
            return "empty"
        if len(epc) != 24:
            return f"len_{len(epc)}"
        if set(epc) == {"0"}:
            return "all_zero"
        try:
            int(epc, 16)
        except ValueError:
            return "non_hex"
        return None

    def _is_valid_formatted_epc(self, epc: str) -> bool:
        if self._epc_schema is None:
            return False

        quick_reason = self._quick_reject_epc(epc)
        if quick_reason is not None:
            return False

        try:
            parsed = parse_epc96(epc, self._epc_schema)
            return (
                parsed.magic == self._epc_schema.magic
                and parsed.version == self._epc_schema.version
                and parsed.checksum_ok
                and parsed.family_name is not None
            )
        except Exception:
            return False

    def _connect_and_loop(self) -> None:
        log.warning("ENTERING _connect_and_loop WITH LOW_LEVEL_READER_16_ANTS")

        self._reader = LowLevelRFIDReader(
            host=self.cfg.host,
            port=self.cfg.port,
            addr=0x01,
            recv_timeout=float(os.getenv("WAREHOUSE18_RFID_SOCK_TIMEOUT_S", "0.20")),
            read_window_s=float(os.getenv("WAREHOUSE18_RFID_RECV_WINDOW_S", "0.35")),
            step_delay_s=float(os.getenv("WAREHOUSE18_RFID_STEP_DELAY_S", "0.03")),
            loop_sleep_s=float(os.getenv("WAREHOUSE18_RFID_INVENTORY_EVERY_S", "0.12")),
        )
        self._reader.connect()

        log.info("RFID TCP connected")
        self._status("connected", f"{self.cfg.host}:{self.cfg.port}")

        forward_to_ingest = os.getenv("WAREHOUSE18_RFID_FORWARD_TO_INGEST", "1") == "1"
        ingest_url = os.getenv("WAREHOUSE18_RFID_INGEST_URL", "http://127.0.0.1:8000/api/rfid/ingest")
        ingest_api_key = (settings.rfid_api_key or "").strip()

        http_client = httpx.Client(timeout=10.0) if forward_to_ingest else None
        ingest_headers: dict[str, str] = {}
        if ingest_api_key:
            ingest_headers["X-RFID-KEY"] = ingest_api_key

        if forward_to_ingest:
            log.info(
                "Forwarding RFID tags to ingest_url=%s api_key_configured=%s",
                ingest_url,
                bool(ingest_api_key),
            )
            log.warning(
                "RFID ingest config | forward=%s url=%s api_key_len=%s",
                forward_to_ingest,
                ingest_url,
                len(ingest_api_key),
            )

        try:
            while not self._stop.is_set():
                try:
                    got_any = False

                    for tag in self._reader.read_cycle():
                        got_any = True

                        epc = (tag.epc or "").strip().upper()
                        antenna = int(tag.antenna)

                        log.debug(
                            "RFID low-level read | epc=%s antenna=%s step=0x%02X ant_in_block=%s freq_ant=0x%02X raw=%s",
                            epc,
                            antenna,
                            tag.step_val,
                            tag.ant_in_block,
                            tag.freq_ant,
                            tag.raw.hex().upper(),
                        )

                        quick_reason = self._quick_reject_epc(epc)
                        if quick_reason is not None:
                            log.debug(
                                "TAG descartado por filtro rápido EPC=%s antenna=%s reason=%s",
                                epc,
                                antenna,
                                quick_reason,
                            )
                            continue

                        if not self._is_valid_formatted_epc(epc):
                            log.debug(
                                "TAG descartado por formato EPC no válido EPC=%s antenna=%s",
                                epc,
                                antenna,
                            )
                            continue

                        try:
                            parsed = parse_epc96(epc, self._epc_schema)
                            family_name = parsed.family_name or "UNKNOWN"
                            serial_num = int(parsed.serial)
                        except Exception:
                            family_name = "UNKNOWN"
                            serial_num = -1

                        log.debug(
                            "TAG válido detectado EPC=%s family=%s serial_num=%s antenna=%s",
                            epc,
                            family_name,
                            serial_num,
                            antenna,
                        )

                        ev = RFIDReadEvent(
                            epc=epc,
                            reader_id=self.cfg.reader_id,
                            antenna=antenna,
                            rssi=float(tag.rssi_raw) if tag.rssi_raw is not None else None,
                            seen_at=tag.seen_at,
                            protocol="DDCT",
                            raw=tag.raw.hex().upper(),
                        )

                        # 1) SSE / monitor
                        self._publish_from_thread({"type": "tag", **ev.to_dict()})

                        # 2) Forward a ingest
                        if http_client is not None:
                            try:
                                resp = http_client.post(
                                    ingest_url,
                                    headers=ingest_headers,
                                    json={
                                        "epc": ev.epc,
                                        "antenna": ev.antenna,
                                        "rssi": ev.rssi,
                                        "reader_id": ev.reader_id,
                                    },
                                )
                                log.debug(
                                    "RFID ingest response | status=%s body=%s",
                                    resp.status_code,
                                    resp.text[:500],
                                )
                            except Exception:
                                log.exception(
                                    "RFID forward to ingest failed | epc=%s antenna=%s",
                                    ev.epc,
                                    ev.antenna,
                                )

                    if not got_any:
                        continue

                except TimeoutError:
                    continue
                except (ConnectionError, OSError) as e:
                    self._status("disconnected", str(e))
                    try:
                        if self._reader:
                            self._reader.close()
                    except Exception:
                        pass
                    raise
        finally:
            if http_client is not None:
                http_client.close()
            if self._reader is not None:
                self._reader.close()