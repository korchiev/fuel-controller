from dataclasses import dataclass

from forecourt.protocol.checksum import checksum
from forecourt.protocol.commands import END, START, command_name

FRAME_LEN = 6


class ProtocolError(Exception):
    """A frame is the wrong length, badly framed, or has a bad checksum."""


@dataclass(frozen=True)
class Frame:
    address: int
    command: int
    data: int

    def to_bytes(self) -> bytes:
        return build_frame(self.address, self.command, self.data)


def _byte(name: str, value: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 0xFF:
        raise ValueError(f"{name} must be an integer 0..255, got {value!r}")


def build_frame(address: int, command: int, data: int) -> bytes:
    """Encode ``START address command data checksum END``."""
    _byte("address", address)
    _byte("command", command)
    _byte("data", data)
    return bytes((START, address, command, data, checksum(address, command, data), END))


def parse_frame(raw: bytes) -> Frame:
    """Decode a frame. Raises ProtocolError when the frame is not trustworthy."""
    if len(raw) != FRAME_LEN:
        raise ProtocolError(f"expected {FRAME_LEN} bytes, got {len(raw)}")
    start, address, command, data, received, end = raw
    if start != START or end != END:
        raise ProtocolError(
            f"bad framing start={start:02X} end={end:02X}"
        )
    expected = checksum(address, command, data)
    if received != expected:
        raise ProtocolError(
            f"bad checksum got={received:02X} expected={expected:02X}"
        )
    return Frame(address, command, data)


def explain(raw: bytes) -> str:
    """Human-readable breakdown of one 6-byte frame, valid or not."""
    if len(raw) != FRAME_LEN:
        return f"len={len(raw)} raw={raw.hex(' ')} (not a 6-byte frame)"
    start, address, command, data, received, end = raw
    expected = checksum(address, command, data)
    checksum_mark = "OK" if received == expected else f"BAD expected={expected:02X}"
    framing = "OK" if start == START and end == END else "BAD"
    data_text = str(data)
    if command_name(command) == "AUTHORIZE":
        data_text = f"{data} liters"
    return (
        f"{raw.hex(' ')}  "
        f"START={start:02X} ADDRESS={address} "
        f"COMMAND={command_name(command)}({command:02X}) "
        f"DATA={data_text} CHECKSUM={received:02X} {checksum_mark} "
        f"END={end:02X} framing={framing}"
    )
