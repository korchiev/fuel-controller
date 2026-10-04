"""Phase 4, device side: one teaching pump behind a COM port.

The pump object already lives in src. This script only carries bytes
between the serial port and VirtualPump.receive(). A frame for another
address produces no reply. A bad frame for this address produces NAK.

Start this before controller_test.py. There is no extra delay before the
reply: the controller is already waiting inside its read timeout.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecourt.protocol.frame import FRAME_LEN, ProtocolError, explain, parse_frame
from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.errors import IncompleteResponse, Timeout, TransportError
from forecourt.transport.serial import SerialTransport


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Answer teaching-protocol frames on one COM port."
    )
    parser.add_argument("port", help="COM port of this adapter, for example COM5")
    parser.add_argument("--address", type=int, default=2, help="pump address (default: 2)")
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--parity", default="N", help="N, E, or O (default: N)")
    parser.add_argument("--stopbits", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pump = VirtualPump(args.address)
    link = SerialTransport(
        args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        response_size=FRAME_LEN,
        parity=args.parity,
        stopbits=args.stopbits,
    )
    print(f"Python: {sys.executable}")
    print(
        f"Pump {pump.address} on {args.port} at {args.baudrate} baud, "
        f"8{args.parity.upper()}{args.stopbits}, timeout={args.timeout}s"
    )
    print(f"state = {pump.state.name}. Waiting for a frame. Ctrl+C to stop.")
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
                reply = pump.receive(incoming)
                if reply is None:
                    print("no reply: frame was not for this pump")
                    continue
                link.write(reply)
                print(explain(reply))
                print(f"state = {pump.state.name}  preset = {pump.preset_liters}")
    except TransportError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
