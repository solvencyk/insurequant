#!/usr/bin/env python3
"""롱포맷 마스터 2개(전/후) 셀단위 diff — 행 손실 · 값 변경 · null 전환을 따로 센다."""
import sys, json
from collections import Counter, defaultdict
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
KEY = ("원보험사코드", "항목번호", "공시분기")

def load(p):
    rows = json.loads(Path(p).read_text(encoding="utf-8"))
    return {tuple(r[k] for k in KEY): r for r in rows}, len(rows)

a, na = load(sys.argv[1])
b, nb = load(sys.argv[2])
label = sys.argv[3] if len(sys.argv) > 3 else ""
sk = lambda k: (str(k[0]), str(k[1]), str(k[2]))
lost = sorted(set(a) - set(b), key=sk)
gained = sorted(set(b) - set(a), key=sk)
chg, nulled, filled = [], [], []
for k in sorted(set(a) & set(b), key=sk):
    va, vb = a[k].get("값"), b[k].get("값")
    if va == vb:
        continue
    if isinstance(va, float) and isinstance(vb, float) and abs(va - vb) < 5e-4:
        continue
    if vb is None:
        nulled.append((k, va))
    elif va is None:
        filled.append((k, vb))
    else:
        chg.append((k, va, vb))
print(f"### {label}  행 {na} -> {nb}")
print(f"  키 손실 {len(lost)}  키 신규 {len(gained)}  값변경 {len(chg)}  값->null {len(nulled)}  null->값 {len(filled)}")
if lost:
    print("  손실 예시:", lost[:8])
if nulled:
    print("  null 전환:", [(k, round(v, 1) if isinstance(v, float) else v) for k, v in nulled[:12]])
cq = defaultdict(list)
for k, va, vb in chg:
    cq[(k[0], k[2])].append((k[1], va, vb))
for k, v in filled:
    cq[(k[0], k[2])].append((k[1], None, v))
print(f"  영향 company-quarter {len(cq)}  회사 {len({c for c,_ in cq})}")
print("  항목별:", dict(sorted(Counter(k[1] for k, _, _ in chg).items())))
