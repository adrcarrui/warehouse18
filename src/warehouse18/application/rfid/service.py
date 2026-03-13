from __future__ import annotations

import asyncio
import logging
import os
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from dotenv import load_dotenv
import httpx

from warehouse18.config import settings
from warehouse18.domain.rfid import RFIDReadEvent, ReaderStatusEvent
from warehouse18.application.rfid.epc96 import EPCSchema, load_epc_schema, parse_epc96
from warehouse18.infrastructure.rfid.parser import decode_frame, try_parse_tag_from_inventory
from warehouse18.infrastructure.rfid.tcp_client import RFIDReaderTCP, TCPConnectionConfig

log = logging.getLogger("warehouse18.rfid.service")

Publisher = Callable[[dict[str, Any]], Any]

root = Path(__file__).resolve().parents[4]
load_dotenv(root / ".env")


@dataclass(frozen=True)
class RFIDServiceConfig:
    reader_id: str = "reader-1"
    host: str = "192.168.0.101"
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

        schema_path = root / "config" / "epc_schema.json"
        self._epc_schema: EPCSchema | None = None

        try:
            self._epc_schema = load_epc_schema(schema_path)
            log.info("EPC schema loaded | path=%s", schema_path)
        except Exception:
            log.exception("Failed to load EPC schema from %s", schema_path)
            raise

        self._last_user_id: int | None = None
        self._last_user_ts: float = 0.0
        self._user_ttl_s: float = float(os.getenv("WAREHOUSE18_RFID_USER_TTL_S", "20"))

        self._tag_dedupe_s: float = float(os.getenv("WAREHOUSE18_RFID_TAG_DEDUPE_S", "0.6"))
        self._last_seen_by_epc_ant: dict[tuple[str, int], float] = {}

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.is_running:
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="RFIDReaderService",
            daemon=True,
        )
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
            pass

    def _status(self, status: str, message: str | None = None) -> None:
        ev = ReaderStatusEvent(
            reader_id=self.cfg.reader_id,
            status=status,
            at=datetime.now(timezone.utc),
            message=message,
        )
        self._publish_from_thread({"type": "reader_status", **ev.to_dict()})

    def _parse_epc_fields(self, epc: str) -> dict[str, object] | None:
        if self._epc_schema is None:
            return None

        try:
            parsed = parse_epc96(epc, self._epc_schema)
            serial_num = int(parsed.serial)

            return {
                "magic": parsed.magic,
                "version": parsed.version,
                "family_code": parsed.family_code,
                "family_name": parsed.family_name,
                "serial_num": serial_num,
                "checksum_ok": parsed.checksum_ok,
            }
        except Exception as e:
            log.debug("EPC parse failed | epc=%s motivo=%s", epc, e)
            return None

    def _is_valid_formatted_epc(self, epc: str) -> bool:
        parsed_info = self._parse_epc_fields(epc)
        if parsed_info is None or self._epc_schema is None:
            return False

        ok = (
            parsed_info["magic"] == self._epc_schema.magic
            and parsed_info["version"] == self._epc_schema.version
            and parsed_info["checksum_ok"] is True
            and parsed_info["family_name"] is not None
        )

        if not ok:
            log.debug(
                "TAG descartado | epc=%s magic=%s version=%s family=%s checksum_ok=%s",
                epc,
                parsed_info["magic"],
                parsed_info["version"],
                parsed_info["family_name"],
                parsed_info["checksum_ok"],
            )

        return ok

    def _serial_to_6_digits(self, serial_num: int) -> str | None:
        s = str(serial_num)
        if len(s) > 6:
            return None
        return s.zfill(6)

    def _build_item_part_code(self, family_name: str, serial_num: int) -> str | None:
        serial_6 = self._serial_to_6_digits(serial_num)
        if serial_6 is None:
            return None
        return f"{family_name}-{serial_6}"

    def _extract_user_id(self, family_name: str, serial_num: int) -> int | None:
        if family_name != "USER":
            return None
        return serial_num

    def _remember_user(self, user_id: int) -> None:
        self._last_user_id = user_id
        self._last_user_ts = time.time()
        log.info("RFID user bound | user_id=%s ttl_s=%s", user_id, self._user_ttl_s)

    def _get_active_user_id(self) -> int | None:
        if self._last_user_id is None:
            return None

        age = time.time() - self._last_user_ts
        if age > self._user_ttl_s:
            log.info(
                "RFID active user expired | user_id=%s age_s=%.2f ttl_s=%s",
                self._last_user_id,
                age,
                self._user_ttl_s,
            )
            self._last_user_id = None
            return None

        return self._last_user_id

    def _should_skip_tag(self, epc: str, antenna: int) -> bool:
        now_ts = time.time()
        key = (epc, antenna)
        last_ts = self._last_seen_by_epc_ant.get(key)

        if last_ts is not None and (now_ts - last_ts) < self._tag_dedupe_s:
            log.debug(
                "RFID dedupe skip | epc=%s antenna=%s delta_s=%.3f dedupe_s=%s",
                epc,
                antenna,
                now_ts - last_ts,
                self._tag_dedupe_s,
            )
            return True

        self._last_seen_by_epc_ant[key] = now_ts
        return False

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
        last_inventory_ts = 0.0

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

        forward_to_ingest = os.getenv("WAREHOUSE18_RFID_FORWARD_TO_INGEST", "1") == "1"
        ingest_url = os.getenv(
            "WAREHOUSE18_RFID_INGEST_URL",
            "http://127.0.0.1:8000/api/rfid/ingest",
        )
        http_client = httpx.Client(timeout=1.0) if forward_to_ingest else None

        if forward_to_ingest:
            log.info("Forwarding RFID tags to ingest_url=%s", ingest_url)

        log.info("Direct mySim movement creation disabled in service.py | mode=forward_only")

        try:
            while not self._stop.is_set():
                try:
                    now_ts = time.time()
                    if (now_ts - last_inventory_ts) >= inventory_every_s:
                        self._reader.send_raw(inv_frame)
                        last_inventory_ts = now_ts

                    got_any = False
                    if int(time.time()) % 2 == 0:
                        log.debug("RFID loop alive, waiting frames…")

                    for raw in self._reader.recv_frames(window_s=3.0):
                        got_any = True
                        log.debug("RFID frame len=%s raw=%s", len(raw), raw.hex().upper())

                        fr = decode_frame(raw)
                        log.debug(
                            "RFID decoded frame cmd=0x%02X data_len=%s data=%s",
                            fr.cmd,
                            len(fr.data),
                            fr.data.hex().upper(),
                        )

                        tag = try_parse_tag_from_inventory(fr)
                        if not tag:
                            log.debug(
                                "RFID frame ignored: cmd=0x%02X data=%s",
                                fr.cmd,
                                fr.data.hex().upper(),
                            )
                            continue

                        log.debug(
                            "TAG leído EPC=%s len=%s antenna=%s",
                            tag.epc,
                            len(tag.epc),
                            tag.antenna,
                        )

                        if not self._is_valid_formatted_epc(tag.epc):
                            log.debug(
                                "TAG descartado por formato EPC no válido EPC=%s antenna=%s",
                                tag.epc,
                                tag.antenna,
                            )
                            continue

                        epc_info = self._parse_epc_fields(tag.epc)
                        if epc_info is None:
                            log.debug(
                                "TAG descartado porque no se pudo parsear EPC=%s antenna=%s",
                                tag.epc,
                                tag.antenna,
                            )
                            continue

                        family_name = str(epc_info.get("family_name") or "")
                        serial_num = int(epc_info.get("serial_num") or 0)

                        # Dedupe solo para USER
                        if family_name == "USER":
                            if self._should_skip_tag(tag.epc, tag.antenna):
                                continue

                        part_code_demo = self._build_item_part_code(family_name, serial_num)

                        log.debug(
                            "TAG válido detectado EPC=%s family=%s serial_num=%s part_code_demo=%s antenna=%s",
                            tag.epc,
                            family_name,
                            serial_num,
                            part_code_demo,
                            tag.antenna,
                        )

                        ev = RFIDReadEvent(
                            epc=tag.epc,
                            reader_id=self.cfg.reader_id,
                            antenna=tag.antenna,
                            rssi=float(tag.rssi_raw) if tag.rssi_raw is not None else None,
                            seen_at=tag.seen_at,
                            protocol="DDCT",
                            raw=raw.hex().upper(),
                        )

                        # USER
                        user_id = self._extract_user_id(family_name, serial_num)
                        if user_id is not None:
                            self._remember_user(user_id)

                            self._publish_from_thread(
                                {
                                    "type": "user_tag",
                                    **ev.to_dict(),
                                    "family": family_name,
                                    "serial_num": serial_num,
                                    "user_id": user_id,
                                }
                            )

                            if http_client is not None:
                                try:
                                    resp = http_client.post(
                                        ingest_url,
                                        json={
                                            "epc": ev.epc,
                                            "antenna": ev.antenna,
                                            "rssi": ev.rssi,
                                        },
                                    )
                                    log.info(
                                        "RFID ingest response | kind=USER status=%s body=%s",
                                        resp.status_code,
                                        resp.text,
                                    )
                                except Exception as e:
                                    log.warning("RFID forward USER to ingest failed: %s", e)

                            continue

                        # ITEM
                        active_user_id = self._get_active_user_id()
                        log.info(
                            "RFID item ready for routing | epc=%s family=%s serial_num=%s part_code_demo=%s active_user_id=%s antenna=%s",
                            ev.epc,
                            family_name,
                            serial_num,
                            part_code_demo,
                            active_user_id,
                            ev.antenna,
                        )

                        if active_user_id is None:
                            log.warning(
                                "route skip | no active user for item epc=%s family=%s serial=%s antenna=%s",
                                ev.epc,
                                family_name,
                                serial_num,
                                ev.antenna,
                            )

                        self._publish_from_thread(
                            {
                                "type": "tag",
                                **ev.to_dict(),
                                "family": family_name,
                                "serial_num": serial_num,
                                "part_code_demo": part_code_demo,
                                "active_user_id": active_user_id,
                            }
                        )

                        if http_client is not None:
                            try:
                                resp = http_client.post(
                                    ingest_url,
                                    json={
                                        "epc": ev.epc,
                                        "antenna": ev.antenna,
                                        "rssi": ev.rssi,
                                    },
                                )
                                log.info(
                                    "RFID ingest response | kind=ITEM status=%s body=%s",
                                    resp.status_code,
                                    resp.text,
                                )
                            except Exception as e:
                                log.warning("RFID forward ITEM to ingest failed: %s", e)

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