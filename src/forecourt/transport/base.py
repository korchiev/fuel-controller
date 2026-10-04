from abc import ABC, abstractmethod


class Transport(ABC):
    """Bytes in, bytes out. The driver does not care what carries them."""

    @abstractmethod
    def exchange(self, frame: bytes) -> bytes | None:
        """Send one frame. Return the single reply, or None on silence."""
