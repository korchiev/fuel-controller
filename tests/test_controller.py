import pytest

from forecourt.controller import ForecourtController
from forecourt.drivers.tatsuno import TatsunoDriver
from forecourt.drivers.virtual import EducationalDriver, VirtualPumpDriver
from forecourt.pumps.state import State
from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.virtual import VirtualTransport


def test_educational_driver_is_the_teaching_driver():
    assert VirtualPumpDriver is EducationalDriver


def test_controller_authorize_stays_above_the_frames():
    bus = VirtualTransport()
    bus.attach(VirtualPump(2))
    controller = ForecourtController(EducationalDriver(bus))
    response = controller.authorize(2, 20)
    assert response.ok is True
    assert response.state is State.AUTHORIZED
    assert bus.pump(2).preset_liters == 20
    assert bus.pump(2).delivered_liters == 0


def test_controller_poll_of_a_missing_pump_is_offline():
    bus = VirtualTransport()
    bus.attach(VirtualPump(2))
    controller = ForecourtController(EducationalDriver(bus), retries=2)
    result = controller.poll_status(9)
    assert result.kind == "OFFLINE"
    assert result.detail == "TIMEOUT"
    assert len(result.attempts) == 2


def test_tatsuno_slot_does_not_speak():
    controller = ForecourtController(TatsunoDriver(VirtualTransport()))
    with pytest.raises(NotImplementedError, match="TatsunoDriver"):
        controller.transaction(1)
