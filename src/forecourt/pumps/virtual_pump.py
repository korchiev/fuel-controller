from forecourt.protocol.checksum import checksum
from forecourt.protocol.commands import ACK, AUTHORIZE, END, NAK, START
from forecourt.protocol.frame import FRAME_LEN, build_frame
from forecourt.pumps.state import ALLOWED, ALWAYS_ALLOWED, State


class VirtualPump:
    """One dispenser on the teaching bus.

    ``receive`` returns response bytes, or ``None`` when the frame is not for
    this pump. Silence is different from NAK: NAK means "this frame was for me
    and I refuse it".
    """

    def __init__(self, address: int) -> None:
        if not 0 <= address <= 0xFF:
            raise ValueError(f"address must be 0..255, got {address!r}")
        self.address = address
        self.state = State.IDLE
        self.preset_liters = 0

    def receive(self, incoming: bytes) -> bytes | None:
        if len(incoming) != FRAME_LEN:
            return None
        start, address, command, data, received, end = incoming
        if address != self.address:
            return None
        if (
            start != START
            or end != END
            or received != checksum(address, command, data)
        ):
            return self._reply(NAK)
        return self._dispatch(command, data)

    def reach_preset(self) -> bool:
        """FUELING event that is not a controller command: the preset was reached."""
        if self.state is not State.FUELING:
            return False
        self.state = State.FINISHED
        return True

    def _dispatch(self, command: int, data: int) -> bytes:
        if command in ALWAYS_ALLOWED:
            return self._reply(ACK)
        next_state = ALLOWED.get((self.state, command))
        if next_state is None:
            return self._reply(NAK)
        if command == AUTHORIZE:
            self.preset_liters = data
        self.state = next_state
        return self._reply(ACK)

    def _reply(self, result: int) -> bytes:
        return build_frame(self.address, result, self.state.value)
