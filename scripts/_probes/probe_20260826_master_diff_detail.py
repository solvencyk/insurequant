#!/usr/bin/env python3
"""롱포맷 마스터 diff 상세 — 회사·분기·항목별 전/후."""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
KEY = ("원보험사코드", "항목번호", "공시분기")
def load(p):
    return {tuple(r[k] for k in KEY): r for r in json.loads(Path(p).read_text(encoding="utf-8"))}
a, b = load(sys.argv[1]), load(sys.argv[2])
nm = {}
for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
    nm.setdefault(r["원보험사코드"], r["원수사명"])
sk = lambda k: (str(k[0]), str(k[2]), str(k[1]))
for k in sorted(set(a) & set(b), key=sk):
    va, vb = a[k].get("값"), b[k].get("값")
    if va == vb or (isinstance(va, float) and isinstance(vb, float) and abs(va - vb) < 5e-4):
        continue
    f = lambda v: "-" if v is None else (f"{v:,.2f}" if isinstance(v, float) else str(v))
    d = "" if not (isinstance(va, float) and isinstance(vb, float)) else f"  Δ{vb-va:+,.2f}"
    print(f"{nm.get(k[0], k[0])[:14]:14s} {k[2]:8s} item{str(k[1]):>4s} "
          f"{a[k].get('항목명','')[:12]:12s} {f(va):>14s} -> {f(vb):>14s}{d}")
