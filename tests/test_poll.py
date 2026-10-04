from forecourt.drivers.base import PumpResponse
from forecourt.poll import poll_address
from forecourt.protocol.frame import ChecksumError
from forecourt.pumps.state import State
from forecourt.transport.errors import IncompleteResponse, Timeout


def _response(ok: bool) -> PumpResponse:
    return PumpResponse(ok=ok, state=State.IDLE, request=b"", response=b"\x02")


class ScriptedAsk:
    def __init__(self, events: list[object]) -> None:
        self.events = list(events)
        self.calls = 0

    def __call__(self, address: int) -> PumpResponse:
        self.calls += 1
        event = self.events.pop(0)
        if isinstance(event, Exception):
            raise event
        assert isinstance(event, PumpResponse)
        return event


def test_nak_is_not_retried():
    ask = ScriptedAsk([_response(ok=False), _response(ok=True)])
    result = poll_address(ask, 2, attempts=3)
    assert ask.calls == 1
    assert result.kind == "NAK"
    assert result.detail == "IDLE"


def test_timeouts_become_offline():
    ask = ScriptedAsk([Timeout(1.0), Timeout(1.0), Timeout(1.0)])
    result = poll_address(ask, 9, attempts=3)
    assert ask.calls == 3
    assert result.kind == "OFFLINE"
    assert result.detail == "TIMEOUT"
    assert [item.kind for item in result.attempts] == ["TIMEOUT", "TIMEOUT", "TIMEOUT"]


def test_checksum_error_is_retried_until_ack():
    ask = ScriptedAsk([ChecksumError("bad checksum"), _response(ok=True)])
    result = poll_address(ask, 1, attempts=3)
    assert result.kind == "ACK"
    assert [item.kind for item in result.attempts] == ["BAD CHECKSUM", "ACK"]


def test_short_read_is_retried():
    ask = ScriptedAsk([IncompleteResponse(b"\x02\x02", 6), _response(ok=True)])
    result = poll_address(ask, 1, attempts=2)
    assert result.kind == "ACK"
    assert result.attempts[0].kind == "INCOMPLETE RESPONSE"
