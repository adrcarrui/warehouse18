import socket
import time

HOST = "192.168.0.101"
PORT = 4001
ADDR = 0x01


def checksum(frame_wo_check: bytes) -> int:
    return (~sum(frame_wo_check) + 1) & 0xFF


def build_cmd(cmd: int, data: bytes = b"") -> bytes:
    length = len(data) + 3
    frame = bytearray([0xA0, length, ADDR, cmd])
    frame.extend(data)
    frame.append(checksum(frame))
    return bytes(frame)


def hexs(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def cmd_6c(val):
    return build_cmd(0x6C, bytes([val]))


def cmd_inventory():
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


def extract_frames(buf):
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


def verify(frame):
    return checksum(frame[:-1]) == frame[-1]


def parse(frame):
    if frame[3] != 0x8A:
        return None

    if frame[1] == 0x0A:
        return None

    payload = frame[4:-1]

    freq = payload[0]
    pc = payload[1:3].hex().upper()
    epc = payload[3:-1].hex().upper()
    rssi = payload[-1] & 0x7F

    return epc, pc, rssi, freq


def main():
    rx = bytearray()

    c0 = cmd_6c(0x00)
    c1 = cmd_6c(0x10)
    c2 = cmd_6c(0x01)
    inv = cmd_inventory()

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.1)
        s.connect((HOST, PORT))

        print("Leyendo con secuencia correcta (6C00→6C10→6C01→8A)\n")

        while True:
            s.sendall(c0)
            time.sleep(0.01)

            s.sendall(c1)
            time.sleep(0.01)

            s.sendall(c2)
            time.sleep(0.01)

            s.sendall(inv)

            t0 = time.time()
            while time.time() - t0 < 0.3:
                try:
                    chunk = s.recv(4096)
                    if not chunk:
                        break
                    rx.extend(chunk)

                    for f in extract_frames(rx):
                        if not verify(f):
                            continue

                        parsed = parse(f)
                        if not parsed:
                            continue

                        epc, pc, rssi, freq = parsed

                        print(f"EPC={epc} RSSI={rssi} PC={pc} FREQ=0x{freq:02X}")

                except socket.timeout:
                    break

            time.sleep(0.05)


if __name__ == "__main__":
    main()