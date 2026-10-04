"""Send raw bytes on one COM port.

Default (Phase 2): exactly one byte, 0x41.
0x41 is the number 65. In ASCII that number is the letter A.
The program sends the number, not the two text characters "41".

--frame (Phase 3): the teaching AUTHORIZE frame from src, six binary bytes.
That is build_frame(2, AUTHORIZE, 50), not the text "02 02 20 32 54 03".

Run receiver.py on the other adapter before starting this program.
"""

import argparse
import sys
from pathlib import Path

import serial

# One binary byte. Decimal 65, ASCII "A".
ONE_BYTE = bytes([0x41])


def lesson_frame() -> bytes:
    """Pump 2, AUTHORIZE, 50 liters. The bytes are built in src."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from forecourt.protocol.commands import AUTHORIZE
    from forecourt.protocol.frame import build_frame

    return build_frame(2, AUTHORIZE, 50)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send raw bytes on a serial port.")
    parser.add_argument("port", help="COM port to send on, for example COM6")
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="must match receiver.py (default: 9600)",
    )
    parser.add_argument(
        "--frame",
        action="store_true",
        help="send build_frame(2, AUTHORIZE, 50) instead of the single byte 0x41",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = lesson_frame() if args.frame else ONE_BYTE
    print(f"Python: {sys.executable}")
    print(
        f"Opening {args.port} at {args.baudrate} baud, "
        "8 data bits, parity NONE, 1 stop bit"
    )
    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=1.0,
        ) as link:
            written = link.write(payload)
            # flush() waits until this process has handed the bytes to the
            # port driver. It does not add an extra pause of its own.
            link.flush()
    except serial.SerialException as exc:
        print(f"Could not use {args.port}: {exc}", file=sys.stderr)
        print(
            "Check the port name from list_ports.py, and that no other "
            "program already has this COM port open.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.frame:
        print(f"Transmitted: {written} bytes")
        print(payload.hex(" "))
        return

    value = payload[0]
    print(f"Transmitted: {written} byte")
    print(f"hex: {value:02X}")
    print(f"decimal: {value}")
    print(f"ASCII: {chr(value)}")


if __name__ == "__main__":
    main()
