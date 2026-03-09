import socket
import time

HOST = "192.168.0.101"
PORT = 4001

HEADER = "A0"

def checksum(hex_bytes):
    data = bytes.fromhex(hex_bytes)
    total = sum(data)
    return f"{(256 - (total % 256)) % 256:02X}"

def build_frame(body_hex):
    body_hex = body_hex.replace(" ", "").upper()
    full = HEADER + body_hex
    chk = checksum(full)
    return bytes.fromhex(full + chk)

def parse_8A(resp_bytes):
    hex_data = resp_bytes.hex().upper()

    if not hex_data.startswith("A0"):
        return None

    if hex_data[6:8] != "8A":
        return None

    freq_ant = int(hex_data[8:10], 16)
    ant_id = freq_ant & 0x03
    epc = hex_data[14:-4]

    return ant_id, epc


# MISMA trama que usabas en RFIDfull.py
BODY = "15018A000101010201030104000500060007000501"
FRAME = build_frame(BODY)
print("Trama a enviar:", FRAME.hex().upper())
print("Iniciando prueba simple RFID...")
print("Acerca una tag a la antena...\n")

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            s.sendall(FRAME)
            resp = s.recv(1024)

        result = parse_8A(resp)
        if result:
            ant, epc = result
            print(f"TAG detectada | Antena: {ant} | EPC: {epc}")
        else:
            print("Sin tag...")

        time.sleep(0.5)

    except KeyboardInterrupt:
        print("Fin de prueba.")
        break
    