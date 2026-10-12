"""s6a_cell_coverage.py -- step 6a (READ-ONLY).  Per-cell rule coverage of every cell a latest-prior-column overlay would change.

Method = the project's own mutation method (tests/test_rule_coverage_manifest.py): perturb ONE cell (x1.5 + 1234) of the live master in memory, run the
rule engine (0.09 s), and see whether ANY finding (status / expected / actual / diff) moves.  If none moves, no engine rule reads that cell for that
bucket -> "rule blind spot" for the engine.  Cells the engine cannot see are listed separately: the full gate has additional axes (items 24-26 via
other_capital_children_sum, the 적용후 mirrors of R1/R2/R5/R6/mmult/irr) -- those are probed with the real gate only when the engine is blind.
Output: cell_coverage.json  {"<code>|<q>|<item>|<field>": {"engine_covered": bool, "n_findings_moved": int, "rules": [..]}}
"""
import copy
import sys
from collections import Counter

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402
import validate_kics_disclosure as vkd  # noqa: E402
from solvency.validation.kics_json_rules import run_validation  # noqa: E402

utf8_stdout()
rows = read_rows()
tfi = vkd._load_tfi_applicability()
life_app = vkd._load_life_subrisk_applicability()
life_abs = vkd._load_life_subrisk_source_absent()


def findings(rs):
    r = run_validation(rs, tfi_applicability=tfi)
    fs = r["findings"] if isinstance(r, dict) else r
    return {(f["원보험사코드"], f["공시분기"], str(f["rule"])): (f["status"], f.get("expected"), f.get("actual"), f.get("diff")) for f in fs}


base = findings(rows)
idx = {}
for i, r in enumerate(rows):
    idx[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = i

cells = set()
for p in sorted((OUT / "plans").glob("*.json")):
    plan = read_json(p)
    for e in plan["edits"]:
        cells.add((e["code"], e["q"], e["item"], e["field"]))

out = {}
for (c, q, it, fld) in sorted(cells):
    j = idx[(c, q, it)]
    old = rows[j].get(fld)
    v = num(old)
    if v is None:
        out[f"{c}|{q}|{it}|{fld}"] = {"engine_covered": False, "n_findings_moved": 0, "rules": [], "note": "cell empty"}
        continue
    rows[j][fld] = str(v * 1.5 + 1234.0)
    try:
        after = findings(rows)
    finally:
        rows[j][fld] = old
    moved = []
    for k in set(base) | set(after):
        b, a = base.get(k), after.get(k)
        if b != a:
            if b and a and b[0] == a[0] and all((x == y) or (isinstance(x, (int, float)) and isinstance(y, (int, float)) and abs(x - y) < 1e-6) for x, y in zip(b[1:], a[1:])):
                continue
            moved.append(k)
    out[f"{c}|{q}|{it}|{fld}"] = {"engine_covered": bool(moved), "n_findings_moved": len(moved),
                                  "rules": sorted({k[2] for k in moved if (k[0], k[1]) == (c, q)})[:12],
                                  "rules_other_buckets": sorted({f"{k[1]}:{k[2]}" for k in moved if (k[0], k[1]) != (c, q)})[:6]}
write_json_lf(OUT / "cell_coverage.json", out)
cov = Counter(v["engine_covered"] for v in out.values())
print("cells tested:", len(out), "engine-covered:", cov[True], "engine-blind:", cov[False])
blind_by_item = Counter((k.split("|")[2], k.split("|")[3]) for k, v in out.items() if not v["engine_covered"])
print("engine-blind by (item, field):", dict(blind_by_item))
