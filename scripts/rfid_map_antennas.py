import argparse
import json
import socket
import time
from pathlib import Path

HOST = "192.168.0.101"
PORT = 4001
ADDR = 0x01

RECV_TIMEOUT = 0.10
READ_WINDOW_S = 0.35
CYCLE_SLEEP = 0.08
DEDUPE_S = 0.4

SEQUENCE_6C = [0x00, 0x10, 0x01]


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
        "low2": low2,
        "upper_half": upper_half,
        "logical_slot": logical_slot,
        "logical_key": logical_key,
    }


def load_mapping(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_mapping(path: Path, mapping: dict) -> None:
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")


def open_reader(host: str, port: int) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(RECV_TIMEOUT)
    sock.connect((host, port))
    return sock


def poll_once(sock: socket.socket):
    rx = bytearray()
    results = []

    for v in SEQUENCE_6C:
        sock.sendall(cmd_6c(v))
        time.sleep(0.01)

    sock.sendall(cmd_inventory())

    t0 = time.time()
    while time.time() - t0 < READ_WINDOW_S:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            rx.extend(chunk)

            for frame in extract_frames(rx):
                if not verify(frame):
                    continue
                parsed = parse_8a(frame)
                if parsed:
                    results.append(parsed)

        except socket.timeout:
            break

    return results


def learn_mode(host: str, port: int, mapping_path: Path, min_hits: int, timeout_s: float):
    mapping = load_mapping(mapping_path)

    print(f"Conectado a {host}:{port}")
    print("Modo calibración mejorado.")
    print(f"Umbral de aprendizaje: {min_hits} hits de la misma logical_key")
    print(f"Timeout por antena: {timeout_s:.1f}s\n")

    with open_reader(host, port) as sock:
        for physical_ant in range(1, 17):
            input(f"\n>>> Coloca el tag SOLO en la antena física {physical_ant} y pulsa Enter... ")

            counts = {}
            start = time.time()
            last_print = 0.0

            while time.time() - start < timeout_s:
                results = poll_once(sock)

                for item in results:
                    if item["type"] == "summary":
                        # imprime de vez en cuando para que veas que no está muerto
                        now = time.time()
                        if now - last_print > 0.5:
                            print(
                                f"summary: total_read={item['total_read']} "
                                f"duration_ms={item['duration_ms']}"
                            )
                            last_print = now
                        continue

                    if item["type"] == "tag":
                        key = item["logical_key"]
                        counts[key] = counts.get(key, 0) + 1

                        print(
                            f"tag: physical_target={physical_ant} "
                            f"logical_key={key} "
                            f"logical_slot={item['logical_slot']} "
                            f"epc={item['epc']} "
                            f"rssi={item['rssi']} "
                            f"hits={counts[key]}"
                        )

                        if counts[key] >= min_hits:
                            mapping[key] = physical_ant
                            save_mapping(mapping_path, mapping)
                            print(f"\nAPRENDIDO: antena física {physical_ant} -> {key}\n")
                            break

                else:
                    time.sleep(CYCLE_SLEEP)
                    continue

                break
            else:
                print(f"\nNo se pudo aprender la antena física {physical_ant} en {timeout_s:.1f}s.\n")
                print("Sugerencias:")
                print("- deja un solo tag quieto, muy cerca de esa antena")
                print("- aleja el tag del resto")
                print("- prueba otra vez esa misma antena")
                print("- si quieres, sube timeout o baja min_hits\n")

    print("Mapeo actual:")
    print(json.dumps(mapping, indent=2, ensure_ascii=False))


def read_mode(host: str, port: int, mapping_path: Path):
    mapping = load_mapping(mapping_path)
    seen = {}

    print(f"Conectado a {host}:{port}")
    print(f"Usando mapeo: {mapping_path}")

    if not mapping:
        print("No hay mapeo todavía. Ejecuta primero --mode learn.")
        return

    with open_reader(host, port) as sock:
        while True:
            results = poll_once(sock)
            now = time.time()

            for item in results:
                if item["type"] != "tag":
                    continue

                logical_key = item["logical_key"]
                physical_ant = mapping.get(logical_key, f"?({logical_key})")

                dedupe_key = (item["epc"], logical_key)
                if dedupe_key in seen and now - seen[dedupe_key] < DEDUPE_S:
                    continue
                seen[dedupe_key] = now

                print(
                    f"EPC={item['epc']} "
                    f"ANT_FISICA={physical_ant} "
                    f"LOGICAL_KEY={logical_key} "
                    f"LOGICAL_SLOT={item['logical_slot']} "
                    f"RSSI={item['rssi']} "
                    f"PC={item['pc']} "
                    f"FREQANT=0x{item['freq_ant']:02X}"
                )

            time.sleep(CYCLE_SLEEP)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--mode", choices=["learn", "read"], required=True)
    parser.add_argument("--mapping", default="scripts/antenna_mapping.json")
    parser.add_argument("--min-hits", type=int, default=3)
    parser.add_argument("--timeout-s", type=float, default=12.0)
    args = parser.parse_args()

    mapping_path = Path(args.mapping)

    if args.mode == "learn":
        learn_mode(args.host, args.port, mapping_path, args.min_hits, args.timeout_s)
    else:
        read_mode(args.host, args.port, mapping_path)


if __name__ == "__main__":
    main()