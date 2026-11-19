"""List the touch components of a USART HMI .HMI project, grouped by page.

The .HMI file is a flat record stream. Objects are delimited by ``att-NN``
markers; a page is an object with ``type=121``. The editor may write a page
more than once, so objects are merged per page name and de-duplicated by id.

Usage:
    python tools/hmi_dump.py hmi/sk1-hmi.HMI
    python tools/hmi_dump.py hmi/sk1-hmi.HMI --page lights
    python tools/hmi_dump.py hmi/sk1-hmi.HMI --json

The editor keeps the project file locked while open; close it first or pass a
copy of the file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
from collections import OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

FILE_SHARE_ALL = 0x7  # FILE_SHARE_READ | FILE_SHARE_WRITE | FILE_SHARE_DELETE

PAGE_TYPE = 121
TOUCH_TYPES = {1, 5, 98, 109}  # hotspot, touch cap, button, dual-state button

_NAME_RE = re.compile(rb"^[A-Za-z][A-Za-z0-9_-]{0,15}$")
_ATT_RE = re.compile(r"^att-\d+$")


@dataclass
class Record:
    name: str
    value: bytes
    offset: int

    @property
    def num(self) -> int | None:
        return int.from_bytes(self.value, "little") if self.value else None

    @property
    def text(self) -> str:
        return self.value.rstrip(b"\x00").decode("utf-8", errors="replace")


@dataclass
class HmiObject:
    att: str = ""
    props: dict[str, Record] = field(default_factory=dict)

    def get(self, name: str) -> int | None:
        rec = self.props.get(name)
        return None if rec is None else rec.num

    def text(self, name: str) -> str:
        rec = self.props.get(name)
        return rec.text if rec else ""

    @property
    def name(self) -> str:
        return self.text("objname")

    @property
    def obj_id(self) -> int | None:
        return self.get("id")

    @property
    def type_code(self) -> int | None:
        return self.get("type")

    @property
    def is_page(self) -> bool:
        return self.type_code == PAGE_TYPE

    def as_dict(self) -> dict:
        d = {
            "id": self.obj_id,
            "name": self.name,
            "type": self.type_code,
            "x": self.get("x"),
            "y": self.get("y"),
            "w": self.get("w"),
            "h": self.get("h"),
        }
        for key in ("pic", "sta", "val", "sendkey"):
            v = self.get(key)
            if v is not None:
                d[key] = v
        txt = self.text("txt")
        if txt:
            d["txt"] = txt
        return d


def read_bytes(path: Path) -> bytes:
    """Read the project file even while the editor holds it open.

    On Windows the editor keeps the .HMI handle without FILE_SHARE_READ, so a
    plain open() fails with PermissionError. Reading through CreateFileW with
    FILE_SHARE_READ|WRITE|DELETE works regardless.
    """
    path = Path(path)
    if os.name != "nt":
        return path.read_bytes()

    import ctypes
    from ctypes import wintypes

    GENERIC_READ = 0x80000000
    OPEN_EXISTING = 3
    FILE_ATTRIBUTE_NORMAL = 0x80
    INVALID_HANDLE = ctypes.c_void_p(-1).value

    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.CreateFileW.restype = wintypes.HANDLE
    k32.CreateFileW.argtypes = [
        wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
        wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE,
    ]
    k32.ReadFile.argtypes = [
        wintypes.HANDLE, wintypes.LPVOID, wintypes.DWORD,
        ctypes.POINTER(wintypes.DWORD), wintypes.LPVOID,
    ]

    handle = k32.CreateFileW(
        str(path), GENERIC_READ, FILE_SHARE_ALL, None,
        OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, None,
    )
    if handle == INVALID_HANDLE:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        chunks: list[bytes] = []
        buf = ctypes.create_string_buffer(1 << 20)
        read = wintypes.DWORD()
        while True:
            if not k32.ReadFile(handle, buf, len(buf), ctypes.byref(read), None):
                raise ctypes.WinError(ctypes.get_last_error())
            if read.value == 0:
                break
            chunks.append(buf.raw[: read.value])
        return b"".join(chunks)
    finally:
        k32.CloseHandle(handle)


def parse_records(blob: bytes) -> list[Record]:
    out: list[Record] = []
    i = 0
    n = len(blob)
    while i + 5 <= n:
        (ln,) = struct.unpack_from("<I", blob, i)
        if 1 <= ln <= 4096:
            if ln < 16:
                raw = blob[i + 4 : i + 4 + ln]
                if raw and b"\x00" not in raw and _NAME_RE.match(raw):
                    out.append(Record(raw.decode("ascii"), b"", i))
                    i += 4 + ln
                    continue
            elif i + 20 <= n:
                raw_name = blob[i + 4 : i + 20]
                trimmed = raw_name.rstrip(b"\x00")
                if trimmed and b"\x00" not in trimmed and _NAME_RE.match(trimmed) \
                        and raw_name[len(trimmed):] == b"\x00" * (16 - len(trimmed)):
                    out.append(Record(trimmed.decode("ascii"), blob[i + 20 : i + 4 + ln], i))
                    i += 4 + ln
                    continue
        i += 1
    return out


def split_objects(records: list[Record]) -> list[HmiObject]:
    objs: list[HmiObject] = []
    cur: HmiObject | None = None
    for rec in records:
        if _ATT_RE.match(rec.name):
            cur = HmiObject(att=rec.name[4:])
            objs.append(cur)
            continue
        if cur is None:
            cur = HmiObject()
            objs.append(cur)
        cur.props[rec.name] = rec
    return [o for o in objs if o.name]


def read_entry_table(blob: bytes) -> dict[str, bytes]:
    """Return {entry_name: payload} from the .HMI entry table.

    The editor appends every save as new payloads and leaves the previous ones
    behind as orphans inside the same file. A linear scan of the whole blob
    therefore finds stale objects (an old ``tc0`` next to the current page),
    so the entry table at offset 0 is the only reliable index: it holds the
    name, offset and size of each live payload.
    """
    if len(blob) < 4:
        return {}
    (count,) = struct.unpack_from("<I", blob, 0)
    if not 1 <= count <= 100_000:
        return {}
    table: dict[str, bytes] = {}
    for i in range(count):
        base = 4 + i * 28
        if base + 28 > len(blob):
            break
        raw_name = blob[base:base + 16]
        name = raw_name.split(b"\x00", 1)[0].decode("latin-1", "replace")
        off, size, _tag = struct.unpack_from("<III", blob, base + 16)
        if not name or off + size > len(blob):
            continue
        table[name] = blob[off:off + size]
    return table


def group_pages(blob: bytes) -> "OrderedDict[str, dict[int, dict]]":
    """Return {page_name: {component_id: object_dict}}.

    Payloads come from the entry table, so orphaned data from earlier saves is
    ignored. Pages are keyed by the ``objname`` of their ``.pa`` payload.
    """
    pages: OrderedDict[str, dict[int, dict]] = OrderedDict()

    table = read_entry_table(blob)
    if table:
        sources = [v for k, v in table.items() if k.endswith(".pa")]
    else:
        sources = [blob]

    for payload in sources:
        objs = split_objects(parse_records(payload))
        page = next((o for o in objs if o.is_page), None)
        if page is None:
            continue
        comps: dict[int, dict] = {}
        for obj in objs:
            if obj is page or not obj.name:
                continue
            entry = obj.as_dict()
            if entry["id"] is None:
                continue
            comps.setdefault(entry["id"], entry)
        pages[page.name] = comps
    return pages


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hmi", type=Path)
    ap.add_argument("--page", default=None, help="page name, e.g. lights")
    ap.add_argument("--json", action="store_true")
    ap.add_argument(
        "--snapshot",
        action="store_true",
        help="also write <hmi>.ids.json next to the file (used by the tests "
        "while the editor holds the project open)",
    )
    args = ap.parse_args()

    pages = group_pages(read_bytes(args.hmi))
    if args.snapshot:
        snap = args.hmi.with_suffix(".HMI.ids.json")
        snap.write_text(
            json.dumps({k: list(v.values()) for k, v in pages.items()},
                       indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"snapshot -> {snap}")
    if args.page:
        pages = OrderedDict((k, v) for k, v in pages.items() if k == args.page)
    if args.json:
        print(json.dumps({k: list(v.values()) for k, v in pages.items()},
                         indent=2, ensure_ascii=False))
        return
    for name, comps in pages.items():
        touch = [c for c in comps.values() if c["type"] in TOUCH_TYPES]
        print(f"\n=== {name}: {len(comps)} objetos, {len(touch)} de toque ===")
        for c in sorted(comps.values(), key=lambda c: c["id"]):
            mark = "*" if c["type"] in TOUCH_TYPES else " "
            geom = f"x{c['x']} y{c['y']} w{c['w']} h{c['h']}"
            extra = ""
            if c.get("sendkey"):
                extra += " SEND"
            if "txt" in c:
                extra += f" txt={c['txt']!r}"
            print(f" {mark} id={c['id']:<3} t={c['type']:<4} {c['name']:<18} {geom}{extra}")


if __name__ == "__main__":
    main()
