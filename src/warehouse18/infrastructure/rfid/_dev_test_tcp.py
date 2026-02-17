# src/warehouse18/infrastructure/rfid/_dev_test_tcp.py

import time

from warehouse18.infrastructure.rfid.tcp_client import RFIDReaderTCP, TCPConnectionConfig
from warehouse18.infrastructure.rfid.parser import (
    decode_frame,
    try_parse_tag_from_inventory,
    pretty_frame,
)


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
                    print(
                        f"[TAG] epc={tag.epc} ant={tag.antenna} "
                        f"rssi_raw={tag.rssi_raw} cmd=0x{tag.cmd:02X}"
                    )
                else:
                    print("[FRAME]", pretty_frame(fr), "RAW=", fr.raw.hex().upper())

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

        # 1) Firmware
        r.send_cmd(0x72)
        print("Enviado 0x72 (firmware). Leyendo 2s...")
        drain_for_seconds(r, 2.0)

        # 2) Inventario usando 0x8A con el payload que YA te funciona
        # (equivalente a tu script del fabricante)
        payload_8a = bytes.fromhex("000101010201030104000500060007000501")
        print("Inventario 0x8A (5s)...")
        r.send_cmd(0x8A, payload_8a)
        drain_for_seconds(r, 5.0)

        print("Fin de prueba.")

    finally:
        r.close()
        print("Cerrado.")


if __name__ == "__main__":
    main()
