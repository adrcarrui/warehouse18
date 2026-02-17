from warehouse18.infrastructure.rfid.ddct_protocol import build_frame, verify_frame, iter_frames_from_bytes

def main():
    f1 = build_frame(0x72)                 # get firmware
    f2 = build_frame(0x89, b"\x00\x00")    # start inventory (ejemplo)

    assert verify_frame(f1)
    assert verify_frame(f2)

    # Simula llegada troceada y pegada (vida real)
    stream = [
        f1[:2],
        f1[2:] + f2[:3],
        f2[3:],
    ]
    out = list(iter_frames_from_bytes(iter(stream)))
    assert out == [f1, f2]

    print("OK: protocolo y framing funcionan.")

if __name__ == "__main__":
    main()
