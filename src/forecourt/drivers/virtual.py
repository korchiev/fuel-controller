from forecourt.drivers.base import PumpDriver, PumpResponse
from forecourt.protocol.commands import (
    ACK,
    AUTHORIZE,
    GET_STATUS,
    GET_TRANSACTION,
    RESET,
    START_FUELING,
    STOP,
)
from forecourt.protocol.frame import build_frame, parse_frame
from forecourt.pumps.state import State
from forecourt.transport.base import Transport


class EducationalDriver(PumpDriver):
    """Teaching protocol behind the pump interface.

    This class is the only place that turns authorize(), start(), and
    get_transaction() into the six-byte lesson frames. A future dispenser
    protocol replaces this class, not the controller above it.
    """

    def __init__(self, transport: Transport) -> None:
        self.transport = transport

    def get_status(self, pump: int) -> PumpResponse:
        return self._roundtrip(pump, GET_STATUS, 0)

    def authorize(self, pump: int, liters: int) -> PumpResponse:
        if not 0 <= liters <= 0xFF:
            raise ValueError(
                f"teaching protocol stores liters in one byte, got {liters}"
            )
        return self._roundtrip(pump, AUTHORIZE, liters)

    def start_fueling(self, pump: int) -> PumpResponse:
        return self._roundtrip(pump, START_FUELING, 0)

    def stop(self, pump: int) -> PumpResponse:
        return self._roundtrip(pump, STOP, 0)

    def reset(self, pump: int) -> PumpResponse:
        return self._roundtrip(pump, RESET, 0)

    def get_transaction(self, pump: int) -> PumpResponse:
        request = build_frame(pump, GET_TRANSACTION, 0)
        raw = self.transport.exchange(request)
        if raw is None:
            return PumpResponse(
                ok=False, state=None, request=request, response=None, volume=None
            )
        frame = parse_frame(raw)
        # DATA in this reply is dispensed liters, not a state number.
        volume = frame.data if frame.command == ACK else None
        return PumpResponse(
            ok=frame.command == ACK,
            state=None,
            request=request,
            response=raw,
            volume=volume,
        )

    def _roundtrip(self, pump: int, command: int, data: int) -> PumpResponse:
        request = build_frame(pump, command, data)
        raw = self.transport.exchange(request)
        if raw is None:
            return PumpResponse(ok=False, state=None, request=request, response=None)
        frame = parse_frame(raw)
        state = State.from_byte(frame.data)
        return PumpResponse(
            ok=frame.command == ACK,
            state=state,
            request=request,
            response=raw,
        )


# Older lessons constructed this name. It is the same driver.
VirtualPumpDriver = EducationalDriver
