"""Business operations for a forecourt.

This object knows pump numbers, liters, and poll results. It does not
know frame bytes. The driver it holds is either the teaching protocol
or, later, another protocol in the same slot.
"""

from forecourt.drivers.base import PumpDriver, PumpResponse
from forecourt.poll import PollResult, poll_address


class ForecourtController:
    """One driver, many pumps. The driver decides which bytes go out."""

    def __init__(self, driver: PumpDriver, retries: int = 3) -> None:
        if retries < 1:
            raise ValueError(f"retries must be at least 1, got {retries}")
        self.driver = driver
        self.retries = retries

    def status(self, pump: int) -> PumpResponse:
        return self.driver.get_status(pump)

    def authorize(self, pump: int, liters: int) -> PumpResponse:
        return self.driver.authorize(pump, liters)

    def start(self, pump: int) -> PumpResponse:
        return self.driver.start_fueling(pump)

    def stop(self, pump: int) -> PumpResponse:
        return self.driver.stop(pump)

    def reset(self, pump: int) -> PumpResponse:
        return self.driver.reset(pump)

    def transaction(self, pump: int) -> PumpResponse:
        return self.driver.get_transaction(pump)

    def poll_status(self, pump: int) -> PollResult:
        """Read one pump, retrying when the reply is missing or damaged."""
        return poll_address(self.driver.get_status, pump, self.retries)
