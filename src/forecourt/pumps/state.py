from enum import Enum

from forecourt.protocol.commands import AUTHORIZE, GET_STATUS, RESET, START_FUELING, STOP


class State(Enum):
    IDLE = 0x00
    AUTHORIZED = 0x01
    FUELING = 0x02
    FINISHED = 0x03

    @classmethod
    def from_byte(cls, value: int) -> "State":
        try:
            return cls(value)
        except ValueError as exc:
            raise ValueError(f"unknown state byte {value:#04x}") from exc


# Commands that change state. GET_STATUS is allowed in every state and changes nothing.
ALLOWED: dict[tuple[State, int], State] = {
    (State.IDLE, AUTHORIZE): State.AUTHORIZED,
    (State.AUTHORIZED, START_FUELING): State.FUELING,
    (State.FUELING, STOP): State.FINISHED,
    (State.FINISHED, RESET): State.IDLE,
}

ALWAYS_ALLOWED = {GET_STATUS}
