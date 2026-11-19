"""Procura strings no .HMI e mostra onde aparecem. Somente leitura."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
needles = sys.argv[2:] or ["b_tab_fan", "tc0"]
data = path.read_bytes()
print(f"file: {path}  size={len(data)}")

for n in needles:
    nb = n.encode("ascii")
    hits = []
    start = 0
    while True:
        i = data.find(nb, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    print(f"\n'{n}': {len(hits)} hit(s)")
    for h in hits[:30]:
        ctx = data[max(0, h - 40):h + len(nb) + 40]
        txt = "".join(chr(c) if 32 <= c < 127 else "." for c in ctx)
        print(f"  0x{h:X} ({h})  ...{txt}...")
