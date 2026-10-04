"""Teaching protocol. These bytes are not Tatsuno SS-LAN."""

START = 0x02
END = 0x03

ACK = 0x06
NAK = 0x15

GET_STATUS = 0x10
AUTHORIZE = 0x20
STOP = 0x30
START_FUELING = 0x40
RESET = 0x50
GET_TRANSACTION = 0x60

COMMAND_NAMES = {
    GET_STATUS: "GET_STATUS",
    AUTHORIZE: "AUTHORIZE",
    STOP: "STOP",
    START_FUELING: "START_FUELING",
    RESET: "RESET",
    GET_TRANSACTION: "GET_TRANSACTION",
    ACK: "ACK",
    NAK: "NAK",
}


def command_name(command: int) -> str:
    return COMMAND_NAMES.get(command, f"UNKNOWN({command:02X})")
