# -*- coding: utf-8 -*-
"""Read-only: full branch table for every remaining blocking RED, run with the
gate's own side-inputs. 2026-08-22 validation iter-5. Modifies nothing."""
import io
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from solvency.validation.kics_json_rules import run_validation  # noqa: E402
from validate_kics_disclosure import (  # noqa: E402
    _load_tfi_applicability, _scan_breakdown_presence,
)

records = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
report = run_validation(records,
                        source_has_breakdown=_scan_breakdown_presence(records),
                        tfi_applicability=_load_tfi_applicability())
findings = report["findings"]

# raw cell lookup so we can classify by the actual numbers
cells = defaultdict(dict)
for r in records:
    c, q, it = r.get("원보험사코드"), r.get("공시분기"), r.get("항목번호")
    try:
        it = int(it)
    except (TypeError, ValueError):
        continue

    def num(x):
        if x in (None, ""):
            return None
        try:
            return float(str(x).replace(",", ""))
        except ValueError:
            return None
    if c and q:
        cells[(c, q)][it] = (num(r.get("값")), num(r.get("값_적용후")))

reds = [f for f in findings if f.get("status") == "RED"]
print(f"TOTAL RED = {len(reds)}")
print(Counter(f["rule"] for f in reds).most_common())
print()

for rule in sorted({f["rule"] for f in reds}):
    rs = [f for f in reds if f["rule"] == rule]
    print(f"=== {rule}  ({len(rs)}) ===")
    for f in sorted(rs, key=lambda x: (x.get("원보험사코드", ""), x.get("공시분기", ""))):
        c, q = f.get("원보험사코드"), f.get("공시분기")
        m = cells.get((c, q), {})

        def g(i, post=False):
            v = m.get(i)
            return None if v is None else v[1 if post else 0]
        extra = ""
        if rule.startswith("2_tier1_bridge"):
            extra = (f" item2={g(2)} item50전={g(50)} "
                     f"|d(2,50)|={None if (g(2) is None or g(50) is None) else round(abs(g(2)-g(50)), 2)}"
                     f" item4={g(4)} item12={g(12)} item13={g(13)}")
        elif rule.startswith("3_tier2_composition"):
            i3, i51 = g(3), g(51)
            extra = (f" item3={i3} item51={i51} "
                     f"|d(3,51)|={None if (i3 is None or i51 is None) else round(abs(i3-i51), 2)}"
                     f" 47={g(47)} 48={g(48)} 49={g(49)}")
        elif rule.startswith("51_tfi"):
            extra = f" item51={g(51)} 47={g(47)} 48={g(48)} 49={g(49)} item3={g(3)}"
        elif rule.startswith("50_tfi"):
            post = rule.endswith("_post")
            extra = (f" 50={g(50, post)} 51={g(51, post)} item1전={g(1)} item1후={g(1, True)}")
        print(f"  {c} {f.get('원수사명')} {q} diff={f.get('diff')}{extra}")
        print(f"      {str(f.get('detail'))[:230]}")
    print()
