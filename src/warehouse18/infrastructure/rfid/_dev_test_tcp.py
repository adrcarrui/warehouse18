# src/warehouse18/infrastructure/rfid/_dev_test_tcp.py

import socket
from warehouse18.infrastructure.rfid.tcp_client import (
    RFIDReaderTCP,
    TCPConnectionConfig,
)


def main():
    # AJUSTA ESTO
    cfg = TCPConnectionConfig(
        host="192.168.0.178",
        port=4001,
        connect_timeout=3.0,
        recv_size=4096,
    )

    r = RFIDReaderTCP(cfg)

    try:
        r.connect()
        print("Conectado.")

        # 0x72 = Get firmware version
        r.send_cmd(0x71)
        print("Enviado cmd 0x72 (firmware). Esperando frames...")

        n = 0

        try:
            for f in r.frames():
                print("FRAME:", f.hex().upper())
                n += 1
                break  # solo queremos el primer frame en este test
        except (TimeoutError, socket.timeout):
            print("Timeout esperando más datos.")

    finally:
        r.close()
        print("Cerrado.")


if __name__ == "__main__":
    main()
