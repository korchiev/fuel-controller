"""Phase 1: list serial ports this Python process can actually open.

The USB-RS485 adapters are plugged into Windows, so Windows Python is the
process that can see COM3, COM4, and so on. The same script inside WSL
usually prints nothing, because WSL does not receive those USB devices.

This script does not open a port and does not guess which one is an adapter.
"""

import sys

from serial.tools import list_ports


def main() -> None:
    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found.")
        print(f"This Python is: {sys.executable}")
        print("Run this file with Windows Python while both adapters are plugged in.")
        return

    print(f"Python: {sys.executable}")
    print(f"Ports: {len(ports)}")
    for port in ports:
        print()
        print(port.device)
        print(f"  description:  {port.description}")
        print(f"  hwid:          {port.hwid}")
        if port.manufacturer:
            print(f"  manufacturer:  {port.manufacturer}")
        if port.serial_number:
            print(f"  serial:        {port.serial_number}")


if __name__ == "__main__":
    main()
