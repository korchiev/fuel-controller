from forecourt.protocol.commands import ACK, NAK
from forecourt.protocol.frame import build_frame, parse_frame
from forecourt.pumps.state import State
from forecourt.pumps.virtual_pump import VirtualPump


def _reply(pump: VirtualPump, command: int, data: int = 0):
    raw = pump.receive(build_frame(pump.address, command, data))
    assert raw is not None
    return parse_frame(raw)


def test_authorize_frame_moves_idle_to_authorized():
    pump = VirtualPump(address=2)
    reply = _reply(pump, 0x20, 50)
    assert reply.command == ACK
    assert reply.data == State.AUTHORIZED.value
    assert pump.state is State.AUTHORIZED
    assert pump.preset_liters == 50


def test_full_cycle_through_frames():
    pump = VirtualPump(address=2)
    assert _reply(pump, 0x20, 50).command == ACK
    assert pump.state is State.AUTHORIZED
    assert _reply(pump, 0x40).command == ACK
    assert pump.state is State.FUELING
    assert _reply(pump, 0x30).command == ACK
    assert pump.state is State.FINISHED
    assert _reply(pump, 0x50).command == ACK
    assert pump.state is State.IDLE
    assert pump.preset_liters == 50


def test_second_authorize_does_not_change_state():
    pump = VirtualPump(address=2)
    _reply(pump, 0x20, 50)
    reply = _reply(pump, 0x20, 10)
    assert reply.command == NAK
    assert pump.state is State.AUTHORIZED
    assert pump.preset_liters == 50


def test_stop_while_idle_is_nak():
    pump = VirtualPump(address=2)
    reply = _reply(pump, 0x30)
    assert reply.command == NAK
    assert pump.state is State.IDLE


def test_other_pumps_frame_is_silence():
    pump = VirtualPump(address=2)
    assert pump.receive(build_frame(3, 0x10, 0)) is None
    assert pump.state is State.IDLE


def test_bad_checksum_addressed_to_us_is_nak():
    pump = VirtualPump(address=2)
    raw = bytearray(build_frame(2, 0x20, 50))
    raw[4] = 0x00
    reply = parse_frame(pump.receive(bytes(raw)))
    assert reply.command == NAK
    assert pump.state is State.IDLE


def test_short_frame_is_silence():
    pump = VirtualPump(address=2)
    assert pump.receive(b"\x02\x02") is None


def test_preset_reached_is_an_event_not_a_command():
    pump = VirtualPump(address=2)
    assert pump.reach_preset() is False
    _reply(pump, 0x20, 50)
    _reply(pump, 0x40)
    assert pump.reach_preset() is True
    assert pump.state is State.FINISHED
    assert pump.delivered_liters == 50


def test_fueling_counts_whole_liters_up_to_the_preset():
    pump = VirtualPump(address=2)
    _reply(pump, 0x20, 10)
    _reply(pump, 0x40)
    assert pump.advance(0.2, 4) is False
    assert pump.delivered_liters == 0
    assert pump.advance(1, 4) is True
    assert pump.delivered_liters == 4
    assert pump.state is State.FUELING
    assert pump.advance(2, 4) is True
    assert pump.delivered_liters == 10
    assert pump.state is State.FINISHED
    assert _reply(pump, 0x60).data == 10


def test_stop_keeps_the_liters_already_dispensed():
    pump = VirtualPump(address=2)
    _reply(pump, 0x20, 10)
    _reply(pump, 0x40)
    pump.advance(1, 3)
    assert _reply(pump, 0x30).data == State.FINISHED.value
    assert pump.delivered_liters == 3
    assert _reply(pump, 0x60).data == 3


def test_reset_clears_delivered_liters_and_keeps_the_preset():
    pump = VirtualPump(address=2)
    _reply(pump, 0x20, 10)
    _reply(pump, 0x40)
    pump.advance(1, 10)
    assert _reply(pump, 0x50).data == State.IDLE.value
    assert pump.preset_liters == 10
    assert pump.delivered_liters == 0
    assert _reply(pump, 0x60).data == 0


def test_get_status_does_not_change_state():
    pump = VirtualPump(address=2)
    reply = _reply(pump, 0x10)
    assert reply.command == ACK
    assert reply.data == State.IDLE.value
    assert pump.state is State.IDLE
