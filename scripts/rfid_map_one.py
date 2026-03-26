import argparse
import json
import socket
import time
from collections import Counter
from pathlib import Path

HOST = "192.168.0.101"
PORT = 4001
ADDR = 0x01

RECV_TIMEOUT = 0.20
READ_WINDOW_S = 0.60
LOOP_SLEEP_S = 0.20

DELAY_6C_00 = 0.05
DELAY_6C_10 = 0.05
DELAY_6C_01 = 0.05


def checksum(frame_wo_check: bytes) -> int:
    return (~sum(frame_wo_check) + 1) & 0xFF


def build_cmd(cmd: int, data: bytes = b"") -> bytes:
    length = len(data) + 3
    frame = bytearray([0xA0, length, ADDR, cmd])
    frame.extend(data)
    frame.append(checksum(frame))
    return bytes(frame)


def cmd_6c(val: int) -> bytes:
    return build_cmd(0x6C, bytes([val]))


def cmd_inventory() -> bytes:
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
    return build_cmd(0x8A, data)


def extract_frames(buf: bytearray):
    frames = []
    i = 0
    while True:
        while i < len(buf) and buf[i] != 0xA0:
            i += 1

        if i >= len(buf):
            del buf[:]
            return frames

        if len(buf) - i < 2:
            if i > 0:
                del buf[:i]
            return frames

        length = buf[i + 1]
        total = 2 + length

        if len(buf) - i < total:
            if i > 0:
                del buf[:i]
            return frames

        frames.append(bytes(buf[i:i + total]))
        i += total


def verify(frame: bytes) -> bool:
    return len(frame) >= 5 and checksum(frame[:-1]) == frame[-1]


def parse_8a(frame: bytes):
    if len(frame) < 5 or frame[0] != 0xA0 or frame[3] != 0x8A:
        return None

    if frame[1] == 0x0A:
        return {
            "type": "summary",
            "total_read": int.from_bytes(frame[4:7], "big"),
            "duration_ms": int.from_bytes(frame[7:11], "big"),
        }

    payload = frame[4:-1]
    if len(payload) < 6:
        return None

    freq_ant = payload[0]
    pc = payload[1:3]
    epc = payload[3:-1]
    rssi_raw = payload[-1]

    if len(epc) < 4:
        return None

    low2 = freq_ant & 0x03
    upper_half = 1 if (rssi_raw & 0x80) else 0
    logical_slot = low2 + 1 + (4 if upper_half else 0)
    logical_key = f"FA{freq_ant:02X}_UH{upper_half}"

    return {
        "type": "tag",
        "freq_ant": freq_ant,
        "pc": pc.hex().upper(),
        "epc": epc.hex().upper(),
        "rssi_raw": rssi_raw,
        "rssi": rssi_raw & 0x7F,
        "logical_slot": logical_slot,
        "logical_key": logical_key,
    }


def load_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_mapping(path: Path, mapping: dict) -> None:
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical-ant", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--mapping", default="scripts/antenna_mapping.json")
    args = parser.parse_args()

    mapping_path = Path(args.mapping)
    mapping = load_mapping(mapping_path)

    c00 = cmd_6c(0x00)
    c10 = cmd_6c(0x10)
    c01 = cmd_6c(0x01)
    inv = cmd_inventory()

    counts = Counter()
    sample_by_key = {}

    print(f"Conectado a {args.host}:{args.port}")
    print(f"Mapeando antena física {args.physical_ant}")
    print(f"Ventana de captura: {args.seconds:.1f}s")
    print("Deja un solo tag quieto SOLO en esa antena.\n")

    rx = bytearray()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(RECV_TIMEOUT)
        s.connect((args.host, args.port))

        t_end = time.time() + args.seconds
        cycle = 0

        while time.time() < t_end:
            cycle += 1

            s.sendall(c00)
            time.sleep(DELAY_6C_00)
            s.sendall(c10)
            time.sleep(DELAY_6C_10)
            s.sendall(c01)
            time.sleep(DELAY_6C_01)
            s.sendall(inv)

            t0 = time.time()
            while time.time() - t0 < READ_WINDOW_S:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    rx.extend(chunk)

                    for frame in extract_frames(rx):
                        if not verify(frame):
                            continue

                        parsed = parse_8a(frame)
                        if not parsed or parsed["type"] != "tag":
                            continue

                        key = parsed["logical_key"]
                        counts[key] += 1
                        sample_by_key[key] = parsed

                        print(
                            f"cycle={cycle} "
                            f"key={key} "
                            f"slot={parsed['logical_slot']} "
                            f"freq=0x{parsed['freq_ant']:02X} "
                            f"rssi={parsed['rssi']} "
                            f"hits={counts[key]}"
                        )

                except socket.timeout:
                    break

            time.sleep(LOOP_SLEEP_S)

    print("\nRanking final:")
    for key, hits in counts.most_common():
        sample = sample_by_key[key]
        print(
            f"{key}: hits={hits} "
            f"slot={sample['logical_slot']} "
            f"freq=0x{sample['freq_ant']:02X}"
        )

    if not counts:
        print("\nNo hubo lecturas. No se guarda nada.")
        return

    best_key, best_hits = counts.most_common(1)[0]
    mapping[str(args.physical_ant)] = {
        "logical_key": best_key,
        "hits": best_hits,
    }
    save_mapping(mapping_path, mapping)

    print(f"\nGuardado: antena física {args.physical_ant} -> {best_key}")
    print(f"Archivo: {mapping_path}")


if __name__ == "__main__":
    main()