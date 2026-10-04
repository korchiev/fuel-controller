"""Poll GET_STATUS across several pump addresses, with a short retry.

ACK and NAK stop the retries: the device answered.
TIMEOUT, a short read, and a bad checksum are tried again.
OFFLINE means every attempt in this scan failed.

--interval is only a pause so the log can be read. The bus itself waits
inside exchange(): the next poll starts after this reply, or after the
timeout. Ctrl+C stops the scan.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecourt.controller import ForecourtController
from forecourt.drivers.virtual import EducationalDriver
from forecourt.poll import PollResult
from forecourt.protocol.frame import FRAME_LEN
from forecourt.transport.errors import TransportError
from forecourt.transport.serial import SerialTransport


def parse_addresses(text: str) -> list[int]:
    addresses: list[int] = []
    for part in text.split(","):
        piece = part.strip()
        if not piece:
            continue
        try:
            value = int(piece)
        except ValueError as exc:
            raise ValueError(f"address must be an integer, got {piece!r}") from exc
        if not 0 <= value <= 0xFF:
            raise ValueError(f"address must be 0..255, got {value}")
        if value in addresses:
            raise ValueError(f"address {value} is listed twice")
        addresses.append(value)
    if not addresses:
        raise ValueError("address list is empty")
    return addresses


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll GET_STATUS on several pumps.")
    parser.add_argument("port", help="COM port of this adapter, for example COM6")
    parser.add_argument(
        "--addresses",
        default="1,2,3",
        help="poll order, for example 1,2,3 (default: 1,2,3)",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=0.5,
        help="seconds to wait after each poll so the log stays readable (default: 0.5)",
    )
    parser.add_argument(
        "--scans",
        type=int,
        default=0,
        help="stop after this many full passes; 0 runs until Ctrl+C",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=3,
        help="attempts per address before OFFLINE (default: 3)",
    )
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--parity", default="N", help="N, E, or O (default: N)")
    parser.add_argument("--stopbits", type=int, default=1)
    return parser.parse_args()


def report(result: PollResult, retries: int) -> None:
    for index, attempt in enumerate(result.attempts, start=1):
        if attempt.kind in ("ACK", "NAK"):
            extra = "" if len(result.attempts) == 1 else f" (attempt {index}/{retries})"
            print(f"pump {result.address}: {attempt.kind} {attempt.detail}{extra}")
        else:
            print(f"pump {result.address}: {attempt.kind} (attempt {index}/{retries})")
    if result.kind == "OFFLINE":
        print(f"pump {result.address}: OFFLINE")


def main() -> None:
    args = parse_args()
    if args.interval < 0:
        print("interval must be >= 0", file=sys.stderr)
        sys.exit(1)
    if args.scans < 0:
        print("scans must be >= 0", file=sys.stderr)
        sys.exit(1)
    if args.retries < 1:
        print("retries must be >= 1", file=sys.stderr)
        sys.exit(1)
    try:
        addresses = parse_addresses(args.addresses)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    link = SerialTransport(
        args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        response_size=FRAME_LEN,
        parity=args.parity,
        stopbits=args.stopbits,
    )
    controller = ForecourtController(EducationalDriver(link), retries=args.retries)
    listed = ", ".join(str(address) for address in addresses)
    print(f"Python: {sys.executable}")
    print("driver = EducationalDriver")
    print(
        f"Polling {listed} on {args.port} at {args.baudrate} baud, "
        f"8{args.parity.upper()}{args.stopbits}, timeout={args.timeout}s"
    )
    print(f"GET_STATUS only, {args.retries} attempts, then OFFLINE. Ctrl+C to stop.")
    scan = 0
    try:
        with link:
            while args.scans == 0 or scan < args.scans:
                scan += 1
                print(f"--- scan {scan} ---")
                for address in addresses:
                    result = controller.poll_status(address)
                    report(result, args.retries)
                    if args.interval:
                        time.sleep(args.interval)
    except TransportError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
