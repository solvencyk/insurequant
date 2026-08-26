#!/usr/bin/env python3
"""basis 수정 전/후 전수 diff + CSM 상각 항등식 영향 판정."""
import sys, json
from collections import defaultdict, Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
base = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
new = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
uni = {r["원보험사코드"]: r["원수사명"] for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))}
wf = {(r["원보험사코드"], r["공시분기"]): r["값"]
      for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))
      if r["항목번호"] == 5}

diffs, err = [], []
for k in sorted(set(base) | set(new)):
    b, n = base.get(k, {}), new.get(k, {})
    if "_error" in b or "_error" in n:
        err.append((k, b.get("_error"), n.get("_error"))); continue
    for i in map(str, range(1, 25)):
        vb, vn = b.get(i), n.get(i)
        if vb == vn:
            continue
        if isinstance(vb, float) and isinstance(vn, float) and abs(vb - vn) < 5e-4:
            continue
        diffs.append((k, int(i), vb, vn))

print(f"버킷 base={len(base)} new={len(new)}  오류={len(err)}")
print(f"값이 바뀐 셀: {len(diffs)}")
by_cq = defaultdict(list)
for k, i, vb, vn in diffs:
    by_cq[k].append((i, vb, vn))
print(f"영향 company-quarter: {len(by_cq)}  회사수: {len({k.split('|')[0] for k in by_cq})}")
print()
print("항목별 변경 건수:", dict(sorted(Counter(i for _, i, _, _ in diffs).items())))
print()
print("=== 회사·분기별 (항목4=원수 CSM상각 중심) ===")
print(f"{'회사':16s} {'분기':8s} {'항목':>4s} {'전(억)':>12s} {'후(억)':>12s} {'워터폴상각':>11s} {'전잔차':>9s} {'후잔차':>9s}")
rows = []
for k in sorted(by_cq, key=lambda x: (uni.get(x.split('|')[0], x), x)):
    code, q = k.split("|")
    nm = uni.get(code, code)
    for i, vb, vn in sorted(by_cq[k]):
        w = wf.get((code, q))
        f = lambda v: "-" if not isinstance(v, (int, float)) else f"{v/100:,.2f}"
        if i == 4 and w is not None:
            db = "-" if not isinstance(vb, (int, float)) else f"{vb/100-abs(w):+,.2f}"
            dn = "-" if not isinstance(vn, (int, float)) else f"{vn/100-abs(w):+,.2f}"
            wtxt = f"{abs(w):,.2f}"
        else:
            db = dn = wtxt = ""
        print(f"{nm[:16]:16s} {q:8s} {i:>4d} {f(vb):>12s} {f(vn):>12s} {wtxt:>11s} {db:>9s} {dn:>9s}")
        rows.append((nm, q, i, vb, vn))
if err:
    print("\n오류 버킷:", err[:10])
