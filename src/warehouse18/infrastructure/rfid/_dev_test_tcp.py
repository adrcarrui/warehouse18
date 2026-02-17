import time

from warehouse18.infrastructure.rfid.tcp_client import RFIDReaderTCP, TCPConnectionConfig
from warehouse18.infrastructure.rfid.parser import decode_frame, try_parse_tag_from_inventory, pretty_frame


def drain_for_seconds(reader: RFIDReaderTCP, seconds: float) -> int:
    """
    Lee frames durante 'seconds' segundos.
    Devuelve cuántos frames se recibieron.
    """
    deadline = time.time() + seconds
    count = 0

    while time.time() < deadline:
        try:
            for raw in reader.frames():
                fr = decode_frame(raw)
                tag = try_parse_tag_from_inventory(fr)
                if tag:
                    print(f"[TAG] epc={tag.epc} ant={tag.antenna} rssi_raw={tag.rssi_raw} cmd=0x{tag.cmd:02X}")
                else:
                    print("[FRAME]", pretty_frame(fr))
                count += 1
                break  # leemos 1 frame por iteración para reevaluar deadline
        except TimeoutError:
            # No llegó nada en este segundo: seguimos hasta deadline
            continue

    return count


def main():
    cfg = TCPConnectionConfig(host="192.168.0.178", port=4001)
    r = RFIDReaderTCP(cfg)

    try:
        r.connect()
        print("Conectado.")

        # 1) firmware
        r.send_cmd(0x72)
        print("Enviado 0x72 (firmware). Leyendo 2s...")
        drain_for_seconds(r, 2.0)

        # 2) intento inventario 0x89 (start)
        print("Intento inventario 0x89 start (2s)...")
        r.send_cmd(0x89, b"\x00\x00")
        n89 = drain_for_seconds(r, 2.0)

        # stop 0x89 (por higiene)
        try:
            r.send_cmd(0x89, b"\x01\x00")
        except Exception:
            pass

        # 3) si no hubo nada, intento 0x8A con payload mínimo (placeholder)
        if n89 == 0:
            print("No hubo frames con 0x89. Intento inventario 0x8A (2s)...")
            # NOTA: el payload exacto depende del lector. Esto es un “mínimo” típico para probar si responde algo.
            # Si el lector lo rechaza, al menos veremos el error/ack.
            # 0x8A suele requerir parámetros de antenas/tiempos. Ajustaremos cuando tengas el YR3004M.
            r.send_cmd(0x8A, b"\x00\x01\x00\x00\x00")
            drain_for_seconds(r, 2.0)

        print("Fin de prueba.")

    finally:
        r.close()
        print("Cerrado.")


if __name__ == "__main__":
    main()
