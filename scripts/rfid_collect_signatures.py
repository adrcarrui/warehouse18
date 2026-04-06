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
READ_WINDOW_S = 0.35
STEP_DELAY = 0.03
LOOP_SLEEP_S = 0.12


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
        "rssi": rssi_raw & 0x7F,
        "logical_slot": logical_slot,
        "logical_key": logical_key,
    }


def do_step(sock, rx, val):
    sock.sendall(cmd_6c(val))
    time.sleep(STEP_DELAY)
    sock.sendall(cmd_inventory())

    results = []
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--physical-ant", type=int, required=True)
    parser.add_argument("--seconds", type=float, default=20.0)
    parser.add_argument("--min-count", type=int, default=3)
    parser.add_argument("--ratio", type=float, default=0.2)
    parser.add_argument("--output", default="scripts/antenna_signatures.json")
    args = parser.parse_args()

    rx = bytearray()
    counts = Counter()
    samples = {}

    print(f"Calibrando antena física {args.physical_ant} durante {args.seconds:.1f}s")
    print("Deja un solo tag quieto SOLO en esa antena.\n")

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(RECV_TIMEOUT)
        s.connect((HOST, PORT))

        end = time.time() + args.seconds
        cycle = 0

        while time.time() < end:
            cycle += 1

            results_1 = do_step(s, rx, 0x01)
            results_0 = do_step(s, rx, 0x00)

            for item in results_1 + results_0:
                if item["type"] != "tag":
                    continue

                key = item["logical_key"]
                counts[key] += 1
                samples[key] = item

                print(
                    f"cycle={cycle} key={key} slot={item['logical_slot']} "
                    f"freq=0x{item['freq_ant']:02X} rssi={item['rssi']} "
                    f"hits={counts[key]}"
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
        print("\nNo hubo lecturas.")
        return

    top_hits = counts.most_common(1)[0][1]
    selected = [
        key for key, hits in counts.items()
        if hits >= args.min_count and hits >= top_hits * args.ratio
    ]

    print("\nFirmas seleccionadas:")
    for key in sorted(selected):
        print(f"  {key}")

    out_path = Path(args.output)
    existing = {}
    if out_path.exists():
        existing = json.loads(out_path.read_text(encoding="utf-8"))

    existing[str(args.physical_ant)] = {
        "logical_keys": sorted(selected),
        "counts": dict(counts),
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nGuardado en: {out_path}")


if __name__ == "__main__":
    main()