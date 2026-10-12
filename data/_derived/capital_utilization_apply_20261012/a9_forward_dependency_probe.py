"""a9: does kics_forward_capital.json depend on the redefined utilization numbers? (read-only probe)

forward_capital_simulation.py reads output/tier{1,2}_utilization/*_20262Q.json ONLY inside compute_confidence()
(T1: tier1_hybrid_issued_eok; T2: subordinated_eok / numerator_eok fallback / utilization_pct > 100 / data_source /
quality_flag). This probe imports the builder's own functions (no re-typing) with the arguments of the last run
(manifest 20261010T213235Z) and, for every row of the deployed kics_forward_capital.json:
  (1) recomputes `confidence` with the tier rows as committed in HEAD   -> must equal the deployed block (sanity)
  (2) recomputes `confidence` with the newly written tier rows          -> the dependency, field by field
  (3) recomputes the projection with today's inputs                     -> would a full re-run change more than (2)?
Writes nothing except a9_forward_dependency_probe.txt / .json in this folder.

Run (repo root):
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_utilization_apply_20261012/a9_forward_dependency_probe.py
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.argv = [sys.argv[0], "--baseline-quarter", "2026.2Q", "--tier-quarter", "2026.2Q",
            "--bonds-source", "data/bonds/capital_securities_fy2026h1.json"]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
import forward_capital_simulation as F  # noqa: E402  (module parses sys.argv at import)


def head_json(rel):
    raw = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=REPO, capture_output=True, check=True).stdout
    return json.loads(raw.decode("utf-8"))


def by_code(doc):
    return {r["code"]: r for r in doc.get("results", [])}


def main() -> int:
    deployed = json.loads((REPO / "kics_forward_capital.json").read_text(encoding="utf-8"))
    old_t1 = by_code(head_json("output/tier1_utilization/tier1_utilization_20262Q.json"))
    old_t2 = by_code(head_json("output/tier2_utilization/tier2_utilization_20262Q.json"))
    new_t1 = by_code(json.loads((REPO / "output/tier1_utilization/tier1_utilization_20262Q.json").read_text(encoding="utf-8")))
    new_t2 = by_code(json.loads((REPO / "output/tier2_utilization/tier2_utilization_20262Q.json").read_text(encoding="utf-8")))
    bonds_per, _src = F.load_outstanding_bonds()
    baselines = F.load_kics_baselines()
    out, sanity_bad, conf_changes, proj_changes = [], [], [], []
    for row in deployed:
        code = row.get("insurer_code")
        if row.get("status") == "excluded" or "confidence" not in row:
            continue
        bonds = bonds_per.get(code, [])
        cov = F._bond_coverage(code, bonds, bonds_per)
        c_old = F.compute_confidence(code, bonds, old_t1, old_t2, bond_coverage=cov)
        c_new = F.compute_confidence(code, bonds, new_t1, new_t2, bond_coverage=cov)
        if c_old != row["confidence"]:
            sanity_bad.append(code)
        diff = {k: (c_old.get(k), c_new.get(k)) for k in set(c_old) | set(c_new) if c_old.get(k) != c_new.get(k)}
        if diff:
            conf_changes.append((code, row.get("insurer_name"), diff))
        if row.get("status") == "ok" and baselines.get(code):
            sim = F.simulate_one(code, baselines[code], bonds)
            keys = [k for k in sim if k not in ("confidence", "bond_coverage")]
            pd = [k for k in keys if sim.get(k) != row.get(k)]
            if pd:
                proj_changes.append((code, row.get("insurer_name"), pd))
    out.append(f"rows={len(deployed)} · sanity(HEAD tier rows reproduce deployed confidence): "
               f"{'OK' if not sanity_bad else 'FAIL ' + str(sanity_bad)}")
    out.append(f"confidence changes with the new tier rows: {len(conf_changes)} rows")
    for code, name, diff in conf_changes:
        out.append(f"  {code} {name}: " + "; ".join(f"{k}: {a!r} -> {b!r}" for k, (a, b) in sorted(diff.items())))
    out.append(f"projection fields that a FULL re-run would also change (inputs moved since 20261010T213235Z): "
               f"{len(proj_changes)} rows")
    for code, name, keys in proj_changes:
        out.append(f"  {code} {name}: {keys}")
    txt = "\n".join(out) + "\n"
    (HERE / "a9_forward_dependency_probe.txt").write_text(txt, encoding="utf-8")
    (HERE / "a9_forward_dependency_probe.json").write_text(json.dumps({
        "sanity_fail": sanity_bad,
        "confidence_changes": [{"code": c, "name": n, "diff": {k: list(v) for k, v in d.items()}} for c, n, d in conf_changes],
        "projection_changes_if_full_rerun": [{"code": c, "name": n, "fields": k} for c, n, k in proj_changes],
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
