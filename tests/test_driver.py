from forecourt.drivers.virtual import VirtualPumpDriver
from forecourt.pumps.state import State
from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.virtual import VirtualTransport


def station():
    bus = VirtualTransport()
    bus.attach(VirtualPump(2))
    bus.attach(VirtualPump(3))
    return bus, VirtualPumpDriver(bus)


def test_driver_cycle_on_pump_2_leaves_pump_3_idle():
    bus, driver = station()
    assert driver.authorize(2, 50).state is State.AUTHORIZED
    assert driver.start_fueling(2).state is State.FUELING
    assert driver.stop(2).state is State.FINISHED
    assert driver.reset(2).state is State.IDLE
    assert bus.pump(3).state is State.IDLE
    assert bus.pump(2).preset_liters == 50


def test_missing_pump_is_silence():
    bus = VirtualTransport()
    bus.attach(VirtualPump(2))
    driver = VirtualPumpDriver(bus)
    response = driver.get_status(9)
    assert response.ok is False
    assert response.response is None
    assert response.request == bytes.fromhex("02 09 10 00 19 03")


def test_rejected_command_reports_current_state():
    _, driver = station()
    response = driver.stop(2)
    assert response.ok is False
    assert response.state is State.IDLE


def test_authorize_above_one_byte_is_rejected_before_the_bus():
    _, driver = station()
    try:
        driver.authorize(2, 300)
    except ValueError:
        return
    raise AssertionError("300 liters must not fit in the teaching frame")
