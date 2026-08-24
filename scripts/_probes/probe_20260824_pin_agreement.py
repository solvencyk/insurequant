"""Read-only: does the ledger's expected_residual agree with (a) the code-side pin
and (b) the live rule output?  PIN_STALE detector.  Nothing is written."""
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


def flat(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{prefix}{k}."))
    else:
        out[prefix.rstrip(".")] = d
    return out


def main():
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    entries = {(e.get("registry"), e.get("company"), e.get("quarter")): e
               for e in led.get("entries") or []}
    recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))

    print("### LIFE8")
    for (c, q), pins in sorted(V._LIFE8_ISSUER_INCONSISTENT.items()):
        e = entries.get(("_LIFE8_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        print(f"  {c} {q}: code={pins}")
        print(f"           ledger={lp}")
        for k in set(pins) | set(lp):
            a, b = pins.get(k), lp.get(k)
            flagm = "" if (a is not None and b is not None and abs(a - b) < 1e-9) else "  <<< MISMATCH"
            print(f"           {k}: code={a} ledger={b}{flagm}")

    print("\n### IRR_DERIVE")
    for (c, q), pins in sorted(IRR_DERIVE_ISSUER_INCONSISTENT.items()):
        e = entries.get(("IRR_DERIVE_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        fa, fb = flat(pins), flat(lp)
        keys = sorted(set(fa) | set(fb))
        bad = [k for k in keys
               if not (isinstance(fa.get(k), (int, float)) and isinstance(fb.get(k), (int, float))
                       and abs(fa[k] - fb[k]) < 1e-6)]
        print(f"  {c} {q}: code_keys={len(fa)} ledger_keys={len(fb)} mismatched={bad}")
        for k in bad:
            print(f"      {k}: code={fa.get(k)} ledger={fb.get(k)}")

    print("\n### TIER2")
    for (c, q), spec in sorted(V._TIER2_ISSUER_INCONSISTENT.items()):
        e = entries.get(("_TIER2_ISSUER_INCONSISTENT", c, q)) or {}
        lp = e.get("expected_residual") or {}
        code_find = spec.get("findings") or {}
        fa, fb = flat(code_find), flat(lp)
        keys = sorted(set(fa) | set(fb))
        bad = [k for k in keys
               if not (isinstance(fa.get(k), (int, float)) and isinstance(fb.get(k), (int, float))
                       and abs(fa[k] - fb[k]) < 1e-6)]
        print(f"  {c} {q}: code_findings={len(fa)} ledger_pin={len(fb)} mismatched={bad}")
        for k in bad:
            print(f"      {k}: code={fa.get(k)} ledger={fb.get(k)}")

    print("\n### live TIER2 recompute")
    try:
        out = V._tier2_issuer_inconsistent(recs)
        acc, red, review, detail = out[0], out[1], out[2], out[3]
        print(f"  accepted={len(acc)} red={len(red)} review={len(review)} detail={len(detail)}")
        for r in red:
            print("   RED", r)
        for r in review:
            print("   REV", r)
    except Exception as exc:  # noqa: BLE001
        print("  (direct call failed:", exc, ")")

    print("\n### live IRR recompute")
    try:
        fn = getattr(V, "_irr_derive_issuer_inconsistent", None)
        print("  fn:", fn)
    except Exception as exc:  # noqa: BLE001
        print("  ", exc)

    print("\n### entries missing registered_by / scope")
    for k, e in sorted(entries.items()):
        miss = [f for f in ("registered_by", "claim", "claim_kind", "citation", "status")
                if not e.get(f)]
        if miss:
            print(f"  {k}: missing {miss}")


if __name__ == "__main__":
    main()
