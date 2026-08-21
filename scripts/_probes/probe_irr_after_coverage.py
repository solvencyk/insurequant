"""items 41-46(금리위험 순자산가치 6시나리오) 적용후 커버리지: 원천 부재인가 추출 갭인가."""
import io, json, sys
from collections import defaultdict, Counter
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
IRR = list(range(41, 47))
stat = Counter(); same = Counter(); diff_cells = []
for (c, q), m in sorted(d.items()):
    have_pre = [i for i in IRR if m.get(i, (None, None))[0] is not None]
    have_post = [i for i in IRR if m.get(i, (None, None))[1] is not None]
    grp = "적용사" if c in APPLIERS else "비적용사"
    if not have_pre:
        stat[f"{grp}: 41-46 전 자체 없음(1Q/3Q 간이공시 등)"] += 1
        continue
    if not have_post:
        stat[f"{grp}: 전 있음·후 전무"] += 1
        continue
    if len(have_post) < len(have_pre):
        stat[f"{grp}: 후 부분"] += 1
        continue
    eq = all(abs(m[i][0] - m[i][1]) < 0.005 for i in have_pre)
    stat[f"{grp}: 후 완비 · 전=후" if eq else f"{grp}: 후 완비 · 전≠후"] += 1
    if not eq:
        diff_cells.append((c, name.get(c,c), q, [(i, m[i]) for i in have_pre
                                                 if abs(m[i][0]-m[i][1]) >= 0.005][:3]))
for k, v in sorted(stat.items()):
    print(f"  {k}: {v}")
print(f"\n전≠후 인 (회사,분기) = {len(diff_cells)}")
for c, nm, q, ex in diff_cells[:10]:
    print(f"   {c} {nm} {q}: {ex}")
