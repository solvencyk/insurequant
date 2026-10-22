# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e19_latest_comparative")
import KR0070_xml as X
from pathlib import Path
OUT = X.ROOT / "data/_derived/remaining_20261022/e19_latest_comparative"
L = []
for fy in X.FILES:
    s, e, rows = X.read_statement(fy)
    L.append(f"=== {fy} {X.FILES[fy]} stmt L{s}-L{e} rows={len(rows)}")
    ctxs = sorted({X.short_ctx(c['ctx']) for r in rows for c in r['cells']})
    L.append("  contexts: " + ", ".join(ctxs))
    for r in rows:
        lab = r["label"][0] if r["label"] else "?"
        parts = [f"{X.short_ctx(c['ctx'])}={c['text']}@{c['line']}" for c in r["cells"]]
        L.append(f"  R{r['tr_line']} [{lab}] " + " | ".join(parts))
(OUT / "KR0070_stmt_dump.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
print(len(L))
