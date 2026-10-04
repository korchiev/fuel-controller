"""Retry one poll and name the outcome.

ACK and NAK are final. The device spoke, so another copy of the same
request is a different question.

TIMEOUT, a short read, and a damaged frame are tried again. OFFLINE
means every attempt in this round failed. The next round starts over.
"""

from collections.abc import Callable
from dataclasses import dataclass

from forecourt.drivers.base import PumpResponse
from forecourt.protocol.frame import ChecksumError, ProtocolError
from forecourt.transport.errors import IncompleteResponse, Timeout

Ask = Callable[[int], PumpResponse]


@dataclass(frozen=True)
class Attempt:
    kind: str
    detail: str


@dataclass(frozen=True)
class PollResult:
    address: int
    kind: str
    detail: str
    attempts: tuple[Attempt, ...]


def _one(ask: Ask, address: int) -> Attempt:
    try:
        response = ask(address)
    except Timeout:
        return Attempt("TIMEOUT", "")
    except IncompleteResponse:
        return Attempt("INCOMPLETE RESPONSE", "")
    except ChecksumError:
        return Attempt("BAD CHECKSUM", "")
    except ProtocolError:
        return Attempt("INVALID FRAME", "")
    if response.response is None:
        return Attempt("TIMEOUT", "")
    state = response.state.name if response.state is not None else "none"
    if response.ok:
        return Attempt("ACK", state)
    return Attempt("NAK", state)


def poll_address(ask: Ask, address: int, attempts: int) -> PollResult:
    """Ask one address up to ``attempts`` times."""
    if attempts < 1:
        raise ValueError(f"attempts must be at least 1, got {attempts}")
    seen: list[Attempt] = []
    for _ in range(attempts):
        outcome = _one(ask, address)
        seen.append(outcome)
        if outcome.kind in ("ACK", "NAK"):
            return PollResult(address, outcome.kind, outcome.detail, tuple(seen))
    last = seen[-1]
    return PollResult(address, "OFFLINE", last.kind, tuple(seen))
