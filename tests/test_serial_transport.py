import pytest

from forecourt.transport.errors import IncompleteResponse, Timeout
from forecourt.transport.serial import SerialTransport


class ScriptedPort:
    """Enough of a serial port to test the three read outcomes."""

    def __init__(self, reads: list[bytes]) -> None:
        self.reads = list(reads)
        self.written: list[bytes] = []
        self.is_open = True
        self.in_waiting = 0

    def write(self, data: bytes) -> int:
        self.written.append(bytes(data))
        return len(data)

    def flush(self) -> None:
        return None

    def read(self, size: int) -> bytes:
        if not self.reads:
            return b""
        return self.reads.pop(0)[:size]

    def reset_input_buffer(self) -> None:
        return None

    def close(self) -> None:
        self.is_open = False


def test_exchange_returns_the_scripted_reply():
    port = ScriptedPort([bytes.fromhex("02 02 06 01 09 03")])
    link = SerialTransport("COM-FAKE", link=port)
    reply = link.exchange(bytes.fromhex("02 02 20 32 54 03"))
    assert port.written == [bytes.fromhex("02 02 20 32 54 03")]
    assert reply == bytes.fromhex("02 02 06 01 09 03")


def test_no_bytes_is_a_timeout():
    link = SerialTransport("COM-FAKE", timeout=1.0, link=ScriptedPort([]))
    try:
        link.exchange(b"\x02\x02\x20\x32\x54\x03")
    except Timeout as exc:
        assert exc.timeout == 1.0
        assert "TIMEOUT" in str(exc)
    else:
        raise AssertionError("expected Timeout")


def test_short_read_is_incomplete():
    link = SerialTransport("COM-FAKE", link=ScriptedPort([b"\x02\x02"]))
    try:
        link.exchange(b"\x02\x02\x20\x32\x54\x03")
    except IncompleteResponse as exc:
        assert exc.received == b"\x02\x02"
        assert exc.expected == 6
        assert "INCOMPLETE RESPONSE" in str(exc)
    else:
        raise AssertionError("expected IncompleteResponse")


def test_parity_is_stored_for_the_port_settings():
    link = SerialTransport("COM-FAKE", parity="e", stopbits=2, bytesize=7)
    assert link.parity == "E"
    assert link.stopbits == 2
    assert link.bytesize == 7


def test_unknown_parity_is_rejected():
    with pytest.raises(ValueError, match="parity"):
        SerialTransport("COM-FAKE", parity="Z")
