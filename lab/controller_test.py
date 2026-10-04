"""Controller side: one teaching-protocol command over RS-485.

VirtualPumpDriver builds the frame. SerialTransport only moves bytes.
parse_frame, inside the driver, decides whether the reply is a valid frame.

The other adapter must already be running device_simulator.py.
The pump remembers its state only while that process stays open.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from forecourt.controller import ForecourtController
from forecourt.drivers.virtual import EducationalDriver
from forecourt.protocol.frame import FRAME_LEN, ProtocolError, explain
from forecourt.transport.errors import IncompleteResponse, Timeout, TransportError
from forecourt.transport.serial import SerialTransport


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send one teaching-protocol command and print the reply."
    )
    parser.add_argument("port", help="COM port of this adapter, for example COM6")
    parser.add_argument(
        "--command",
        choices=("authorize", "start", "stop", "reset", "status", "transaction"),
        default="authorize",
        help="authorize, start, stop, reset, status, or transaction (default: authorize)",
    )
    parser.add_argument("--address", type=int, default=2)
    parser.add_argument(
        "--liters",
        type=int,
        default=50,
        help="used only by authorize (default: 50)",
    )
    parser.add_argument("--baudrate", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=1.0)
    parser.add_argument("--parity", default="N", help="N, E, or O (default: N)")
    parser.add_argument("--stopbits", type=int, default=1)
    return parser.parse_args()


def send(controller: ForecourtController, args: argparse.Namespace):
    if args.command == "authorize":
        return controller.authorize(args.address, args.liters)
    if args.command == "start":
        return controller.start(args.address)
    if args.command == "stop":
        return controller.stop(args.address)
    if args.command == "reset":
        return controller.reset(args.address)
    if args.command == "transaction":
        return controller.transaction(args.address)
    return controller.status(args.address)


def main() -> None:
    args = parse_args()
    link = SerialTransport(
        args.port,
        baudrate=args.baudrate,
        timeout=args.timeout,
        response_size=FRAME_LEN,
        parity=args.parity,
        stopbits=args.stopbits,
    )
    controller = ForecourtController(EducationalDriver(link))
    print(f"Python: {sys.executable}")
    print("driver = EducationalDriver")
    print(
        f"Controller on {args.port} at {args.baudrate} baud, "
        f"8{args.parity.upper()}{args.stopbits}, timeout={args.timeout}s"
    )
    try:
        with link:
            response = send(controller, args)
    except Timeout as exc:
        print(exc)
        sys.exit(1)
    except IncompleteResponse as exc:
        print(exc)
        sys.exit(1)
    except ProtocolError as exc:
        print(f"INVALID FRAME: {exc}")
        sys.exit(1)
    except TransportError as exc:
        print(exc, file=sys.stderr)
        sys.exit(1)

    print(explain(response.request))
    if response.response is None:
        print("TIMEOUT: the transport returned no bytes")
        sys.exit(1)
    print(explain(response.response))
    if response.volume is not None:
        print(f"accepted = {response.ok}  volume = {response.volume} L")
        return
    state = response.state.name if response.state is not None else "none"
    print(f"accepted = {response.ok}  state = {state}")
    if not response.ok:
        print("NAK: the pump answered and refused the command. The state above is its current state.")


if __name__ == "__main__":
    main()
