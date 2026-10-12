"""Read-only: strict CSM closure (WFY / CONT / SPIKE / ZAMORT, no exemption sets) of the company chain when ONLY the given CSM blocks are replaced by the latest comparative vector.
usage: python s84_joint_feasibility.py KR0008|2023.1Q KR0008|2023.2Q KR0008|2023.3Q   (blocks of ONE company; run once per company)"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lib_dryrun as D  # noqa: E402

ov = json.loads((HERE / "cand" / "csm_adopt_overlay.json").read_text(encoding="utf-8"))
allt = json.loads((HERE / "cand" / "CSM_waterfall.ALLTRUSTED.json").read_text(encoding="utf-8"))
chain0 = D.csm_chain(D.load_json("CSM_waterfall.json"))
blocks = {}
for key in sys.argv[1:]:
    kr, q = key.split("|")
    v = ov.get(key)
    if v is None:                                         # fall back to the ALLTRUSTED candidate (gold-released pool)
        v = {str(r["항목번호"]): r["값"] for r in allt if r["원보험사코드"] == kr and r["공시분기"] == q}
    blocks[(kr, q)] = {int(k): x for k, x in v.items()}
cos = {k for k, _ in blocks}
for co in sorted(cos):
    base = D.strict_violations(chain0[co])
    ch = {q: dict(m) for q, m in chain0[co].items()}
    for (kr, q), v in blocks.items():
        if kr == co:
            for k, x in v.items():
                if x is not None:
                    ch[q][k] = x
    new = D.strict_violations(ch)
    print(co, "baseline:", D.fmt_viol(base) or "(none)")
    print(co, "after   :", D.fmt_viol(new) or "(none)")
    print(co, "created_or_worse:", D.created_or_worse(base, new), "| resolved:", len(D.resolved(base, new)))
