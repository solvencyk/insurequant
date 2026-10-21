"""Read-only: KR0073 rows of the builder's fresh diag source (csm_waterfall_master_diag.json) next to the live master."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
with open(ROOT / "data/dart/viz/csm_waterfall_master_diag.json", "r", encoding="utf-8") as f:
    diag = json.load(f)
with open(ROOT / "CSM_waterfall.json", "r", encoding="utf-8") as f:
    master = json.load(f)
print("diag rows:", len(diag), "keys:", list(diag[0].keys()))
QORD = lambda q: int(q[:4]) * 10 + int(q[5])


def vec(rows):
    d = {}
    for r in rows:
        if r.get("원보험사코드") != "KR0073":
            continue
        d.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
    return d


dv, mv = vec(diag), vec(master)
print(f"{'quarter':8s} | diag I1..I6 | master I1..I6 | equal?")
for q in sorted(set(dv) | set(mv), key=QORD):
    a = [dv.get(q, {}).get(i) for i in range(1, 7)]
    b = [mv.get(q, {}).get(i) for i in range(1, 7)]
    eq = ["=" if (x == y) else "!" for x, y in zip(a, b)]
    print(f"{q:8s} | {a} | {b} | {''.join(eq)}")
extra = sorted({k for r in diag if r.get("원보험사코드") == "KR0073" for k in r.keys()} - {"원보험사코드", "원수사명", "티커", "생손보여부", "항목번호", "항목명", "공시분기", "값"})
print("extra keys on KR0073 diag rows:", extra)
