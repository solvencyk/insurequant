"""a0: dump the current deployed tier1/tier2 utilization JSONs (read-only) - key census + per-company core fields.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a0_dump_current.py
Output: a0_current_dump.txt (same folder)
"""
from __future__ import annotations

import collections
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def main() -> int:
    out = []
    for name in ("kics_tier1_utilization.json", "kics_tier2_utilization.json"):
        doc = json.loads((REPO / name).read_text(encoding="utf-8"))
        out.append(f"== {name}  top-level keys={list(doc.keys())}  count={doc.get('count')} n_rows={len(doc['results'])}")
        if "definition" in doc:
            out.append("  definition=" + json.dumps(doc["definition"], ensure_ascii=False))
        kc = collections.Counter()
        for r in doc["results"]:
            kc[tuple(r.keys())] += 1
        for keys, n in kc.most_common():
            out.append(f"  keyset x{n}: {list(keys)}")
        for r in sorted(doc["results"], key=lambda x: x["code"]):
            if name.startswith("kics_tier1"):
                out.append(f"  {r['code']} {r['company'][:10]:10s} pct={r.get('utilization_pct')} strict={r.get('utilization_pct_strict')} "
                           f"issued={r.get('tier1_hybrid_issued_eok')} lim={r.get('tier1_hybrid_limit_eok')} qf={r.get('quality_flag')} "
                           f"src={r.get('data_source')} gf={r.get('tier1_grandfathered_hybrid_eok')} extra={ {k: r[k] for k in r if k in ('reinsurer_basis',)} }")
            else:
                out.append(f"  {r['code']} {r['company'][:10]:10s} pct={r.get('utilization_pct')} num={r.get('numerator_eok')} "
                           f"lim={r.get('tier2_limit_eok')} qf={r.get('quality_flag')} src={r.get('data_source')} "
                           f"t2={r.get('tier2_eok')} pre={r.get('pre_limit_eok')} lapse={r.get('lapse_excess_eok')} "
                           f"gfh={r.get('grandfathered_hybrid_eok')} gfs={r.get('grandfathered_subordinated_eok')} "
                           f"extra={ {k: r[k] for k in r if k in ('reinsurer_basis',)} }")
    txt = "\n".join(out) + "\n"
    (HERE / "a0_current_dump.txt").write_text(txt, encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
