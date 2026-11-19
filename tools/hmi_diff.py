"""Compara dois .HMI entrada por entrada (tabela de 168 x 28 bytes). Somente leitura."""
import struct
import sys
from pathlib import Path


def entries(data):
    count = struct.unpack_from("<I", data, 0)[0]
    out = []
    for i in range(count):
        base = 4 + i * 28
        raw = data[base:base + 16]
        name = raw.split(b"\x00", 1)[0].decode("latin-1", "replace")
        off, size, tag = struct.unpack_from("<III", data, base + 16)
        out.append((i, name, off, size, tag, raw))
    return count, out


a_path, b_path = Path(sys.argv[1]), Path(sys.argv[2])
a, b = a_path.read_bytes(), b_path.read_bytes()
ca, ea = entries(a)
cb, eb = entries(b)
print(f"A={a_path.name} entries={ca}")
print(f"B={b_path.name} entries={cb}")

by_name_a = {e[1]: e for e in ea if e[1]}
by_name_b = {e[1]: e for e in eb if e[1]}

changed = []
for name in sorted(set(by_name_a) | set(by_name_b)):
    x = by_name_a.get(name)
    y = by_name_b.get(name)
    if x is None:
        print(f"ONLY IN B: {name}")
        continue
    if y is None:
        print(f"ONLY IN A: {name}")
        continue
    _, _, offx, szx, tagx, rawx = x
    _, _, offy, szy, tagy, rawy = y
    dx = a[offx:offx + szx]
    dy = b[offy:offy + szy]
    if dx != dy or szx != szy or tagx != tagy:
        n = sum(1 for p, q in zip(dx, dy) if p != q) + abs(len(dx) - len(dy))
        changed.append((name, szx, szy, n, offx, offy, tagx, tagy, dx, dy))

print(f"\n=== {len(changed)} entradas alteradas ===")
for name, szx, szy, n, offx, offy, tagx, tagy, dx, dy in changed:
    print(f"\n{name!r}: size {szx}->{szy}  diffs={n}  off 0x{offx:X}->0x{offy:X}  tag {tagx}->{tagy}")
    # mostra contexto das diferenças em ASCII
    shown = 0
    i = 0
    while i < min(len(dx), len(dy)) and shown < 6:
        if dx[i] != dy[i]:
            lo = max(0, i - 30)
            hi = i + 50
            sa = "".join(chr(c) if 32 <= c < 127 else "." for c in dx[lo:hi])
            sb = "".join(chr(c) if 32 <= c < 127 else "." for c in dy[lo:hi])
            print(f"   @{i}  OLD ...{sa}...")
            print(f"   @{i}  NEW ...{sb}...")
            shown += 1
            i += 40
        i += 1
