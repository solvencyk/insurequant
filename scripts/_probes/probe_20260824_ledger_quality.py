"""Read-only audit of data/_gold/kics_exemption_provenance.json entry quality.

Usage:
  python scripts/_probes/probe_20260824_ledger_quality.py dump
  python scripts/_probes/probe_20260824_ledger_quality.py table
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

LEDGER = ROOT / "data" / "_gold" / "kics_exemption_provenance.json"


def load():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "table"
    led = load()
    entries = led.get("entries") or []
    regs = V._exemption_registries()
    live = set()
    for reg, cells in regs.items():
        for c, q in cells:
            live.add((reg, c, q))

    by_key = {}
    for e in entries:
        by_key[(e.get("registry"), e.get("company"), e.get("quarter"))] = e

    print(f"ledger entries total = {len(entries)}")
    print(f"live registry cells  = {len(live)}")
    orphans = [k for k in by_key if k not in live]
    missing = [k for k in live if k not in by_key]
    print(f"orphan ledger records (not in any live registry) = {len(orphans)}")
    for k in sorted(orphans):
        print(f"   ORPHAN {k}  status={by_key[k].get('status')}")
    print(f"live cells with NO ledger record = {len(missing)}")
    for k in sorted(missing):
        print(f"   MISSING {k}")

    if mode == "dump":
        for k in sorted(live):
            e = by_key.get(k)
            print("=" * 100)
            print(json.dumps({"_key": list(k), **(e or {})}, ensure_ascii=False, indent=2))
        return

    # table mode
    print()
    hdr = ("registry", "company", "quarter", "status", "claim_kind",
           "cit_pages", "abs_mk", "pres_mk", "has_pin")
    print(" | ".join(hdr))
    for k in sorted(live):
        reg, c, q = k
        e = by_key.get(k) or {}
        cit = e.get("citation") or {}
        ver = e.get("verify") or {}
        pages = cit.get("pages")
        has_pin = bool(e.get("expected_residual") or e.get("expected_cells")
                       or e.get("pinned_residual"))
        print(" | ".join([
            reg, c, q, str(e.get("status")), str(e.get("claim_kind")),
            str(pages), str(len(ver.get("absent_markers") or [])),
            str(len(ver.get("present_markers") or [])), str(has_pin),
        ]))


if __name__ == "__main__":
    main()
