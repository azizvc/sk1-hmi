"""Add or clone objects inside a USART HMI .HMI project file.

Objects in the .HMI file are serialized as a flat run of records:

    att-NN                      (marker, no value)
    <u32 len><name, 16 bytes><value>   ...

A page is an object with ``type=121``; the objects that follow belong to it
until the next page record. This tool clones an existing object of the same
kind (so every property the editor expects is present) and rewrites only the
fields you ask for, then appends the new block at the end of the target page.

Usage (always write to a copy first, then open it in the editor to verify):

    python tools/hmi_add.py SRC.HMI DST.HMI spec.json

spec.json is a list of objects to create:

    [
      {"page": "zoffset", "name": "t_title", "template": ["files", "t_title"],
       "x": 16, "y": 9, "w": 200, "h": 22, "txt": "Z Offset"},
      {"page": "zoffset", "name": "b_z_m", "template": ["print", "b_z_m"],
       "x": 74, "y": 177, "w": 50, "h": 34, "sendkey": 1}
    ]

``template`` is ``[page, name]`` of an object to clone; the clone inherits all
of its properties (including the record layout) and the overrides are applied.
New ids continue from the highest id already used on the target page.
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from hmi_dump import HmiObject, parse_records, split_objects  # noqa: E402

PAGE_TYPE = 121
_ATT = "att-"


def serialize_object(obj: HmiObject, order: list[str]) -> bytes:
    out = bytearray()
    att = _ATT + obj.att
    out += struct.pack("<I", len(att)) + att.encode("ascii")
    for name in order:
        rec = obj.props.get(name)
        if rec is None:
            continue
        value = rec.value
        name_bytes = name.encode("ascii")
        if len(name_bytes) < 16:
            block = name_bytes.ljust(16, b"\x00")
            out += struct.pack("<I", 16 + len(value)) + block + value
        else:
            out += struct.pack("<I", len(name_bytes)) + name_bytes + value
    return bytes(out)


def page_blocks(blob: bytes) -> list[dict]:
    """Return [{name, start, end, objects:[(obj, start, end)]}] in file order."""
    records = parse_records(blob)
    objs = split_objects(records)
    # Track byte ranges: each object starts at its att marker and ends where
    # the next att marker starts.
    starts: list[int] = []
    for rec in records:
        if rec.name.startswith(_ATT):
            starts.append(rec.offset - 4 - len(rec.name))
    starts.append(len(blob))
    blocks: list[dict] = []
    for idx, obj in enumerate(objs):
        start, end = starts[idx], starts[idx + 1]
        if obj.type_code == PAGE_TYPE:
            blocks.append({"name": obj.name, "start": start, "end": end, "objects": []})
        elif blocks:
            blocks[-1]["objects"].append({"obj": obj, "start": start, "end": end})
            blocks[-1]["end"] = end
    return blocks


def find_page(blocks: list[dict], name: str) -> dict:
    # The editor may serialize a page twice; the last occurrence is the current one.
    hits = [b for b in blocks if b["name"] == name]
    if not hits:
        raise SystemExit(f"page {name!r} not found")
    return hits[-1]


def find_object(blocks: list[dict], page: str, name: str) -> HmiObject:
    for block in blocks:
        if block["name"] != page:
            continue
        for entry in block["objects"]:
            if entry["obj"].name == name:
                return entry["obj"]
    raise SystemExit(f"template {page}.{name} not found")


def set_value(obj: HmiObject, key: str, value) -> None:
    rec = obj.props.get(key)
    if rec is None:
        raise SystemExit(f"template has no property {key!r}")
    if isinstance(value, str):
        raw = value.encode("utf-8")
    elif isinstance(value, int):
        raw = int(value).to_bytes(len(rec.value) or 1, "little", signed=False)
    else:
        raw = bytes(value)
    rec.value = raw


def apply_spec(blob: bytes, spec: list[dict]) -> bytes:
    blocks = page_blocks(blob)
    inserts: dict[int, bytearray] = {}
    for item in spec:
        page_name = item["page"]
        tpl_page, tpl_name = item.get("template") or (page_name, item["name"])
        template = find_object(blocks, tpl_page, tpl_name)
        block = find_page(blocks, page_name)

        clone = HmiObject(att=template.att, props={k: v for k, v in template.props.items()})
        # Deep copy the records so edits do not touch the template.
        clone.props = {
            k: type(v)(v.name, bytes(v.value), v.offset) for k, v in template.props.items()
        }
        existing = {e["obj"].obj_id for e in block["objects"]}
        next_id = max([i for i in existing if i is not None] + [0]) + 1
        set_value(clone, "id", item.get("id", next_id))
        set_value(clone, "objname", item["name"])
        for key in ("x", "y", "w", "h", "sendkey", "pic", "sta", "val"):
            if key in item:
                set_value(clone, key, item[key])
        if "txt" in item:
            set_value(clone, "txt", item["txt"])

        order = list(template.props.keys())
        payload = serialize_object(clone, order)
        inserts.setdefault(block["end"], bytearray()).extend(payload)
        # Later items in the spec see the id we just used.
        block["objects"].append({"obj": clone, "start": 0, "end": 0})

    out = bytearray()
    cursor = 0
    for offset in sorted(inserts):
        out += blob[cursor:offset]
        out += inserts[offset]
        cursor = offset
    out += blob[cursor:]
    return bytes(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src", type=Path)
    ap.add_argument("dst", type=Path)
    ap.add_argument("spec", type=Path)
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    blob = args.src.read_bytes()
    result = apply_spec(blob, spec)
    args.dst.write_bytes(result)
    print(f"wrote {args.dst} ({len(blob)} -> {len(result)} bytes, {len(spec)} objects)")


if __name__ == "__main__":
    main()
