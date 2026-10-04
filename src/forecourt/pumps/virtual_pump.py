from forecourt.protocol.checksum import checksum
from forecourt.protocol.commands import ACK, AUTHORIZE, END, GET_TRANSACTION, NAK, RESET, START
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
        self.delivered_liters = 0
        self._pending_liters = 0.0

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
        self.delivered_liters = self.preset_liters
        self._pending_liters = 0.0
        self.state = State.FINISHED
        return True

    def advance(self, seconds: float, liters_per_second: float) -> bool:
        """Dispense whole liters while FUELING. Return True when the counter moves.

        The teaching frame can carry only one byte, so the counter steps in
        whole liters. Fractions wait in ``_pending_liters`` until they add up.
        """
        if self.state is not State.FUELING:
            return False
        if seconds < 0 or liters_per_second < 0:
            raise ValueError("seconds and liters_per_second must be >= 0")
        if liters_per_second == 0 or seconds == 0:
            return False
        before = self.delivered_liters
        self._pending_liters += seconds * liters_per_second
        whole = int(self._pending_liters)
        if whole > 0:
            self._pending_liters -= whole
            room = self.preset_liters - self.delivered_liters
            taken = min(whole, max(0, room))
            self.delivered_liters += taken
            if taken < whole:
                self._pending_liters = 0.0
        if self.delivered_liters >= self.preset_liters:
            self.reach_preset()
        return self.state is State.FINISHED or self.delivered_liters != before

    def _dispatch(self, command: int, data: int) -> bytes:
        if command == GET_TRANSACTION:
            return build_frame(self.address, ACK, self.delivered_liters)
        if command in ALWAYS_ALLOWED:
            return self._reply(ACK)
        next_state = ALLOWED.get((self.state, command))
        if next_state is None:
            return self._reply(NAK)
        if command == AUTHORIZE:
            self.preset_liters = data
            self.delivered_liters = 0
            self._pending_liters = 0.0
        if command == RESET:
            self.delivered_liters = 0
            self._pending_liters = 0.0
        self.state = next_state
        if self.state is not State.FUELING:
            self._pending_liters = 0.0
        return self._reply(ACK)

    def _reply(self, result: int) -> bytes:
        return build_frame(self.address, result, self.state.value)
