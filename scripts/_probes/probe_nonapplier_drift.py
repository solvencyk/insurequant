"""비적용사인데 요구자본측(15-26, 29-46) 적용후 != 적용전 인 셀 — 선택경과조치가 없으므로 전부 오염."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
rows = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
APPLIERS = frozenset({"KR0070","KR0071","KR0072","KR0073","KR0076","KR0082","KR0083",
                      "KR0097","KR0100","KR1010","KR1011","KR0104","KR0049","KR0002",
                      "KR0003","KR0004","KR0005","KR0032"})
def num(v):
    try: return float(str(v).replace(",", ""))
    except (TypeError, ValueError): return None
d = defaultdict(dict); name = {}
for r in rows:
    c, q = r["원보험사코드"], r["공시분기"]; name[c] = r.get("원수사명", c)
    try: d[(c, q)][int(r["항목번호"])] = (num(r.get("값")), num(r.get("값_적용후")))
    except (TypeError, ValueError, KeyError): pass
ITEMS = list(range(15, 27)) + list(range(29, 47))
tot = 0
for (c, q), m in sorted(d.items()):
    if c in APPLIERS: continue
    bad = []
    for it in ITEMS:
        pre, post = m.get(it, (None, None))
        if pre is None or post is None: continue
        if abs(pre - post) > max(0.005, 0.0005 * abs(pre)):
            bad.append((it, pre, post))
    if bad:
        tot += len(bad)
        print(f"{c} {name.get(c,c)} {q}: {len(bad)}셀")
        for it, pre, post in bad:
            print(f"    item{it:>2}  전={pre!s:>12}  후={post!s:>12}")
print(f"\n총 {tot}셀")
