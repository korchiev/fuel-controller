def checksum(address: int, command: int, data: int) -> int:
    """One-byte sum of the three payload fields.

    The lesson frame ``02 02 20 32 54 03`` checks out as
    ``(0x02 + 0x20 + 0x32) & 0xFF == 0x54``.
    """
    return (address + command + data) & 0xFF
