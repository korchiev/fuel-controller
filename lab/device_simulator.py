"""Device side: one or more teaching pumps behind a single COM port.

Each VirtualPump has its own address and its own state. A frame is shown
to all of them through VirtualTransport.deliver(). Only the pump with
that address answers. The others stay silent. That is the same multidrop
rule the in-process bus already uses.

Start this before the controller. There is no extra delay before the
reply: the controller is already waiting inside its read timeout.
"""

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecourt.protocol.commands import NAK
from forecourt.protocol.frame import FRAME_LEN, ProtocolError, build_frame, explain, parse_frame
from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.errors import IncompleteResponse, Timeout, TransportError
from forecourt.transport.serial import SerialTransport
from forecourt.transport.virtual import VirtualTransport


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
    parser = argparse.ArgumentParser(
        description="Answer teaching-protocol frames on one COM port."
    )
    parser.add_argument("port", help="COM port of this adapter, for example COM5")
    parser.add_argument(
        "--address",
        type=int,
        default=2,
        help="one pump address, used when --addresses is omitted (default: 2)",
    )
    parser.add_argument(
        "--addresses",
        help="several pumps on this port, for example 1,2,3",
    )
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--parity", default="N", help="N, E, or O (default: N)")
    parser.add_argument("--stopbits", type=int, default=1)
    parser.add_argument(
        "--fault",
        choices=("none", "silence", "nak", "bad-checksum", "short", "delay"),
        default="none",
        help="damage every reply: silence, nak, bad-checksum, short, or delay",
    )
    parser.add_argument(
        "--fault-delay",
        type=float,
        default=2.0,
        help="seconds to wait before a reply when --fault delay (default: 2)",
    )
    return parser.parse_args()


def faulty_bytes(reply: bytes, fault: str) -> bytes:
    """Return the bytes that should actually be written for this fault."""
    if fault == "bad-checksum":
        damaged = bytearray(reply)
        damaged[4] ^= 0xFF
        return bytes(damaged)
    if fault == "short":
        return reply[:2]
    if fault == "nak":
        frame = parse_frame(reply)
        return build_frame(frame.address, NAK, frame.data)
    return reply


def main() -> None:
    args = parse_args()
    if args.fault_delay < 0:
        print("fault-delay must be >= 0", file=sys.stderr)
        sys.exit(1)
    try:
        addresses = parse_addresses(args.addresses) if args.addresses else [args.address]
    except ValueError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    bus = VirtualTransport()
    for address in addresses:
        bus.attach(VirtualPump(address))
    link = SerialTransport(
        args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        response_size=FRAME_LEN,
        parity=args.parity,
        stopbits=args.stopbits,
    )
    listed = ", ".join(str(address) for address in addresses)
    print(f"Python: {sys.executable}")
    print(
        f"Pumps {listed} on {args.port} at {args.baudrate} baud, "
        f"8{args.parity.upper()}{args.stopbits}, timeout={args.timeout}s, "
        f"fault={args.fault}"
    )
    for address in addresses:
        print(f"  pump {address} state = {bus.pump(address).state.name}")
    print("Waiting for a frame. Ctrl+C to stop.")
    try:
        with link:
            while True:
                try:
                    incoming = link.read_exact()
                except Timeout:
                    # The port is idle. This is not a failed request.
                    continue
                except IncompleteResponse as exc:
                    print(exc)
                    continue
                print(explain(incoming))
                try:
                    parse_frame(incoming)
                except ProtocolError as exc:
                    print(f"INVALID FRAME: {exc}")
                if args.fault == "silence":
                    # The pump is left untouched. Silence is "no answer",
                    # not a lost reply after the command was applied.
                    print("fault silence: no bytes will be sent")
                    continue
                reply = bus.deliver(incoming)
                if reply is None:
                    print("no reply: no pump here uses this address")
                    continue
                if args.fault == "delay":
                    # The controller is already inside its read timeout.
                    # A delay longer than that timeout becomes TIMEOUT there.
                    # Bytes that arrive after the controller has moved on
                    # can sit in the port until the next request clears them.
                    print(f"fault delay: waiting {args.fault_delay}s before the reply")
                    time.sleep(args.fault_delay)
                wire = faulty_bytes(reply, args.fault)
                if args.fault == "bad-checksum":
                    print("fault bad-checksum: checksum byte flipped")
                elif args.fault == "short":
                    print("fault short: sending the first 2 bytes only")
                elif args.fault == "nak":
                    print("fault nak: sending NAK instead of the pump reply")
                link.write(wire)
                if len(wire) == FRAME_LEN:
                    print(explain(wire))
                answered = bus.pump(parse_frame(reply).address)
                print(
                    f"pump {answered.address} state = {answered.state.name}"
                    f"  preset = {answered.preset_liters}"
                )
    except TransportError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
