# -*- coding: utf-8 -*-
"""Re-encode the raw console captures (cp949 from the redirected pytest / update runs) of this evidence folder to UTF-8, line by line: strict UTF-8 first, else cp949."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
changed = 0
for f in sorted(HERE.glob("*.txt")) + sorted(HERE.glob("*.log")):
    raw = f.read_bytes()
    try:
        raw.decode("utf-8")
        continue
    except UnicodeDecodeError:
        pass
    out = []
    nbad = 0
    for line in raw.split(b"\n"):
        try:
            out.append(line.decode("utf-8"))
        except UnicodeDecodeError:
            try:
                out.append(line.decode("cp949"))
            except UnicodeDecodeError:
                out.append(line.decode("cp949", errors="replace"))
                nbad += 1
    f.write_bytes("\n".join(out).encode("utf-8"))
    changed += 1
    print(f"recoded {f.name} (lines that needed replacement chars: {nbad})")
print("files recoded:", changed)
