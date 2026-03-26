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

DEFAULT_MAPPING = "scripts/antenna_mapping.json"


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

    # Resumen del comando
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=2, ensure_ascii=False), encoding="utf-8")


def perform_sequence_and_collect(sock: socket.socket):
    rx = bytearray()
    results = []

    sock.sendall(cmd_6c(0x00))
    time.sleep(DELAY_6C_00)

    sock.sendall(cmd_6c(0x10))
    time.sleep(DELAY_6C_10)

    sock.sendall(cmd_6c(0x01))
    time.sleep(DELAY_6C_01)

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


def calibrate_one(sock: socket.socket, physical_ant: int, seconds: float, mapping: dict):
    counts = Counter()
    samples = {}
    total_tags = 0
    total_summaries = 0

    print(f"\n--- Calibrando antena física {physical_ant} durante {seconds:.1f}s ---")
    print("Deja un solo tag quieto SOLO en esa antena.\n")

    end_time = time.time() + seconds
    cycle = 0

    while time.time() < end_time:
        cycle += 1
        results = perform_sequence_and_collect(sock)

        for item in results:
            if item["type"] == "summary":
                total_summaries += 1
                continue

            if item["type"] == "tag":
                total_tags += 1
                key = item["logical_key"]
                counts[key] += 1
                samples[key] = item

                print(
                    f"cycle={cycle} "
                    f"key={key} "
                    f"slot={item['logical_slot']} "
                    f"freq=0x{item['freq_ant']:02X} "
                    f"rssi={item['rssi']} "
                    f"hits={counts[key]} "
                    f"epc={item['epc']}"
                )

        time.sleep(LOOP_SLEEP_S)

    print("\nRanking final:")
    for key, hits in counts.most_common():
        s = samples[key]
        print(
            f"  {key}: hits={hits}, slot={s['logical_slot']}, "
            f"freq=0x{s['freq_ant']:02X}, rssi={s['rssi']}"
        )

    if not counts:
        print("\nNo hubo lecturas. No se guarda nada.")
        return

    best_key, best_hits = counts.most_common(1)[0]
    mapping[str(physical_ant)] = {
        "logical_key": best_key,
        "hits": best_hits,
        "sample": {
            "logical_slot": samples[best_key]["logical_slot"],
            "freq_ant_hex": f"0x{samples[best_key]['freq_ant']:02X}",
            "rssi": samples[best_key]["rssi"],
            "pc": samples[best_key]["pc"],
            "epc": samples[best_key]["epc"],
        },
    }

    print(f"\nGuardado provisional:")
    print(f"  antena física {physical_ant} -> {best_key}")


def invert_mapping(mapping: dict) -> dict:
    inv = {}
    for physical_ant, info in mapping.items():
        logical_key = info.get("logical_key")
        if logical_key:
            inv[logical_key] = int(physical_ant)
    return inv


def mode_calibrate(args):
    mapping_path = Path(args.mapping)
    mapping = load_mapping(mapping_path)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(RECV_TIMEOUT)
        sock.connect((args.host, args.port))
        print(f"Conectado a {args.host}:{args.port}")

        if args.physical_ant is not None:
            calibrate_one(sock, args.physical_ant, args.seconds, mapping)
        else:
            ants = args.range or "1-16"
            start_s, end_s = ants.split("-")
            start_ant = int(start_s)
            end_ant = int(end_s)

            for ant in range(start_ant, end_ant + 1):
                input(f"\nPulsa Enter cuando tengas el tag colocado SOLO en la antena física {ant}...")
                calibrate_one(sock, ant, args.seconds, mapping)

        save_mapping(mapping_path, mapping)

    print(f"\nMapeo guardado en: {mapping_path}")
    print(json.dumps(mapping, indent=2, ensure_ascii=False))


def mode_read(args):
    mapping_path = Path(args.mapping)
    mapping = load_mapping(mapping_path)
    logical_to_physical = invert_mapping(mapping)

    if not mapping:
        print("No hay mapping todavía. Calibra antes, campeón del caos.")
        return

    seen = {}

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(RECV_TIMEOUT)
        sock.connect((args.host, args.port))
        print(f"Conectado a {args.host}:{args.port}")
        print(f"Usando mapping: {mapping_path}\n")

        while True:
            results = perform_sequence_and_collect(sock)
            now = time.time()

            for item in results:
                if item["type"] != "tag":
                    continue

                dedupe_key = (item["epc"], item["logical_key"])
                if dedupe_key in seen and now - seen[dedupe_key] < args.dedupe_s:
                    continue
                seen[dedupe_key] = now

                physical_ant = logical_to_physical.get(item["logical_key"], None)
                physical_text = str(physical_ant) if physical_ant is not None else f"?({item['logical_key']})"

                print(
                    f"EPC={item['epc']} "
                    f"ANT_FISICA={physical_text} "
                    f"LOGICAL_KEY={item['logical_key']} "
                    f"SLOT={item['logical_slot']} "
                    f"FREQ=0x{item['freq_ant']:02X} "
                    f"RSSI={item['rssi']} "
                    f"PC={item['pc']}"
                )

            time.sleep(LOOP_SLEEP_S)


def mode_show(args):
    mapping_path = Path(args.mapping)
    mapping = load_mapping(mapping_path)
    if not mapping:
        print("No hay mapping guardado.")
        return

    print(json.dumps(mapping, indent=2, ensure_ascii=False))

    print("\nInvertido:")
    logical_to_physical = invert_mapping(mapping)
    print(json.dumps(logical_to_physical, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--mapping", default=DEFAULT_MAPPING)

    subparsers = parser.add_subparsers(dest="mode", required=True)

    p_cal = subparsers.add_parser("calibrate")
    p_cal.add_argument("--physical-ant", type=int, default=None)
    p_cal.add_argument("--range", default=None, help='Ejemplo: "1-16" o "9-16"')
    p_cal.add_argument("--seconds", type=float, default=12.0)

    p_read = subparsers.add_parser("read")
    p_read.add_argument("--dedupe-s", type=float, default=0.5)

    subparsers.add_parser("show")

    args = parser.parse_args()

    if args.mode == "calibrate":
        mode_calibrate(args)
    elif args.mode == "read":
        mode_read(args)
    elif args.mode == "show":
        mode_show(args)


if __name__ == "__main__":
    main()