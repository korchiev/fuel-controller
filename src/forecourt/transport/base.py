from abc import ABC, abstractmethod


class Transport(ABC):
    """Bytes in, bytes out. The driver does not care what carries them."""

    @abstractmethod
    def exchange(self, frame: bytes) -> bytes | None:
        """Send one frame and return the single reply.

        None means the peer chose silence, as a virtual pump does when the
        address is not its own. A serial port cannot see that difference
        until the timer fires, so SerialTransport raises Timeout instead.
        """
