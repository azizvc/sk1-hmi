"""Read the USART HMI (Nextion/TJC) .HMI project container.

Layout discovered by inspection of an editor-saved file:

    u32                  entry count (168)
    entry[count]        28 bytes each, starting at offset 4:
        char  name[16]      NUL padded ascii, or flags+id for unnamed slots
        u32   offset        absolute offset of the payload
        u32   size          payload size in bytes
    (entry table ends at 4 + count*28; a few checksum words follow)
    (zero padding)
    payloads            stored back to back starting at 0x700000

READ ONLY. The header carries checksums this tool does not model, so a
repacked file is rejected by the editor with "Version mismatch". Never write a
modified container by hand; drive the editor instead.

Usage:
    python tools/hmi_archive.py hmi/sk1-hmi.HMI --list
    python tools/hmi_archive.py hmi/sk1-hmi.HMI --extract OUTDIR
"""

from __future__ import annotations

import argparse
import struct
from dataclasses import dataclass
from pathlib import Path

HEADER_SIZE = 4
ENTRY_SIZE = 28
NAME_SIZE = 16
DATA_START = 0x700000


@dataclass
class Entry:
    #: Raw 16 bytes of the name slot. Named entries hold a NUL padded ascii
    #: name; unnamed ones hold flags plus an 8 byte id, which must be kept
    #: verbatim or the editor rejects the file.
    name_raw: bytes
    tag: int
    data: bytes
    offset: int = 0

    @property
    def name(self) -> str:
        if self.name_raw[:1] in (b"", b"\x00"):
            return ""
        return self.name_raw.split(b"\x00", 1)[0].decode("ascii", errors="replace")

    @property
    def size(self) -> int:
        return len(self.data)


def read_archive(blob: bytes) -> list[Entry]:
    (count,) = struct.unpack_from("<I", blob, 0)
    if count == 0 or HEADER_SIZE + count * ENTRY_SIZE > len(blob):
        raise ValueError(f"not an .HMI archive (count={count})")
    entries: list[Entry] = []
    for i in range(count):
        base = HEADER_SIZE + i * ENTRY_SIZE
        raw = bytes(blob[base : base + NAME_SIZE])
        offset, size, tag = struct.unpack_from("<III", blob, base + NAME_SIZE)
        if size == 0:
            data = b""
        elif offset + size <= len(blob):
            data = bytes(blob[offset : offset + size])
        else:
            raise ValueError(f"entry {i} out of bounds {offset}+{size}")
        entries.append(Entry(name_raw=raw, tag=tag, data=data, offset=offset))
    return entries


def write_archive(entries: list[Entry], *, data_start: int = DATA_START) -> bytes:
    """NOT SUPPORTED — kept only to fail loudly.

    The 4 bytes after each entry's size field and the words right after the
    entry table are checksums the editor validates. A repack built from
    ``read_archive`` round-trips to a file the editor rejects with
    "Version mismatch", so editing the container by hand is a dead end.
    """
    raise NotImplementedError(
        "the .HMI header carries checksums; modify the project in the editor"
    )


def load(path: Path) -> list[Entry]:
    from hmi_dump import read_bytes

    return read_archive(read_bytes(path))


def find(entries: list[Entry], name: str) -> Entry | None:
    for entry in entries:
        if entry.name == name:
            return entry
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("hmi", type=Path)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--extract", type=Path, default=None)
    args = ap.parse_args()

    entries = load(args.hmi)
    if args.extract:
        args.extract.mkdir(parents=True, exist_ok=True)
        seen: dict[str, int] = {}
        for i, e in enumerate(entries):
            label = e.name or f"_{i:03d}"
            seen[label] = seen.get(label, 0) + 1
            if seen[label] > 1:
                label = f"{label}.{seen[label]}"
            (args.extract / label).write_bytes(e.data)
        print(f"extracted {len(entries)} files to {args.extract}")

    if args.list or not args.extract:
        total = sum(e.size for e in entries)
        print(f"{len(entries)} entries, {total} payload bytes, "
              f"file {Path(args.hmi).stat().st_size}")
        for i, e in enumerate(entries):
            print(f"  [{i:>3}] {e.name or '-':<16} off=0x{e.offset:<8x} size={e.size}")


if __name__ == "__main__":
    main()
