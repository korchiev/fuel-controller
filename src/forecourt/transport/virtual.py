from collections.abc import Callable

from forecourt.pumps.virtual_pump import VirtualPump
from forecourt.transport.base import Transport

FrameHook = Callable[[str, bytes], None]


class VirtualTransport(Transport):
    """Several virtual pumps on one bus.

    Every pump sees every frame. Only the addressed pump answers.
    deliver() is that rule. The in-process lesson calls it through
    exchange(). The RS-485 simulator calls deliver() itself, because
    the frame has already arrived on the wire.
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

    def deliver(self, frame: bytes) -> bytes | None:
        """Hand one frame to every pump. Return the single reply, or None."""
        replies = []
        for pump in self._pumps.values():
            reply = pump.receive(frame)
            if reply is not None:
                replies.append(reply)
        if len(replies) > 1:
            raise RuntimeError(f"more than one pump answered: {replies!r}")
        return replies[0] if replies else None

    def exchange(self, frame: bytes) -> bytes | None:
        if self.on_frame is not None:
            self.on_frame("tx", frame)
        reply = self.deliver(frame)
        if reply is not None and self.on_frame is not None:
            self.on_frame("rx", reply)
        return reply
