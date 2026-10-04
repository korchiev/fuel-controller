from collections.abc import Callable

from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.base import Transport

FrameHook = Callable[[str, bytes], None]


class VirtualTransport(Transport):
    """Several virtual pumps on one bus.

    Every pump sees every frame. Only the addressed pump answers.
    That is the multidrop behaviour RS-485 will have later.
    """

    def __init__(self, on_frame: FrameHook | None = None) -> None:
        self._pumps: dict[int, VirtualPump] = {}
        self.on_frame = on_frame

    def attach(self, pump: VirtualPump) -> None:
        if pump.address in self._pumps:
            raise ValueError(f"pump address {pump.address} is already attached")
        self._pumps[pump.address] = pump

    def pump(self, address: int) -> VirtualPump:
        try:
            return self._pumps[address]
        except KeyError as exc:
            raise KeyError(f"no pump at address {address}") from exc

    def exchange(self, frame: bytes) -> bytes | None:
        if self.on_frame is not None:
            self.on_frame("tx", frame)
        replies = []
        for pump in self._pumps.values():
            reply = pump.receive(frame)
            if reply is not None:
                replies.append(reply)
        if len(replies) > 1:
            raise RuntimeError(f"more than one pump answered: {replies!r}")
        reply = replies[0] if replies else None
        if reply is not None and self.on_frame is not None:
            self.on_frame("rx", reply)
        return reply
