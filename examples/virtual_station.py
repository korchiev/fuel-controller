"""Lesson 8: controller and virtual pump talk in binary frames.

Run from the repo root:

    PYTHONPATH=src python examples/virtual_station.py
"""

from forecourt.drivers.virtual import EducationalDriver
from forecourt.protocol.frame import explain
from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.virtual import VirtualTransport


def main() -> None:
    bus = VirtualTransport(on_frame=lambda direction, raw: print(f"  {direction:>2}  {explain(raw)}"))
    bus.attach(VirtualPump(2))
    bus.attach(VirtualPump(3))
    driver = EducationalDriver(bus)

    def step(title: str, response) -> None:
        print(f"\n{title}")
        print(f"  pump 2 = {bus.pump(2).state.name}  preset = {bus.pump(2).preset_liters}")
        print(f"  pump 3 = {bus.pump(3).state.name}")
        print(f"  accepted = {response.ok}")

    step("1. AUTHORIZE pump 2, 50 liters", driver.authorize(2, 50))
    step("2. GET_STATUS pump 3 (pump 2 must stay quiet)", driver.get_status(3))
    step("3. START_FUELING pump 2", driver.start_fueling(2))
    step("4. AUTHORIZE again while FUELING (expect NAK)", driver.authorize(2, 50))
    step("5. STOP pump 2", driver.stop(2))
    step("6. RESET pump 2", driver.reset(2))

    print("\n7. preset reached is an event, not a command")
    driver.authorize(2, 50)
    driver.start_fueling(2)
    changed = bus.pump(2).reach_preset()
    print(f"  reach_preset() = {changed}")
    print(f"  pump 2 = {bus.pump(2).state.name}")


if __name__ == "__main__":
    main()
