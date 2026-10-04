"""Byte exchange over a COM port.

This class does not know addresses, commands, or checksums. The caller
decides how many reply bytes to wait for. The teaching frames happen to
be 6 bytes; that number is passed in, not discovered here.

9600 8N1 is the setting that already carried a byte across the two
USB-RS485 adapters in the lab. It is not a Tatsuno setting.
"""

import serial

from forecourt.transport.base import Transport
from forecourt.transport.errors import IncompleteResponse, Timeout, TransportError

_PARITY = {
    "N": serial.PARITY_NONE,
    "E": serial.PARITY_EVEN,
    "O": serial.PARITY_ODD,
}
_BYTESIZE = {
    8: serial.EIGHTBITS,
    7: serial.SEVENBITS,
}
_STOPBITS = {
    1: serial.STOPBITS_ONE,
    2: serial.STOPBITS_TWO,
}


class SerialTransport(Transport):
    """Write a request, then read one reply from a serial port."""

    def __init__(
        self,
        port: str,
        baudrate: int = 9600,
        timeout: float = 1.0,
        response_size: int = 6,
        bytesize: int = 8,
        parity: str = "N",
        stopbits: int = 1,
        link: serial.Serial | None = None,
    ) -> None:
        if response_size < 1:
            raise ValueError(f"response_size must be at least 1, got {response_size}")
        if parity.upper() not in _PARITY:
            raise ValueError("parity must be N, E, or O")
        if bytesize not in _BYTESIZE:
            raise ValueError("bytesize must be 7 or 8")
        if stopbits not in _STOPBITS:
            raise ValueError("stopbits must be 1 or 2")
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.response_size = response_size
        self.bytesize = bytesize
        self.parity = parity.upper()
        self.stopbits = stopbits
        # Tests pass an already-open fake. The lab leaves this empty and
        # open() creates the real COM port.
        self._link = link
        self._owns_link = link is None

    def open(self) -> None:
        if self._link is not None and self._link.is_open:
            return
        try:
            self._link = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=_BYTESIZE[self.bytesize],
                parity=_PARITY[self.parity],
                stopbits=_STOPBITS[self.stopbits],
                timeout=self.timeout,
                write_timeout=self.timeout,
            )
        except serial.SerialException as exc:
            raise TransportError(f"could not open {self.port}: {exc}") from exc

    def close(self) -> None:
        if self._link is not None and self._owns_link:
            self._link.close()
            self._link = None

    def __enter__(self) -> "SerialTransport":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()

    def write(self, frame: bytes) -> None:
        """Send bytes and wait until they have left this process."""
        self.open()
        assert self._link is not None
        self._link.write(frame)
        # flush() returns when the port driver has accepted the bytes.
        # It is not an extra pause before reading the reply.
        self._link.flush()
        print(f"TX [{len(frame)} bytes]: {frame.hex(' ')}")

    def read_exact(self) -> bytes:
        """Read response_size bytes, or name the kind of miss."""
        self.open()
        assert self._link is not None
        data = self._link.read(self.response_size)
        if len(data) == self.response_size:
            print(f"RX [{len(data)} bytes]: {data.hex(' ')}")
            return data
        if len(data) == 0:
            raise Timeout(self.timeout)
        print(f"RX [{len(data)} bytes]: {data.hex(' ')}")
        raise IncompleteResponse(data, self.response_size)

    def exchange(self, frame: bytes) -> bytes:
        """Send one request and return the reply bytes.

        Raises Timeout when nothing arrives. Raises IncompleteResponse
        when the reply is shorter than response_size. A wrong checksum
        is not decided here.
        """
        self.open()
        assert self._link is not None
        # Bytes left from an earlier attempt would be mistaken for this reply.
        self._link.reset_input_buffer()
        self.write(frame)
        reply = self.read_exact()
        extra = self._link.in_waiting
        if extra:
            print(f"NOTE: {extra} more bytes are already waiting")
        return reply
