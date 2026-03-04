from __future__ import annotations

import json
import logging
import os
import socket
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from warehouse18.application.rfid.epc96 import load_epc_schema, is_whitelisted

logger = logging.getLogger("warehouse18.rfid.service")

HEAD = 0xA0


@dataclass(frozen=True)
class DedupeKey:
    reader_id: str
    epc: str
    antenna: int


@dataclass
class RFIDServiceConfig:
    reader_host: str = os.getenv("WAREHOUSE18_RFID_HOST", "192.168.0.178")
    reader_port: int = int(os.getenv("WAREHOUSE18_RFID_PORT", "4001"))
    # Identificador estable del lector (para dedupe multi-reader). Por defecto: host.
    reader_id: str = os.getenv(
        "WAREHOUSE18_RFID_READER_ID",
        os.getenv("WAREHOUSE18_RFID_HOST", "reader-1"),
    )

    inventory_body_hex: str = os.getenv(
        "WAREHOUSE18_RFID_8A_BODY_HEX",
        "15018A000101010200030004000500060007000001",
        # "15018A000101010201030104000500060007000501",
    )

    ingest_url: str = os.getenv(
        "WAREHOUSE18_RFID_INGEST_URL",
        "http://127.0.0.1:8000/api/rfid/ingest",
    )

    poll_interval_s: float = float(os.getenv("WAREHOUSE18_RFID_POLL_INTERVAL_S", "0.08"))

    # ventana de lectura tras enviar 8A (puerta doble)
    recv_window_s: float = float(os.getenv("WAREHOUSE18_RFID_RECV_WINDOW_S", "0.18"))
    sock_timeout_s: float = float(os.getenv("WAREHOUSE18_RFID_SOCK_TIMEOUT_S", "0.05"))

    # anti-spam (antes del POST)
    dedupe_seconds: float = float(os.getenv("WAREHOUSE18_RFID_DEDUPE_SECONDS", "0.6"))
    # TTL para limpiar el diccionario de dedupe (evita crecimiento infinito)
    dedupe_ttl_seconds: float = float(os.getenv("WAREHOUSE18_RFID_DEDUPE_TTL_SECONDS", "6.0"))
    # cada cuánto intentamos limpiar (segundos)
    dedupe_gc_every_s: float = float(os.getenv("WAREHOUSE18_RFID_DEDUPE_GC_EVERY_S", "2.0"))

    # batching
    batch_max: int = int(os.getenv("WAREHOUSE18_RFID_BATCH_MAX", "25"))
    batch_flush_s: float = float(os.getenv("WAREHOUSE18_RFID_BATCH_FLUSH_S", "0.25"))

    log_level: str = os.getenv("WAREHOUSE18_RFID_LOG_LEVEL", "INFO")


def checksum(hex_bytes: str) -> str:
    data = bytes.fromhex(hex_bytes)
    total = sum(data)
    return f"{(256 - (total % 256)) % 256:02X}"


def build_frame(body_hex: str) -> bytes:
    full = "A0" + body_hex.upper()
    chk = checksum(full)
    return bytes.fromhex(full + chk)


def parse_8A(frame: bytes) -> Optional[tuple[int, str, int | None]]:
    """
    Parse de respuesta 0x8A según 'UHF RFID Reader Serial Interface V3.8':
    Tag packet:
      Head(0xA0) Len Addr Cmd FreqAnt PC(2) EPC(N) RSSI(1) Check(1)

    - FreqAnt: high 6 bits = frequency, low 2 bits = antenna ID (0..3)
    - RSSI: high bit selects antenna group (0 => ant 1..4, 1 => ant 5..8) for 8-ant models.
            (High bit not counted in RSSI)
    """
    if len(frame) < 6:
        return None
    if frame[0] != 0xA0:
        return None

    length = frame[1]
    # sanity: total bytes should be 2 + length
    if len(frame) != 2 + length:
        # si tu split_frames ya recorta perfecto, esto debería cuadrar
        return None

    addr = frame[2]
    cmd = frame[3]
    if cmd != 0x8A:
        return None

    # Caso "antena missing" (detector on): Len=0x05, payload: Addr Cmd AntID ErrorCode Check
    if length == 0x05:
        ant_id = frame[4]  # 00..03
        err = frame[5]
        logger.warning("RFID antenna missing | ant=%s err=0x%02X", ant_id, err)
        return None

    # Caso "summary": Len=0x0A (TotalRead + Duration). No hay EPC.
    if length == 0x0A:
        # frame[4:7] totalRead (3 bytes), frame[7:11] duration (4 bytes)
        total_read = int.from_bytes(frame[4:7], "big")
        duration_ms = int.from_bytes(frame[7:11], "big")
        logger.debug("RFID summary | total_read=%s duration=%sms", total_read, duration_ms)
        return None

    # Caso tag packet normal
    # Layout mínimo: Addr(1) Cmd(1) FreqAnt(1) PC(2) EPC(?) RSSI(1) Check(1)
    if length < (1 + 1 + 1 + 2 + 1 + 1):
        return None

    freq_ant = frame[4]
    pc = frame[5:7]  # no lo usamos, pero está ahí
    rssi_byte = frame[-2]  # penúltimo byte
    epc_bytes = frame[7:-2]  # desde después de PC hasta antes de RSSI

    if not epc_bytes:
        return None

    # Antena real:
    ant_low = freq_ant & 0x03  # 0..3
    ant_group = 4 if (rssi_byte & 0x80) else 0  # grupo 5..8 si high bit set
    antenna = ant_low + ant_group  # 0..7 para modelos de 8 antenas

    rssi = rssi_byte & 0x7F

    epc = epc_bytes.hex().upper()
    return antenna, epc, rssi


