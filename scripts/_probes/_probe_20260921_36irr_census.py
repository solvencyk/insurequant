"""36_irr coverage census — every (company, quarter) bucket, what the rule engine actually did.

Read-only. Answers inbox/validation/20260921T0215Z (KR0094 2025.4Q / 2026.2Q "36_irr not RED").

For each bucket prints: item36 present? 41-46 complete? even quarter? the 36_irr finding status
and its branch (pinned-SKIP / tol-GREEN / RED / cadence-SKIP ...), plus the independently
recomputed residual item36 - derive(41-46) so the engine's verdict can be checked against
the arithmetic, not against itself.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_probe_20260921_36irr_census.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import validate_kics_disclosure as vkd  # noqa: E402
from src.solvency.validation.kics_json_rules import (  # noqa: E402
    IRR_DERIVE_ISSUER_INCONSISTENT,
    IRR_DERIVED_TOL_REL,
    IRR_SCENARIO_ITEMS,
    _group_records,
    irr_derive_expected,
    run_validation,
)

OUT = ROOT / "data" / "_derived" / "_probe_20260921_36irr_census.json"


def _branch(detail: str) -> str:
    d = detail or ""
    if "잔차 박제" in d or "documented exception (owner 2026-08-21" in d:
        return "PINNED_SKIP"
    if "IRR_EXEMPTION_RESIDUAL_DRIFT" in d:
        return "PIN_DRIFT_RED"
    if "IRR_EXEMPTION_INPUT_MISSING" in d:
        return "PIN_INPUT_MISSING_RED"
    if "internal-model" in d:
        return "INTERNAL_MODEL_SKIP"
    if "scenario table 41-46 missing/incomplete" in d:
        return "EVENQ_SCENARIO_MISSING_RED"
    if "item36 absent, or odd quarter" in d:
        return "CADENCE_OR_ABSENT_SKIP"
    return "NUMERIC_CHECK"


def main() -> int:
    src = ROOT / "kics_disclosure.json"
    records = vkd._load_records(src)
    report = run_validation(
        records,
        source_has_breakdown=vkd._scan_breakdown_presence(records),
        tfi_applicability=vkd._load_tfi_applicability(),
        life_subrisk_applicability=vkd._load_life_subrisk_applicability(),
        life_subrisk_source_absent=vkd._load_life_subrisk_source_absent(),
    )
    buckets = _group_records(records)
    findings = [f for f in report["findings"] if f.get("rule") == "36_irr"]
    by_cq: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for f in findings:
        by_cq[(f["원보험사코드"], f["공시분기"])].append(f)

    rows = []
    for b in buckets:
        cq = (b.code, b.quarter)
        vals = {i: b.get(i) for i in (36, *IRR_SCENARIO_ITEMS)}
        complete = all(vals[i] is not None for i in IRR_SCENARIO_ITEMS)
        derive = irr_derive_expected(vals) if complete else None
        resid = (float(vals[36]) - derive) if (derive is not None and vals[36] is not None) else None
        rel = (resid / float(vals[36])) if (resid is not None and vals[36]) else None
        fs = by_cq.get(cq, [])
        st = fs[0]["status"] if fs else "NO_FINDING"
        br = _branch(fs[0].get("detail", "")) if fs else "NOT_EVALUATED"
        if br == "NUMERIC_CHECK" and st in ("GREEN", "YELLOW", "RED"):
            br = f"NUMERIC_{st}"
        rows.append({
            "code": b.code, "name": b.name, "quarter": b.quarter,
            "even_q": b.quarter.endswith(("2Q", "4Q")),
            "item36": vals[36], "scen_complete": complete,
            "n_scen_present": sum(vals[i] is not None for i in IRR_SCENARIO_ITEMS),
            "derive": derive, "resid": resid, "rel": rel,
            "beyond_tol": (abs(resid) > max(2.0, IRR_DERIVED_TOL_REL * abs(derive))) if resid is not None else None,
            "n_findings": len(fs), "status": st, "branch": br,
            "pinned": cq in IRR_DERIVE_ISSUER_INCONSISTENT,
        })

    n_b = len(buckets)
    multi = [r for r in rows if r["n_findings"] != 1]
    print(f"buckets={n_b}  36_irr findings={len(findings)}  buckets with !=1 finding={len(multi)}")
    print("status x branch:")
    for (st, br), n in sorted(Counter((r["status"], r["branch"]) for r in rows).items()):
        print(f"  {st:6s} {br:28s} {n}")

    # The blind-spot question: any bucket where the arithmetic is beyond tol but the engine is not RED?
    print("\n[beyond-tol, not RED] — every one must be a pinned documented exception:")
    bad = []
    for r in rows:
        if r["beyond_tol"] and r["status"] != "RED":
            bad.append(r)
            print(f"  {r['code']} {r['quarter']:8s} item36={r['item36']:>10.2f} derive={r['derive']:>10.2f} "
                  f"resid={r['resid']:+.4f} rel={r['rel']:+.2%} status={r['status']} branch={r['branch']} pinned={r['pinned']}")
    unpinned_bad = [r for r in bad if not r["pinned"]]
    print(f"  -> beyond-tol non-RED = {len(bad)}, of which NOT pinned = {len(unpinned_bad)}  (must be 0)")

    print("\n[pinned entries] engine verdict per pin:")
    for cq in sorted(IRR_DERIVE_ISSUER_INCONSISTENT):
        r = next((x for x in rows if (x["code"], x["quarter"]) == cq), None)
        if r is None:
            print(f"  {cq} -> NO BUCKET")
            continue
        print(f"  {cq[0]} {cq[1]:8s} status={r['status']} branch={r['branch']} resid={r['resid']:+.4f} "
              f"pin={IRR_DERIVE_ISSUER_INCONSISTENT[cq]['적용전']:+.4f} rel={r['rel']:+.2%}")

    print("\n[KR0094 all quarters]:")
    for r in rows:
        if r["code"] == "KR0094":
            d = f"{r['derive']:.2f}" if r["derive"] is not None else "-"
            rs = f"{r['resid']:+.4f}" if r["resid"] is not None else "-"
            print(f"  {r['quarter']:8s} item36={r['item36']} scen={r['n_scen_present']}/6 derive={d} resid={rs} "
                  f"status={r['status']} branch={r['branch']}")

    # Ticket claim: "36_irr x 2026.2Q findings = 0 in latest report"
    q = "2026.2Q"
    q_rows = [r for r in rows if r["quarter"] == q]
    print(f"\n[{q}] buckets={len(q_rows)} findings={sum(r['n_findings'] for r in q_rows)} "
          f"status={dict(Counter(r['status'] for r in q_rows))} "
          f"scen_complete={sum(r['scen_complete'] for r in q_rows)} beyond_tol={sum(bool(r['beyond_tol']) for r in q_rows)}")
    latest = ROOT / "artifacts" / "kics_validation" / "report_latest.json"
    if latest.exists():
        rep = json.loads(latest.read_text(encoding="utf-8"))
        lf = [f for f in rep.get("findings", []) if f.get("rule") == "36_irr" and f.get("공시분기") == q]
        print(f"  report_latest.json ({rep.get('generated_at')}): 36_irr x {q} findings = {len(lf)} "
              f"status={dict(Counter(f['status'] for f in lf))}")

    OUT.write_text(json.dumps({
        "buckets": n_b, "findings_36irr": len(findings),
        "status_branch": {f"{k[0]}|{k[1]}": v for k, v in Counter((r["status"], r["branch"]) for r in rows).items()},
        "beyond_tol_not_red": bad, "beyond_tol_not_red_unpinned": unpinned_bad,
        "rows": rows,
    }, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print(f"\nwrote {OUT}")
    return 0 if not unpinned_bad else 2


if __name__ == "__main__":
    raise SystemExit(main())
