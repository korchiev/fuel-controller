"""Open one COM port and print bytes that arrive.

Default (Phase 2): print each byte as hex, decimal, and ASCII.
--burst (Phase 3): collect bytes until the line goes quiet, then print
them with spaces between hex bytes. The quiet gap is the read timeout.
This program still does not know what a frame means.

Start this program first, then run sender.py on the other adapter.
A byte sent before the receiver is open is already gone: RS-485 does not
store it.
"""

import argparse
import sys

import serial


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print raw bytes received on one serial port."
    )
    parser.add_argument("port", help="COM port to listen on, for example COM5")
    parser.add_argument(
        "--baudrate",
        type=int,
        default=9600,
        help="must match sender.py (default: 9600)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=1.0,
        help="seconds of silence that end one burst, or one empty read (default: 1)",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="print each quiet-delimited group as hex bytes, for example 02 02 20 32 54 03",
    )
    return parser.parse_args()


def ascii_if_printable(value: int) -> str:
    if 32 <= value <= 126:
        return chr(value)
    return "(not printable)"


def read_burst(link: serial.Serial) -> bytes:
    """Return the next group of bytes, ended by one read that times out.

    The length is not known in advance. At 9600 baud six bytes take about
    6 ms, so they arrive, and the following empty read is the gap after them.
    """
    collected = bytearray()
    while True:
        chunk = link.read(1)
        if chunk:
            collected += chunk
            continue
        if collected:
            return bytes(collected)


def main() -> None:
    args = parse_args()
    print(f"Python: {sys.executable}")
    print(
        f"Listening on {args.port} at {args.baudrate} baud, "
        "8 data bits, parity NONE, 1 stop bit"
    )
    print("Waiting for bytes. Press Ctrl+C to stop.")
    try:
        with serial.Serial(
            port=args.port,
            baudrate=args.baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=args.timeout,
        ) as link:
            while True:
                # timeout makes read() return b"" instead of blocking forever,
                # so Ctrl+C is noticed between waits.
                if args.burst:
                    data = read_burst(link)
                    print(f"Received {len(data)} bytes:")
                    print(data.hex(" "))
                    continue
                chunk = link.read(1)
                if not chunk:
                    continue
                value = chunk[0]
                print("Received:")
                print(f"hex: {value:02X}")
                print(f"decimal: {value}")
                print(f"ASCII: {ascii_if_printable(value)}")
    except serial.SerialException as exc:
        print(f"Could not use {args.port}: {exc}", file=sys.stderr)
        print(
            "Check the port name from list_ports.py, and that no other "
            "program already has this COM port open.",
            file=sys.stderr,
        )
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
