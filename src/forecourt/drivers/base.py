from abc import ABC, abstractmethod
from dataclasses import dataclass

from forecourt.pumps.state import State


@dataclass(frozen=True)
class PumpResponse:
    ok: bool
    state: State | None
    request: bytes
    response: bytes | None


class PumpDriver(ABC):
    """Business commands. Subclasses turn them into protocol bytes."""

    @abstractmethod
    def get_status(self, pump: int) -> PumpResponse:
        raise NotImplementedError

    @abstractmethod
    def authorize(self, pump: int, liters: int) -> PumpResponse:
        raise NotImplementedError

    @abstractmethod
    def start_fueling(self, pump: int) -> PumpResponse:
        raise NotImplementedError

    @abstractmethod
    def stop(self, pump: int) -> PumpResponse:
        raise NotImplementedError

    @abstractmethod
    def reset(self, pump: int) -> PumpResponse:
        raise NotImplementedError
