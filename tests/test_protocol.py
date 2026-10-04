import pytest

from forecourt.protocol.checksum import checksum
from forecourt.protocol.commands import AUTHORIZE
from forecourt.protocol.frame import ProtocolError, build_frame, explain, parse_frame


def test_lesson_authorize_frame_bytes():
    frame = build_frame(address=2, command=AUTHORIZE, data=50)
    assert frame == bytes((0x02, 0x02, 0x20, 0x32, 0x54, 0x03))
    assert checksum(0x02, 0x20, 0x32) == 0x54


def test_frames_from_the_lesson():
    assert build_frame(1, 0x30, 0) == bytes.fromhex("02 01 30 00 31 03")
    assert build_frame(3, 0x10, 0) == bytes.fromhex("02 03 10 00 13 03")


def test_parse_roundtrip():
    raw = build_frame(2, AUTHORIZE, 50)
    frame = parse_frame(raw)
    assert frame.address == 2
    assert frame.command == AUTHORIZE
    assert frame.data == 50
    assert frame.to_bytes() == raw


def test_bad_checksum_is_rejected():
    raw = bytearray(build_frame(2, AUTHORIZE, 50))
    raw[4] = 0x00
    with pytest.raises(ProtocolError, match="checksum"):
        parse_frame(bytes(raw))


def test_explain_names_the_authorize_command():
    text = explain(build_frame(2, AUTHORIZE, 50))
    assert "AUTHORIZE" in text
    assert "50 liters" in text
    assert "OK" in text
