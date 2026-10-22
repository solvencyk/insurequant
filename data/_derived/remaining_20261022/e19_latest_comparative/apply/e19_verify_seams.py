# -*- coding: utf-8 -*-
"""Read-only: re-read every set_dangi (3-month printed value) cell of the manifest at its XML line; print value, ACONTEXT (must be a prior-period 3-month context '...QQ'), label."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import e19_verify_plans as V  # noqa: E402

ROOT = V.ROOT
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
man = json.loads((OUT / "e19_manifest.json").read_text(encoding="utf-8"))
L_RE = re.compile(r"(data/dart/[^ :]+\.xml):L(\d+)")
res, lines = [], []
for code, q, it, val, src in man["set_dangi"]:
    refs = L_RE.findall(src)
    scale = 1.0 if code == "KR0005" else 1e6
    rows = []
    for f, ln in refs:
        raw, cx = V.cell_ctx(f, int(ln))
        row, _ = V.row_of(f, int(ln))
        rows.append((int(ln), raw, cx, row[0] if row else None))
    # direct single-line items: compare
    status = "n/a"
    if len(rows) == 1 and code != "KR0005" or (code == "KR0005"):
        # KR0005 refs[0] is the statement line (L45xx of the later filing) ; note-41 line is in the text
        v = V.parse_num(rows[0][1]) if rows[0][1] is not None else None
        if it == 18 and code == "KR0082":
            status = "derived (checked below)"
        elif v is not None:
            status = "OK" if abs(v / scale - val) <= (0.5 if code == "KR0005" else 1e-5) else f"MISMATCH {v/scale}"
    res.append({"cell": [code, q, it], "value": val, "rows": rows, "status": status})
    lines.append(f"{code} {q} item {it:2d} value {val:>16,.6f}  status {status}  rows {[(r[0], r[1], (r[2] or '')[:12], r[3]) for r in rows]}")
# KR0082 item 18 derived: 17 - 19 where 19 = +rev -exp
f = "data/dart/FY2024_Q3/raw/KR0082_DB생명보험/20241114001831.xml"
g = lambda ln: V.parse_num(V.cell_at(f, ln))
i17 = g(25538); rev = g(25584) + g(25607); exp = -(g(25837) + g(25860))
i19 = rev + exp
lines.append(f"KR0082 item18 derived: 17={i17/1e6:.6f} 19={i19/1e6:.6f} -> 18 = {(i17-i19)/1e6:.6f} (manifest 16742.113684)")
# KR0083 item 19: reinsurance finance income - insurance finance expense - (reinsurance finance expense if any) ; manifest gives 2 lines, verify
f = "data/dart/FY2025_Q3/raw/KR0083_푸본현대생명보험/20251114001046.xml"
lines.append(f"KR0083 item19 lines: L21711={V.cell_at(f, 21711)} L21815={V.cell_at(f, 21815)} -> {(V.parse_num(V.cell_at(f,21711)) - V.parse_num(V.cell_at(f,21815)))/1e6:.6f} (manifest -77029.404569)")
(OUT / "e19_verify_seams.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(l[:330] for l in lines))
