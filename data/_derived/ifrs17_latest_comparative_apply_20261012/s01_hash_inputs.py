"""Read-only: sha256 + row count of every IFRS17-lane master / registry / sidecar the dry run reads.

Run at the start and at the end: the two outputs must be identical (proof that the dry run wrote nothing).
usage: python s01_hash_inputs.py <out.txt>
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parents[3]

FILES = [
    "CSM_waterfall.json", "CSM_waterfall_provenance.json", "CSM_amortization.json", "CSM_sensitivity.json",
    "PL_breakdown.json", "PL_breakdown_provenance.json", "IFRS17_BS.json",
    "insurance_liability_portfolio.json", "insurance_liability_portfolio_provenance.json",
    "NB_CSM_multiple.json", "kics_disclosure.json",
    "data/_derived/ilp_restated_comparative.json", "data/_derived/ilp_includes_lic.json",
    "data/_gold/user_pl_cells.json", "data/_gold/user_csm_cells.json", "data/_gold/user_pl_confirmed_cells.json",
    "data/_gold/bs_restated_cells.json", "data/_gold/csm_amort_identity_ledger.json",
    "data/_gold/pl_csm_amort_missing_ledger.json", "data/_gold/pl_amort_coverage_baseline.json",
    "data/_gold/pl_bridge_baseline.json", "data/_gold/gold_overlay_ledger.json",
    "data/_gold/live_artifact_baseline.json",
    "data/dart/viz/csm_waterfall.json", "data/dart/viz/csm_amort_schedule.json",
    "data/dart/viz/csm_continuity_validation.json",
    "data/dart/viz/pl_breakdown_master.json",
    "insurequant_master_tables.xlsx",
    "tests/fixtures/pl_breakdown_golden.json",
]


def main() -> int:
    out = Path(sys.argv[1])
    lines = []
    for rel in FILES:
        p = ROOT / rel
        if not p.exists():
            lines.append(f"{rel}\tMISSING")
            continue
        b = p.read_bytes()
        h = hashlib.sha256(b).hexdigest()
        n = ""
        if rel.endswith(".json"):
            try:
                o = json.loads(b.decode("utf-8"))
                n = str(len(o)) if isinstance(o, (list, dict)) else ""
            except Exception:
                n = "?"
        lines.append(f"{rel}\t{len(b)}\t{n}\t{h}")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
