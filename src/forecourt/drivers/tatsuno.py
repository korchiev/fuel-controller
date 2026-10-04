"""Empty slot for a real dispenser protocol.

The controller asks for status, authorize, start, stop, reset, and the
transaction. This class accepts those calls and stops. It does not build
SS-LAN frames and it does not write to the transport.
"""

from forecourt.drivers.base import PumpDriver, PumpResponse
from forecourt.transport.base import Transport


class TatsunoDriver(PumpDriver):
    """Same pump operations as the teaching driver, with no protocol yet."""

    def __init__(self, transport: Transport) -> None:
        self.transport = transport

    def get_status(self, pump: int) -> PumpResponse:
        return self._unavailable()

    def authorize(self, pump: int, liters: int) -> PumpResponse:
        return self._unavailable()

    def start_fueling(self, pump: int) -> PumpResponse:
        return self._unavailable()

    def stop(self, pump: int) -> PumpResponse:
        return self._unavailable()

    def reset(self, pump: int) -> PumpResponse:
        return self._unavailable()

    def get_transaction(self, pump: int) -> PumpResponse:
        return self._unavailable()

    def _unavailable(self) -> PumpResponse:
        raise NotImplementedError(
            "TatsunoDriver is only a slot. It does not speak a dispenser protocol yet."
        )
