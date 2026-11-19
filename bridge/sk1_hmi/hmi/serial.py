from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from .protocol import FrameBuffer, HmiEvent, encode_command

log = logging.getLogger(__name__)


class HmiSerial:
    def __init__(
        self,
        port: str,
        baud: int = 115200,
        *,
        dry_run: bool = False,
        on_event: Callable[[HmiEvent], Awaitable[None]] | None = None,
    ) -> None:
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self.on_event = on_event
        self._ser = None
        self._fb = FrameBuffer()
        self._write_q: asyncio.Queue[str] = asyncio.Queue()
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        self._running = True
        if not self.dry_run:
            import serial

            self._ser = serial.Serial(
                self.port,
                self.baud,
                timeout=0.05,
                write_timeout=1,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
            )
            try:
                self._ser.dtr = False
                self._ser.rts = False
            except Exception:
                pass
            log.info("opened HMI serial %s @ %s", self.port, self.baud)
        else:
            log.warning("HMI dry-run mode (no serial)")
        self._tasks = [
            asyncio.create_task(self._reader()),
            asyncio.create_task(self._writer()),
        ]

    async def stop(self) -> None:
        self._running = False
        for t in self._tasks:
            t.cancel()
        if self._ser and self._ser.is_open:
            self._ser.close()

    async def send(self, cmd: str) -> None:
        await self._write_q.put(cmd)

    async def send_many(self, cmds: list[str]) -> None:
        for c in cmds:
            await self._write_q.put(c)

    async def _writer(self) -> None:
        while self._running:
            cmd = await self._write_q.get()
            payload = encode_command(cmd)
            log.debug("HMI TX %s", cmd)
            if self._ser:
                loop = asyncio.get_event_loop()

                def _write() -> None:
                    self._ser.write(payload)
                    self._ser.flush()

                await loop.run_in_executor(None, _write)
            await asyncio.sleep(0.02)

    async def _reader(self) -> None:
        while self._running:
            if self.dry_run:
                await asyncio.sleep(0.2)
                continue
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, self._ser.read, 256)
            if not data:
                await asyncio.sleep(0.02)
                continue
            for ev in self._fb.feed(data):
                # 0x1a = invalid instruction ACK — common noise; keep out of INFO
                if ev.kind.name == "UNKNOWN" and ev.raw == b"\x1a":
                    log.debug("HMI RX ACK invalid (0x1a)")
                else:
                    log.info(
                        "HMI RX kind=%s page=%s comp=%s raw=%s",
                        ev.kind.name,
                        ev.page,
                        ev.component,
                        ev.raw.hex(),
                    )
                if self.on_event:
                    await self.on_event(ev)