def split_frames(buf: bytearray) -> list[bytes]:
    """
    Frame: A0 LEN ...   (LEN incluye addr+cmd+data+chk)
    total = 2 + LEN
    """
    out: list[bytes] = []
    while True:
        try:
            i = buf.index(HEAD)
        except ValueError:
            buf.clear()
            break

        if i > 0:
            del buf[:i]

        if len(buf) < 2:
            break

        length = buf[1]
        total = 2 + length
        if len(buf) < total:
            break

        out.append(bytes(buf[:total]))
        del buf[:total]

    return out


class RFIDIngestService:
    def __init__(self, cfg: RFIDServiceConfig | None = None):
        self.cfg = cfg or RFIDServiceConfig()
        self.frame = build_frame(self.cfg.inventory_body_hex)

        # schema EPC (familias fuera del código)
        root = Path(__file__).resolve().parents[4]  # ajusta si tu árbol difiere
        schema_path = root / "config" / "epc_schema.json"
        self.schema = load_epc_schema(schema_path)
        logger.info("EPC schema loaded | path=%s", schema_path)

        # dedupe: (reader_id, epc, antenna) -> last_emit_ts
        self.reader_id = str(self.cfg.reader_id)
        self._last_emit: dict[DedupeKey, float] = {}
        self._last_dedupe_gc_ts: float = 0.0

        # batching
        self._batch: list[dict[str, object]] = []
        self._last_flush = time.time()

        # URL batch derivada
        self.batch_url = self.cfg.ingest_url.rstrip("/")
        if self.batch_url.endswith("/ingest"):
            self.batch_url = self.batch_url + "/batch"
        else:
            # fallback si alguien configura raro
            self.batch_url = self.batch_url + "/batch"

    def _dedupe_gc(self, now: float) -> None:
        if self.cfg.dedupe_seconds <= 0:
            return
        if (now - self._last_dedupe_gc_ts) < self.cfg.dedupe_gc_every_s:
            return
        self._last_dedupe_gc_ts = now

        cutoff = now - max(self.cfg.dedupe_ttl_seconds, self.cfg.dedupe_seconds * 2)
        if not self._last_emit:
            return

        dead = [k for k, ts in self._last_emit.items() if ts < cutoff]
        for k in dead:
            self._last_emit.pop(k, None)

    def _dedupe_ok(self, epc: str, antenna: int, now: float) -> bool:
        if self.cfg.dedupe_seconds <= 0:
            return True

        self._dedupe_gc(now)

        k = DedupeKey(self.reader_id, epc, int(antenna))
        last = self._last_emit.get(k)
        if last is not None and (now - last) < self.cfg.dedupe_seconds:
            return False
        self._last_emit[k] = now
        return True

    def _flush_batch_if_needed(self, force: bool = False) -> None:
        now = time.time()
        if not self._batch:
            return

        if not force:
            if len(self._batch) < self.cfg.batch_max and (now - self._last_flush) < self.cfg.batch_flush_s:
                return

        reads = self._batch
        self._batch = []
        self._last_flush = now

        payload = {"reads": reads}
        data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.batch_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                body = resp.read(200).decode("utf-8", errors="ignore")
                logger.debug("POST batch OK | %s | %s", resp.status, body)
        except Exception as e:
            logger.warning("POST batch FAIL | url=%s | %s", self.batch_url, e)

    def run(self) -> None:
        logging.basicConfig(
            level=getattr(logging, self.cfg.log_level.upper(), logging.INFO),
            format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        )

        logger.info(
            "RFID service starting | reader=%s:%s reader_id=%s ingest=%s batch=%s",
            self.cfg.reader_host,
            self.cfg.reader_port,
            self.reader_id,
            self.cfg.ingest_url,
            self.batch_url,
        )

        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2.0)
                    s.connect((self.cfg.reader_host, self.cfg.reader_port))
                    s.settimeout(self.cfg.sock_timeout_s)

                    s.sendall(self.frame)

                    buf = bytearray()
                    end = time.time() + self.cfg.recv_window_s

                    while time.time() < end:
                        try:
                            chunk = s.recv(4096)
                            if not chunk:
                                break
                            buf.extend(chunk)
                        except socket.timeout:
                            break

                frames = split_frames(buf)

                now = time.time()
                for fr in frames:
                    parsed = parse_8A(fr)
                    if parsed:
                        antenna, epc, rssi = parsed
                        epc = epc.upper()

                        logger.debug("RAW TAG | antenna=%s epc=%s rssi=%s", antenna, epc, rssi)

                        if not is_whitelisted(epc, self.schema):
                            logger.debug("IGNORED whitelist | antenna=%s epc=%s", antenna, epc)
                            continue

                        if not self._dedupe_ok(epc, antenna, now):
                            logger.debug("IGNORED dedupe | antenna=%s epc=%s", antenna, epc)
                            continue

                        logger.info("ACCEPTED | antenna=%s epc=%s rssi=%s", antenna, epc, rssi)
                        self._batch.append({"epc": epc, "antenna": antenna, "rssi": rssi})

                # flush batch por tiempo/tamaño
                self._flush_batch_if_needed(force=False)

                time.sleep(self.cfg.poll_interval_s)

            except Exception as e:
                logger.warning("RFID loop error: %s", e)
                # intenta mandar lo que quede, por si acaso
                self._flush_batch_if_needed(force=True)
                time.sleep(1)


if __name__ == "__main__":
    RFIDIngestService().run()