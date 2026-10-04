class TransportError(Exception):
    """The bytes did not cross the link. This is not a protocol verdict."""


class Timeout(TransportError):
    """No bytes arrived before the configured timeout."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(f"TIMEOUT: no response within {timeout} seconds")


class IncompleteResponse(TransportError):
    """Some bytes arrived, but fewer than the caller was waiting for."""

    def __init__(self, received: bytes, expected: int) -> None:
        self.received = received
        self.expected = expected
        super().__init__(
            f"INCOMPLETE RESPONSE: got {len(received)} of {expected} bytes"
        )
