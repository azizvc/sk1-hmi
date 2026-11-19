"""Dump de uma pagina lendo a TABELA DE ENTRADAS do .HMI (ignora dados orfaos).

Uso:
    python tools/hmi_page.py arquivo.HMI 5
    python tools/hmi_page.py arquivo.HMI lights
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hmi_dump import parse_records, split_objects  # noqa: E402


def entry_bytes(data: bytes, target: str) -> bytes | None:
    count = struct.unpack_from("<I", data, 0)[0]
    for i in range(count):
        base = 4 + i * 28
        name = data[base:base + 16].split(b"\x00", 1)[0].decode("latin-1", "replace")
        off, size, _tag = struct.unpack_from("<III", data, base + 16)
        if name == target:
            return data[off:off + size]
    return None


def dump_page(data: bytes, key: str) -> int:
    payload = entry_bytes(data, f"{key}.pa")
    if payload is None:
        # tenta por nome de pagina: varre as entradas .pa e casa o objname
        count = struct.unpack_from("<I", data, 0)[0]
        for i in range(count):
            base = 4 + i * 28
            name = data[base:base + 16].split(b"\x00", 1)[0].decode("latin-1", "replace")
            if not name.endswith(".pa"):
                continue
            off, size, _tag = struct.unpack_from("<III", data, base + 16)
            pl = data[off:off + size]
            objs = [o for o in split_objects(parse_records(pl)) if o.is_page]
            if objs and objs[0].name == key:
                payload, key = pl, name[:-3]
                break
    if payload is None:
        print(f"pagina nao encontrada: {key}")
        return 1

    objs = split_objects(parse_records(payload))
    page = next((o for o in objs if o.is_page), None)
    comps = [o for o in objs if not o.is_page and o.name]
    print(f"=== {page.name if page else key} ({key}.pa, {len(payload)} bytes): "
          f"{len(comps)} componentes ===")
    for o in sorted(comps, key=lambda o: o.obj_id or 0):
        print(f"  id={o.obj_id:<3} t={o.type_code:<4} {o.name:<16} "
              f"x{o.get('x')} y{o.get('y')} w{o.get('w')} h{o.get('h')}"
              + (" SEND" if o.get("sendkey") else "")
              + (f" txt={o.text('txt')!r}" if o.text("txt") else ""))
    return 0


def main() -> int:
    data = Path(sys.argv[1]).read_bytes()
    return dump_page(data, sys.argv[2])


if __name__ == "__main__":
    raise SystemExit(main())
