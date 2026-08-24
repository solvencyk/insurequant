"""Read-only ledger-quality audit for the 26 live exemption cells.

For each live (registry, company, quarter):
  - which keys the ledger entry carries
  - whether verify markers actually ran this execution (_verify_markers_ran)
  - whether the markers pin a page range or scan the whole document
  - whether the CODE-side registry carries a residual/cell pin, and whether the
    ledger's expected_residual agrees with the code pin and with live rule output
Nothing is written.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

import validate_kics_disclosure as V  # noqa: E402
from solvency.validation.kics_json_rules import IRR_DERIVE_ISSUER_INCONSISTENT  # noqa: E402

LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"


def main():
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = {(e.get("registry"), e.get("company"), e.get("quarter")): e
               for e in led.get("entries") or []}
    regs = V._exemption_registries()
    recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

    # live pins from code
    code_pin = {}
    for (c, q), pins in V._LIFE8_ISSUER_INCONSISTENT.items():
        code_pin[("_LIFE8_ISSUER_INCONSISTENT", c, q)] = pins
    for (c, q), pins in IRR_DERIVE_ISSUER_INCONSISTENT.items():
        code_pin[("IRR_DERIVE_ISSUER_INCONSISTENT", c, q)] = pins
    for (c, q), spec in V._TIER2_ISSUER_INCONSISTENT.items():
        code_pin[("_TIER2_ISSUER_INCONSISTENT", c, q)] = spec

    # live recompute
    l8_acc, l8_red, l8_rev, l8_detail = V._life8_issuer_inconsistent(recs)
    print("LIFE8 accepted:", l8_acc, "red:", len(l8_red), "review:", len(l8_rev))
    for d in l8_detail:
        print("   detail", d)
    for r in l8_red:
        print("   RED", r)
    for r in l8_rev:
        print("   REV", r)

    ered, erev = V._exemption_provenance_findings()
    print(f"\nprovenance findings: red={len(ered)} review={len(erev)}")
    for r in ered:
        print("   RED  ", r["rule"], r["registry"], r["code"], r["quarter"], r["detail"][:160])
    for r in erev:
        print("   REV  ", r["rule"], r["registry"], r["code"], r["quarter"], r["detail"][:200])

    print("\n" + "=" * 110)
    print("LIVE CELL AUDIT")
    print("=" * 110)
    rows = []
    for reg, cells in sorted(regs.items()):
        for c, q in sorted(cells):
            e = entries.get((reg, c, q)) or {}
            ver = e.get("verify") or {}
            ran = V._verify_markers_ran(ver)
            pages = ver.get("pages")
            am = len([m for m in (ver.get("absent_markers") or []) if m])
            pm = len([m for m in (ver.get("present_markers") or []) if m])
            contradicted, why = V._verify_absent_markers(ver)
            cp = code_pin.get((reg, c, q))
            lp = e.get("expected_residual")
            rows.append({
                "registry": reg, "company": c, "quarter": q,
                "status": e.get("status"), "claim_kind": e.get("claim_kind"),
                "cit_pages": (e.get("citation") or {}).get("pages"),
                "verify_file": bool(ver.get("file")),
                "verify_pages": pages, "absent": am, "present": pm,
                "markers_ran": ran, "contradicted": contradicted,
                "ledger_pin": lp, "code_pin": ("yes" if cp else "no"),
                "keys": sorted(e.keys()),
            })
    for r in rows:
        print(f"{r['registry']:<32} {r['company']} {r['quarter']}  status={r['status']:<20} "
              f"kind={str(r['claim_kind']):<36} verify_pages={str(r['verify_pages']):<14} "
              f"abs={r['absent']} pres={r['present']} ran={r['markers_ran']} "
              f"ledger_pin={'yes' if r['ledger_pin'] else 'NO':<3} code_pin={r['code_pin']}")
    print("\nkeys per entry:")
    for r in rows:
        print(f"  {r['registry']}|{r['company']}|{r['quarter']}: {r['keys']}")


if __name__ == "__main__":
    main()
