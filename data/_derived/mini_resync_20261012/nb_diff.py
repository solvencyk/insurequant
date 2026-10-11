# -*- coding: utf-8 -*-
"""Diff NB_CSM_multiple.json before/after the rebuild (key = code+quarter)."""
import json
from pathlib import Path

D = Path(__file__).resolve().parent
ROOT = D.parents[2]
before = json.loads((D / "NB_CSM_multiple.before.json").read_text(encoding="utf-8"))
after = json.loads((ROOT / "NB_CSM_multiple.json").read_text(encoding="utf-8"))
kb = {(r["원보험사코드"], r["공시분기"]): r for r in before}
ka = {(r["원보험사코드"], r["공시분기"]): r for r in after}
print("before rows", len(before), "after rows", len(after))
added = sorted(set(ka) - set(kb))
removed = sorted(set(kb) - set(ka))
print("removed", removed)
print("added", len(added))
for k in added:
    r = ka[k]
    print("  +", k, {c: r[c] for c in r if c not in ("원보험사코드", "원수사명", "티커", "생손보여부", "공시분기")})
changed = []
for k in sorted(set(kb) & set(ka)):
    if kb[k] != ka[k]:
        diff = {c: (kb[k].get(c), ka[k].get(c)) for c in set(kb[k]) | set(ka[k]) if kb[k].get(c) != ka[k].get(c)}
        changed.append((k, diff))
print("changed existing", len(changed))
for k, d in changed:
    print("  ~", k, ka[k]["원수사명"], d)
lina = [r for r in after if r["원보험사코드"] == "KR0074"]
print("Lina rows", len(lina))
for r in sorted(lina, key=lambda r: (int(r["공시분기"][:4]), r["공시분기"][5])):
    print("  ", r["공시분기"], r["신계약CSM_연누계"], r["월납월초보험료_연누계"], r["신계약CSM배수_연누계"], "|", r["신계약CSM_당분기"], r["월납월초보험료_당분기"], r["신계약CSM배수_당분기"])
rein = [r for r in after if r["원보험사코드"].startswith("KR11")]
print("reinsurer rows", len(rein), "with non-null multiple:", sum(1 for r in rein if r["신계약CSM배수_연누계"] is not None or r["신계약CSM배수_당분기"] is not None))
