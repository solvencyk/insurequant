# -*- coding: utf-8 -*-
"""Gate simulation for the reinsurer CSM_waterfall rows -- READ ONLY, no master is touched.

Loads the live data once (validate_data_contract.Env), runs the CSM-relevant checks of the data-contract gate and of
validate_master_tables on the live masters (baseline), then adds the staged reinsurer rows IN MEMORY and runs the same
checks again. The difference = what loading data/_derived/reinsurer_ifrs17_csm_20261011/rows_waterfall.json would change.

Variant B additionally adds (in memory) an empty PL bucket for every reinsurer quarter that has a waterfall row, to show
the other branch of the same cross-check (PL bucket exists but has no 원수CSM상각).

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20261011_reinsurer_csm_gate_sim.py
Writes data/_derived/reinsurer_ifrs17_csm_20261011/gate_sim_report.json
"""
from __future__ import annotations

import contextlib
import copy
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")

import validate_data_contract as V          # noqa: E402
import validate_master_tables as M          # noqa: E402

STAGE = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
CHECKS = ["check_artifact_readable", "check_csm_continuity", "check_census", "check_cross_source", "check_domain_identity"]


def run_checks(env):
    res = V.GateResult()
    for name in CHECKS:
        getattr(V, name)(res, env)
    return res


def sig(f):
    return (f.severity, f.master, f.rule, f.company, f.quarter)


def apply_wf(env, rows):
    """add staged rows to env.wf (keyed by 원수사명) and env.wf_by_code (keyed by code)"""
    for r in rows:
        nm = M.norm(r["항목명"])
        env.wf.setdefault((r["원수사명"], r["공시분기"]), {})[nm] = r["값"]
        env.wf_by_code.setdefault((r["원보험사코드"], r["공시분기"]), {})[nm] = r["값"]


def run_vmt(wf, pl):
    """validate_master_tables CSM sections (closing identity, coverage holes, plausibility, PL<->WF 상각 identity)"""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        ci_pass, ci_fail, ci_skip = M._check_closing_identity(wf)
        wf_holes, pl_holes = M._check_coverage(wf, pl)
        dup, spike, cont, wfy, zam = M._check_plausibility(wf)
        cc_pass, cc_fail, cc_pin, cc_skip = M._check_csm_crosscheck(pl, wf)
    return {"closing_pass": ci_pass, "closing_fail": len(ci_fail), "closing_skip": ci_skip, "wf_holes": len(wf_holes),
            "dup": len(dup), "spike": len(spike), "cont": len(cont), "wfy": len(wfy), "zamort": len(zam),
            "csm_amort_identity_fail": len(cc_fail), "csm_amort_identity_pass": cc_pass}


def main() -> int:
    rows = json.loads((STAGE / "rows_waterfall.json").read_text(encoding="utf-8"))
    t0 = time.time()
    vmt_base = run_vmt(M.load_long("CSM_waterfall.json"), M.load_long("PL_breakdown.json"))
    wf_sim = M.load_long("CSM_waterfall.json")
    for r in rows:
        wf_sim.setdefault((r["원수사명"], r["공시분기"]), {})[M.norm(r["항목명"])] = r["값"]
    vmt_sim = run_vmt(wf_sim, M.load_long("PL_breakdown.json"))
    print("validate_master_tables baseline:", vmt_base)
    print("validate_master_tables with WF rows:", vmt_sim)
    env = V.Env()
    print(f"Env loaded in {time.time() - t0:.0f}s; wf keys {len(env.wf)}, pl keys {len(env.pl)}")
    already = [k for k in env.wf if k[0] in {r['원수사명'] for r in rows}]
    print("reinsurer WF buckets already in live master:", len(already))

    base = run_checks(env)
    base_sigs = Counter(sig(f) for f in base.findings)
    print(f"baseline: RED={len(base.red)} YELLOW={len(base.yellow)}")

    # --- variant A: add the WF rows only (PL as on disk)
    envA = env
    apply_wf(envA, rows)
    resA = run_checks(envA)
    new_A = [f for f in resA.findings if sig(f) not in base_sigs]
    print(f"variant A (WF rows added, PL as on disk): RED={len(resA.red)} YELLOW={len(resA.yellow)} new findings {len(new_A)}")
    by_rule = Counter((f.severity, f.rule) for f in new_A)
    for k, v in sorted(by_rule.items()):
        print("   ", k, v)

    # --- variant B: + empty PL buckets for the same (company, quarter)
    for r in rows:
        envA.pl.setdefault((r["원수사명"], r["공시분기"]), {"보험손익": 0.0})
    resB = run_checks(envA)
    new_B = [f for f in resB.findings if sig(f) not in base_sigs]
    print(f"variant B (+ PL bucket without 원수CSM상각): RED={len(resB.red)} YELLOW={len(resB.yellow)} new findings {len(new_B)}")
    by_rule_b = Counter((f.severity, f.rule) for f in new_B)
    for k, v in sorted(by_rule_b.items()):
        print("   ", k, v)

    report = {
        "validate_master_tables": {"baseline": vmt_base, "with_wf_rows": vmt_sim},
        "baseline": {"red": len(base.red), "yellow": len(base.yellow)},
        "variant_A_new": [{"severity": f.severity, "master": f.master, "rule": f.rule, "company": f.company,
                           "quarter": f.quarter, "message": f.message[:300]} for f in new_A],
        "variant_B_new": [{"severity": f.severity, "master": f.master, "rule": f.rule, "company": f.company,
                           "quarter": f.quarter, "message": f.message[:300]} for f in new_B],
    }
    (STAGE / "gate_sim_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote", (STAGE / "gate_sim_report.json").relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
