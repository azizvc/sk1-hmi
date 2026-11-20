from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import aiohttp

log = logging.getLogger(__name__)


def sort_files_newest_first(items: list[Any]) -> list[str]:
    """Sort Moonraker ``/server/files/list`` rows by ``modified`` desc, then name."""
    rows: list[tuple[float, str]] = []
    for item in items:
        if not isinstance(item, dict) or "path" not in item:
            continue
        path = str(item["path"])
        try:
            modified = float(item.get("modified") or 0)
        except (TypeError, ValueError):
            modified = 0.0
        rows.append((modified, path))
    rows.sort(key=lambda row: (-row[0], row[1].lower()))
    return [path for _, path in rows]


# Keep subscribe set conservative for stock SK1 / old Moonraker
SUBSCRIBE_OBJECTS = {
    "print_stats": None,
    "virtual_sdcard": None,
    "extruder": None,
    "heater_bed": None,
    "toolhead": None,
    "gcode_move": None,
    "display_status": None,
    "fan": None,
    "fan_generic Side_fan": None,
    "fan_generic Filter_fan": None,
    "temperature_sensor toolboard": None,
    "temperature_sensor mcu": None,
    "temperature_sensor chamber": None,
}


class MoonrakerClient:
    def __init__(
        self,
        host: str,
        port: int,
        *,
        api_key: str = "",
        on_message: Callable[[dict[str, Any]], Awaitable[None]] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.api_key = api_key
        self.on_message = on_message
        self._session: aiohttp.ClientSession | None = None
        self._ws: aiohttp.ClientWebSocketResponse | None = None
        self._id = 1
        self._running = False
        self._task: asyncio.Task | None = None
        self._last_rx = 0.0
        self._connected = asyncio.Event()

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def ws_url(self) -> str:
        return f"ws://{self.host}:{self.port}/websocket"

    def _headers(self) -> dict[str, str]:
        if self.api_key:
            return {"X-Api-Key": self.api_key}
        return {}

    async def start(self) -> None:
        self._running = True
        self._session = aiohttp.ClientSession()
        self._connected.clear()
        self._task = asyncio.create_task(self._run_loop())
        try:
            await asyncio.wait_for(self._connected.wait(), timeout=8.0)
        except asyncio.TimeoutError:
            log.warning("Moonraker WS not ready after timeout; continuing with HTTP")

    async def stop(self) -> None:
        self._running = False
        if self._ws and not self._ws.closed:
            await self._ws.close()
        if self._session:
            await self._session.close()
        if self._task:
            self._task.cancel()

    async def send_gcode(self, script: str) -> None:
        await self._http_post("/printer/gcode/script", {"script": script})

    async def list_files(self) -> list[str]:
        """Return gcode paths sorted newest-first (Moonraker ``modified``)."""
        result = await self._http_get("/server/files/list", {"root": "gcodes"})
        return sort_files_newest_first(result if isinstance(result, list) else [])

    async def query_objects(self, objects: dict[str, Any]) -> dict[str, Any]:
        result = await self._http_post("/printer/objects/query", {"objects": objects})
        if isinstance(result, dict):
            return result.get("status") or {}
        return {}

    async def get_network_info(self) -> dict[str, str]:
        info: dict[str, str] = {"hostname": "", "ip": "", "ssid": ""}
        try:
            sysinfo = await self._http_get("/machine/system_info")
            if isinstance(sysinfo, dict):
                net = (sysinfo.get("system_info") or {}).get("network", {}) or {}
                preferred: list[str] = []
                others: list[str] = []
                for name, data in net.items():
                    if not isinstance(data, dict):
                        continue
                    bucket = preferred if name in ("wlan0", "eth0", "end0") else others
                    for entry in data.get("ip_addresses") or []:
                        if not isinstance(entry, dict):
                            continue
                        addr = str(entry.get("address", "") or "")
                        fam = str(entry.get("family", "")).lower()
                        if addr.count(".") != 3 and fam not in ("ipv4", "af_inet"):
                            continue
                        if addr and not addr.startswith("127."):
                            bucket.append(addr)
                info["ip"] = (preferred or others or [""])[0]
        except Exception as exc:  # noqa: BLE001
            log.debug("network info failed: %s", exc)
        try:
            ident = await self._http_get("/printer/info")
            if isinstance(ident, dict):
                info["hostname"] = str(ident.get("hostname", ""))
        except Exception:  # noqa: BLE001
            pass
        return info

    async def download_thumbnail(self, path: str) -> bytes | None:
        if not self._session:
            return None
        url = f"{self.base_url}/server/files/gcodes/{path}"
        try:
            meta = await self._http_get("/server/files/metadata", {"filename": path})
            thumbs = meta.get("thumbnails") if isinstance(meta, dict) else None
            if thumbs:
                rel = thumbs[-1].get("relative_path")
                if rel:
                    url = f"{self.base_url}/server/files/gcodes/{rel}"
        except Exception:  # noqa: BLE001
            pass
        async with self._session.get(url, headers=self._headers()) as resp:
            if resp.status != 200:
                return None
            return await resp.read()

    async def _http_get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        assert self._session
        async with self._session.get(
            f"{self.base_url}{path}", params=params or {}, headers=self._headers()
        ) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status} {path}: {data}")
            return data.get("result", data)

    async def _http_post(self, path: str, body: dict[str, Any]) -> Any:
        assert self._session
        async with self._session.post(
            f"{self.base_url}{path}", json=body, headers=self._headers()
        ) as resp:
            data = await resp.json(content_type=None)
            if resp.status >= 400:
                raise RuntimeError(f"HTTP {resp.status} {path}: {data}")
            return data.get("result", data)

    async def _run_loop(self) -> None:
        while self._running:
            try:
                await self._connect_and_listen()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001
                log.warning("Moonraker disconnected: %s", exc)
                self._connected.clear()
            await asyncio.sleep(2.0)

    async def _connect_and_listen(self) -> None:
        assert self._session
        log.info("connecting Moonraker %s", self.ws_url)
        async with self._session.ws_connect(
            self.ws_url, heartbeat=20, headers=self._headers()
        ) as ws:
            self._ws = ws
            req_id = self._id
            self._id += 1
            await ws.send_str(
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "method": "printer.objects.subscribe",
                        "params": {"objects": SUBSCRIBE_OBJECTS},
                        "id": req_id,
                    }
                )
            )
            self._connected.set()
            async for msg in ws:
                if msg.type != aiohttp.WSMsgType.TEXT:
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break
                    continue
                self._last_rx = asyncio.get_event_loop().time()
                data = json.loads(msg.data)
                method = data.get("method")
                if method:
                    log.debug("MR notify %s", method)
                if self.on_message:
                    await self.on_message(data)
