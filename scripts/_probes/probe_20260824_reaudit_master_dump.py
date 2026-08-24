# -*- coding: utf-8 -*-
"""Read-only: dump master cells for the re-audit target companies (KR0094, KR0032)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "kics_disclosure.json"
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_master_cells.txt"

K_CODE, K_NAME, K_NO, K_ITEM, K_Q = "원보험사코드", "원수사명", "항목번호", "항목명", "공시분기"
K_V, K_VA = "값", "값_적용후"

recs = json.loads(MASTER.read_text(encoding="utf-8"))
buf = []
for code in ("KR0094", "KR0032"):
    rows = [r for r in recs if r.get(K_CODE) == code]
    quarters = sorted({r[K_Q] for r in rows})
    buf.append("#" * 100)
    buf.append(f"{code}  quarters={quarters}")
    # item -> label
    labels = {}
    for r in rows:
        labels.setdefault(r[K_NO], r.get(K_ITEM))
    items = sorted(labels)
    buf.append(f"items present: {items}")
    for n in items:
        buf.append(f"  item{n}: {labels[n]}")
    buf.append("")
    # matrix for items of interest
    focus = [1,2,3,4,12,13,14,19,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54]
    hdr = f"{'Q':<10}" + "".join(f"{('i'+str(n)):>14}" for n in focus)
    buf.append("[값] " + hdr)
    for q in quarters:
        d = {r[K_NO]: r.get(K_V) for r in rows if r[K_Q] == q}
        line = f"{q:<10}" + "".join(f"{(str(d.get(n)) if d.get(n) is not None else '-'):>14}" for n in focus)
        buf.append("     " + line)
    buf.append("")
    buf.append("[값_적용후] " + hdr)
    for q in quarters:
        d = {r[K_NO]: r.get(K_VA) for r in rows if r[K_Q] == q}
        line = f"{q:<10}" + "".join(f"{(str(d.get(n)) if d.get(n) is not None else '-'):>14}" for n in focus)
        buf.append("     " + line)
    buf.append("")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT)
