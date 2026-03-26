import socket
import time

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


def do_step(sock, rx, cycle_label, val):
    sock.sendall(cmd_6c(val))
    time.sleep(STEP_DELAY)
    sock.sendall(cmd_inventory())

    got_tag = False
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
                if not parsed:
                    continue

                if parsed["type"] == "summary":
                    print(
                        f"{cycle_label} step=6C{val:02X} "
                        f"SUMMARY total_read={parsed['total_read']} "
                        f"duration_ms={parsed['duration_ms']}"
                    )
                else:
                    got_tag = True
                    print(
                        f"{cycle_label} step=6C{val:02X} TAG "
                        f"epc={parsed['epc']} "
                        f"logical_key={parsed['logical_key']} "
                        f"slot={parsed['logical_slot']} "
                        f"freq=0x{parsed['freq_ant']:02X} "
                        f"rssi={parsed['rssi']} "
                        f"pc={parsed['pc']}"
                    )

        except socket.timeout:
            break

    return got_tag


def main():
    rx = bytearray()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(RECV_TIMEOUT)
        s.connect((HOST, PORT))

        print("Modo 1-8 candidato: 6C01 -> 8A -> 6C00 -> 8A")
        print("Deja un solo tag quieto SOLO en una antena 1-8.\n")

        cycle = 0
        while True:
            cycle += 1
            label = f"cycle={cycle}"

            got1 = do_step(s, rx, label, 0x01)
            got2 = do_step(s, rx, label, 0x00)

            if not (got1 or got2):
                print(f"{label} sin tags")

            time.sleep(LOOP_SLEEP_S)


if __name__ == "__main__":
    main()