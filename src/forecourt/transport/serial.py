from forecourt.transport.base import Transport


class SerialTransport(Transport):
    """Placeholder for pySerial and a USB-RS485 adapter.

    The simulator lessons do not open a real port. A later lesson will
    implement exchange() once the teaching protocol is stable.
    """

    def __init__(self, port: str, baudrate: int = 19200) -> None:
        self.port = port
        self.baudrate = baudrate

    def exchange(self, frame: bytes) -> bytes | None:
        raise NotImplementedError(
            "SerialTransport is not implemented yet. "
            f"Would open {self.port} at {self.baudrate} baud via pySerial."
        )
