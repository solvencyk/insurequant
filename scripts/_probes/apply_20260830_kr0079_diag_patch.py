# -*- coding: utf-8 -*-
"""Surgically patch data/dart/viz/csm_waterfall_master_diag.json: update ONLY the
50 (KR0079, quarter, item) cells that change between the PREFIX and POSTFIX
waterfall_for_dir() sweeps (scripts/_probes/_out_20260830_sweep_{PREFIX,POSTFIX}.json)
to the POSTFIX (fixed) value. Mirrors commit 9a067dd's proven pattern: never re-run
build_csm_waterfall_master.py's main() wholesale; patch the diag artefact directly
from a read-only full-population sweep, so every OTHER company/quarter/row in the
diag file stays byte-identical. Asserts exactly the expected N cells are touched.
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

pre = json.loads((ROOT / "scripts/_probes/_out_20260830_sweep_PREFIX.json").read_text(encoding="utf-8"))
post = json.loads((ROOT / "scripts/_probes/_out_20260830_sweep_POSTFIX.json").read_text(encoding="utf-8"))

# Build the exact patch list: (kr, quarter, item) -> new_value, restricted to KR0079
# (the diff sweep already proved zero other companies move).
patch = {}
for key in pre:
    kr, q = key.split("|")
    pv = (pre[key].get("vals") or {})
    qv = (post[key].get("vals") or {})
    for it in range(1, 7):
        a, b = pv.get(str(it)), qv.get(str(it))
        if a != b:
            assert kr == "KR0079", f"unexpected company touched: {kr} {q} item{it}"
            patch[(kr, q, it)] = b

print(f"patch cells: {len(patch)}")

DIAG = ROOT / "data/dart/viz/csm_waterfall_master_diag.json"
rows = json.loads(DIAG.read_text(encoding="utf-8"))

applied = set()
for r in rows:
    k = (r["원보험사코드"], r["공시분기"], r["항목번호"])
    if k in patch:
        old = r.get("값")
        new = patch[k]
        r["값"] = new
        applied.add(k)
        print(f"  {k}: {old} -> {new}")

missing = set(patch) - applied
if missing:
    raise SystemExit(f"FATAL: {len(missing)} patch cells had no matching diag row: {sorted(missing)}")
assert len(applied) == len(patch), f"applied {len(applied)} != patch {len(patch)}"

DIAG.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"wrote {DIAG} ({len(rows)} rows, {len(applied)} cells patched)")
