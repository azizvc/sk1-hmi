from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path

from .app.reducers import reduce_moonraker
from .app.state import AppState, PrintState, Screen
from .config import AppConfig
from .hmi.protocol import HmiEvent, HmiEventKind
from .hmi.serial import HmiSerial
from .moonraker.client import MoonrakerClient
from .ui.action_handler import apply_intent
from .ui.effect import EffectKind
from .ui.intent import IntentKind, UiIntent
from .ui.render import render_diff, render_full
from .ui.route import route_slider, route_touch

log = logging.getLogger(__name__)

_STATUS_OBJECTS = {
    "extruder": None,
    "heater_bed": None,
    "print_stats": None,
    "virtual_sdcard": None,
    "toolhead": None,
    "gcode_move": None,
    "display_status": None,
    "fan": None,
    "fan_generic Side_fan": None,
    "fan_generic Filter_fan": None,
    "output_pin caselight": None,
    "temperature_sensor toolboard": None,
    "temperature_sensor mcu": None,
    "temperature_sensor chamber": None,
}


class Runtime:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.state = AppState()
        self.hmi = HmiSerial(
            config.hmi.serial,
            config.hmi.baud,
            dry_run=config.hmi.dry_run,
            on_event=self.on_hmi_event,
        )
        self.moonraker = MoonrakerClient(
            config.moonraker.host,
            config.moonraker.port,
            api_key=config.moonraker.api_key,
            on_message=self.on_moonraker_message,
        )
        self._lock = asyncio.Lock()
        self._last_slider: tuple[int, int] | None = None
        self._poll_task = None  # type: asyncio.Task | None
        self._load_task = None  # type: asyncio.Task | None

    async def start(self) -> None:
        await self.hmi.start()
        await self.moonraker.start()
        # Seed state via HTTP so first paint has real temps even if WS lags
        try:
            status = await self.moonraker.query_objects(_STATUS_OBJECTS)
            if status:
                self.state = reduce_moonraker(
                    self.state, {"result": {"status": status}}
                )
                log.info(
                    "seed temps hotend=%.1f bed=%.1f print=%s file=%s",
                    self.state.temps.hotend,
                    self.state.temps.bed,
                    self.state.print.state.name,
                    self.state.print.filename or "-",
                )
        except Exception as exc:  # noqa: BLE001
            log.warning("status seed failed: %s", exc)
        try:
            files = await self.moonraker.list_files()
            self.state.files.entries = files
        except Exception as exc:  # noqa: BLE001
            log.warning("file list failed: %s", exc)
        try:
            net = await self.moonraker.get_network_info()
            self.state.network.hostname = net.get("hostname", "")
            self.state.network.ip = net.get("ip", "")
            self.state.network.ssid = net.get("ssid", "")
        except Exception as exc:  # noqa: BLE001
            log.warning("network info failed: %s", exc)
        self._maybe_follow_print(None)
        cmds = render_full(self.state)
        log.info("HMI initial paint %d cmds screen=%s", len(cmds), self.state.ui.screen.name)
        await self.hmi.send_many(cmds)
        self._poll_task = asyncio.create_task(self._http_poll_loop())

    async def stop(self) -> None:
        if self._poll_task:
            self._poll_task.cancel()
        if self._load_task:
            self._load_task.cancel()
        await self.hmi.stop()
        await self.moonraker.stop()

    def _maybe_follow_print(self, old: AppState | None) -> None:
        """Follow job: Home->Print on start; Print->Home when job ends."""
        active_states = (PrintState.PRINTING, PrintState.PAUSED)
        idle_states = (
            PrintState.STANDBY,
            PrintState.COMPLETE,
            PrintState.CANCELLED,
            PrintState.ERROR,
        )
        active = self.state.print.state in active_states
        was_active = old is not None and old.print.state in active_states

        if active and self.state.ui.screen == Screen.HOME:
            # follow on transition, or on first seed while already printing
            if old is None or not was_active:
                self.state.ui.screen = Screen.PRINT
                log.info(
                    "auto screen PRINT (state=%s file=%s)",
                    self.state.print.state.name,
                    self.state.print.filename or "-",
                )
            return

        if (
            was_active
            and self.state.print.state in idle_states
            and self.state.ui.screen == Screen.PRINT
        ):
            self.state.ui.screen = Screen.HOME
            if not self.state.ui.status_text or self.state.ui.status_text in (
                "Printing",
                "Paused",
                "Heating",
            ):
                label = {
                    PrintState.COMPLETE: "Complete",
                    PrintState.CANCELLED: "Cancelled",
                    PrintState.ERROR: "Error",
                    PrintState.STANDBY: "Standby",
                }.get(self.state.print.state, self.state.print.state.name.title())
                self.state.ui.status_text = label
            log.info(
                "auto screen HOME after print end (state=%s)",
                self.state.print.state.name,
            )

    async def on_hmi_event(self, event: HmiEvent) -> None:
        async with self._lock:
            intent = None  # type: UiIntent | None
            if event.kind == HmiEventKind.INIT:
                intent = UiIntent(IntentKind.DISPLAY_INIT)
            elif event.kind == HmiEventKind.TOUCH:
                log.info(
                    "HMI touch page=%s comp=%s val=%s",
                    event.page,
                    event.component,
                    event.value,
                )
                # Sliders report their value in a separate NUMERIC frame, so
                # remember which slider was touched. A touch on a plain button
                # (one that has a route) clears the pending slider.
                intent = route_touch(event.page, event.component)
                if intent is None:
                    # Only sliders (components with a slider route) can be the
                    # source of a later NUMERIC frame.
                    self._last_slider = (
                        (event.page, event.component)
                        if route_slider(event.page, event.component, 0) is not None
                        else None
                    )
                else:
                    self._last_slider = None
            elif event.kind == HmiEventKind.NUMERIC:
                # 0x71 frame: page/component are not included, so apply the
                # value to the slider that was touched last.
                intent = None
                if self._last_slider is not None:
                    page, comp = self._last_slider
                    log.info("HMI slider page=%s comp=%s value=%s", page, comp, event.value)
                    intent = route_slider(page, comp, event.value)
            elif event.kind == HmiEventKind.UNKNOWN:
                if event.raw != b"\x1a":
                    log.info("HMI unknown frame: %s", event.raw.hex())
            if intent is None:
                return
            log.info("intent %s", intent.kind.name)
            await self._apply(intent)

    async def on_moonraker_message(self, message: dict) -> None:
        async with self._lock:
            await self._ingest_moonraker(message)

    async def _ingest_moonraker(self, message: dict) -> None:
        old = self.state.clone()
        self.state = reduce_moonraker(self.state, message)
        if old.print.state != self.state.print.state:
            log.info(
                "print state %s -> %s file=%s progress=%.1f",
                old.print.state.name,
                self.state.print.state.name,
                self.state.print.filename or "-",
                self.state.print.progress,
            )
        self._maybe_follow_print(old)
        cmds = render_diff(old, self.state)
        if cmds:
            await self.hmi.send_many(cmds)

    async def _refresh_network_info(self) -> None:
        try:
            net = await self.moonraker.get_network_info()
        except Exception as exc:  # noqa: BLE001
            log.debug("network refresh failed: %s", exc)
            return
        self.state.network.hostname = net.get("hostname", "") or self.state.network.hostname
        self.state.network.ip = net.get("ip", "") or self.state.network.ip
        self.state.network.ssid = net.get("ssid", "") or self.state.network.ssid
        log.info("network ip=%s host=%s", self.state.network.ip or "-", self.state.network.hostname or "-")

    async def _refresh_file_list(self) -> None:
        try:
            files = await self.moonraker.list_files()
        except Exception as exc:  # noqa: BLE001
            log.debug("file list refresh failed: %s", exc)
            return
        self.state.files.entries = files
        self.state.files.offset = 0
        if self.state.files.selected >= len(files):
            self.state.files.selected = 0
        log.info("files refreshed count=%d newest=%s", len(files), files[0] if files else "-")

    async def _http_poll_loop(self) -> None:
        """HTTP backup so temps/print progress keep updating if WS notifies lag."""
        while True:
            await asyncio.sleep(2.0)
            try:
                status = await self.moonraker.query_objects(_STATUS_OBJECTS)
            except Exception as exc:  # noqa: BLE001
                log.debug("status poll failed: %s", exc)
                continue
            if not status:
                continue
            async with self._lock:
                await self._ingest_moonraker({"result": {"status": status}})

    async def _apply(self, intent: UiIntent) -> None:
        old = self.state.clone()
        new_state, effects = apply_intent(self.state, intent)
        self.state = new_state
        cmds = render_diff(old, self.state)
        if cmds:
            await self.hmi.send_many(cmds)
        for effect in effects:
            if effect.kind == EffectKind.PAGE:
                if effect.page == Screen.NETWORK.value:
                    await self._refresh_network_info()
                elif effect.page == Screen.FILES.value:
                    await self._refresh_file_list()
                await self.hmi.send(f"page {effect.page}")
                await self.hmi.send_many(render_full(self.state))
            elif effect.kind == EffectKind.SET_BRIGHTNESS:
                await self.hmi.send(f"dim={effect.value}")
            elif effect.kind == EffectKind.GCODE:
                log.info("gcode: %s", effect.script.replace("\n", " | "))
                if intent.kind in (IntentKind.LOAD_FILAMENT, IntentKind.UNLOAD_FILAMENT):
                    if self._load_task and not self._load_task.done():
                        self._load_task.cancel()
                    self._load_task = asyncio.create_task(self._run_load_gcode(effect.script))
                else:
                    try:
                        await self.moonraker.send_gcode(effect.script)
                    except Exception as exc:  # noqa: BLE001
                        log.error("gcode failed: %s", exc)
            elif effect.kind == EffectKind.RESTART_PROCESS:
                log.warning("restart requested")
                await self.stop()
                os.execv(sys.executable, [sys.executable, *sys.argv])

    async def _run_load_gcode(self, script: str) -> None:
        try:
            await self.moonraker.send_gcode(script)
            async with self._lock:
                old = self.state.clone()
                if self.state.load.step in (1, 2):
                    self.state.load.step = 3
                cmds = render_diff(old, self.state)
                if cmds:
                    await self.hmi.send_many(cmds)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            log.error("load/unload gcode failed: %s", exc)
            async with self._lock:
                old = self.state.clone()
                self.state.load.step = 0
                self.state.load.mode = ""
                cmds = render_diff(old, self.state)
                if cmds:
                    await self.hmi.send_many(cmds)


async def run_forever(config: AppConfig) -> None:
    rt = Runtime(config)
    await rt.start()
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await rt.stop()
