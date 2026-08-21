"""All applier (company,quarter) with item22/23 적용후 missing while 적용전 row exists."""
import io, json, sys
from collections import defaultdict
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
APPLIERS = frozenset({"KR0070","KR0071","KR0072","KR0073","KR0076","KR0082","KR0083",
                      "KR0097","KR0100","KR1010","KR1011","KR0104","KR0049","KR0002",
                      "KR0003","KR0004","KR0005","KR0032"})
d = defaultdict(dict); name = {}
for r in rows:
    c, q = r.get("원보험사코드"), r.get("공시분기"); name[c] = r.get("원수사명", c)
    try: d[(c, q)][int(r["항목번호"])] = r
    except (TypeError, ValueError, KeyError): pass
def key(cq): 
    y, qq = cq[1].split("."); return (cq[0], int(y), int(qq[0]))
miss = []
for cq in sorted(d, key=key):
    c, q = cq
    if c not in APPLIERS: continue
    m = d[cq]
    gone = [n for n in (22, 23) if n in m and m[n].get("값_적용후") in (None, "")]
    if gone:
        miss.append((c, q, gone, m[15].get("값_적용후") if 15 in m else None))
print(f"# applier 셀 중 item22/23 적용후 결측 = {len(miss)} (회사,분기)")
for c, q, gone, p15 in miss:
    print(f"   {c} {name.get(c,c)} {q}: {gone}   (item15후={p15})")
