"""Read-only PIN_STALE audit, corrected key mapping.

ledger  expected_residual = {"<rule>|적용전": <residual>, ...}
code    _TIER2_ISSUER_INCONSISTENT[(c,q)]["findings"][<rule>] = {"flag":..., "residual":...}
live    run_validation(...) RED finding diff for that (rule, c, q)

Also recomputes LIFE8 + IRR pins.  Nothing is written to disk.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402
from solvency.validation.kics_json_rules import (  # noqa: E402
    IRR_DERIVE_ISSUER_INCONSISTENT, run_validation,
)

LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"


def main():
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = {(e.get("registry"), e.get("company"), e.get("quarter")): e
               for e in led.get("entries") or []}
    records = V._load_records(ROOT / "kics_disclosure.json")
    report = run_validation(records,
                            source_has_breakdown=V._scan_breakdown_presence(records),
                            tfi_applicability=V._load_tfi_applicability())
    findings = report.get("findings", [])
    red_idx = {}
    for f in findings:
        if f.get("status") == "RED":
            red_idx.setdefault((str(f.get("rule")), f.get(V.KEY_CODE), f.get(V.KEY_QUARTER)),
                               []).append(f)
    print(f"live findings={len(findings)} red={sum(1 for f in findings if f.get('status') == 'RED')}")

    problems = []

    print("\n### TIER2 pin triangulation  (ledger | code | live)")
    for (c, q), spec in sorted(V._TIER2_ISSUER_INCONSISTENT.items()):
        e = entries.get(("_TIER2_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        code_find = spec.get("findings") or {}
        # ledger keys -> rule name
        lp_by_rule = {}
        for k, v in lp.items():
            rule = k.split("|")[0]
            col = k.split("|")[1] if "|" in k else "?"
            lp_by_rule[(rule, col)] = v
        for rule, pin in sorted(code_find.items()):
            pinned = pin.get("residual")
            col = "적용후" if rule.endswith("_post") else "적용전"
            lv = lp_by_rule.get((rule, col), "<<MISSING>>")
            hits = red_idx.get((rule, c, q)) or []
            live = hits[0].get("diff") if hits else None
            flags = []
            if lv == "<<MISSING>>":
                flags.append("LEDGER_KEY_MISSING")
            elif not (lv is None and pinned is None) and not (
                    isinstance(lv, (int, float)) and isinstance(pinned, (int, float))
                    and abs(lv - pinned) < 1e-6):
                flags.append("LEDGER_vs_CODE")
            if not hits:
                flags.append("NO_LIVE_RED(INERT)")
            elif pinned is not None and (live is None or abs(live - pinned) > 0.01):
                flags.append("CODE_vs_LIVE")
            mark = ("  <<< " + ",".join(flags)) if flags else ""
            print(f"  {c} {q} {rule:<28} ledger={str(lv):<12} code={str(pinned):<12} "
                  f"live={str(live):<12}{mark}")
            if flags:
                problems.append((c, q, rule, flags, lv, pinned, live))
        # ledger keys not present in code
        code_cols = {(r, "적용후" if r.endswith("_post") else "적용전") for r in code_find}
        for k in sorted(set(lp_by_rule) - code_cols):
            print(f"  {c} {q} {k[0]:<28} ledger-only key [{k[1]}] = {lp_by_rule[k]}  <<< ORPHAN_LEDGER_KEY")
            problems.append((c, q, k[0], ["ORPHAN_LEDGER_KEY"], lp_by_rule[k], None, None))

    print("\n### IRR pin triangulation")
    for (c, q), pins in sorted(IRR_DERIVE_ISSUER_INCONSISTENT.items()):
        e = entries.get(("IRR_DERIVE_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        print(f"  {c} {q}: code={pins}")
        print(f"           ledger={lp}")
        for k in sorted(set(pins) | set(lp)):
            a, b = pins.get(k), lp.get(k)
            same = (isinstance(a, (int, float)) and isinstance(b, (int, float))
                    and abs(a - b) < 1e-6)
            if not same:
                print(f"           {k}: code={a} ledger={b}  <<< MISMATCH")
                problems.append((c, q, "36_irr", ["LEDGER_vs_CODE"], b, a, None))

    print("\n### LIFE8 pin triangulation")
    for (c, q), pins in sorted(V._LIFE8_ISSUER_INCONSISTENT.items()):
        e = entries.get(("_LIFE8_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        hits = red_idx.get(("8_life", c, q)) or []
        live = hits[0].get("diff") if hits else None
        print(f"  {c} {q}: code={pins} ledger={lp} live_8life_diff={live}")

    print("\n### summary")
    print(f"  problem rows = {len(problems)}")
    for p in problems:
        print("   ", p)

    # cells pins (TIER2 only)
    print("\n### TIER2 cells pin vs master")
    byq = {}
    for r in records:
        c, q, it = r.get(V.KEY_CODE), r.get(V.KEY_QUARTER), r.get(V.KEY_ITEM)
        try:
            it = int(it)
        except (TypeError, ValueError):
            continue
        if c and q:
            def _n(v):
                try:
                    return float(str(v).replace(",", ""))
                except (TypeError, ValueError):
                    return None
            byq.setdefault((c, q), {})[it] = {V.KEY_VALUE: _n(r.get(V.KEY_VALUE)),
                                              V.KEY_VALUE_POST: _n(r.get(V.KEY_VALUE_POST))}
    bad = 0
    for (c, q), spec in sorted(V._TIER2_ISSUER_INCONSISTENT.items()):
        m = byq.get((c, q)) or {}
        for item, cols in sorted(spec["cells"].items()):
            for col, pinned in cols.items():
                actual = (m.get(item) or {}).get(col)
                if actual is None or abs(actual - pinned) > V._TIER2_PIN_TOL:
                    print(f"  DRIFT {c} {q} item{item} [{col}] pinned={pinned} actual={actual}")
                    bad += 1
    print(f"  cells drift = {bad}")


if __name__ == "__main__":
    main()
