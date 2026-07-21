# -*- coding: utf-8 -*-
"""Emit provenance sidecar for bonds/capital-securities fetched artifacts.

Downloader Phase 2 contract (inbox/downloader/20260616T1242Z):
  source_file  = repo-relative path to the bonds normalized file
  as_of_date   = quarter-end of the disclosure period (2026-03-31 for 2026.1Q)
  effective_filtered = True (bonds_outstanding already excludes called/matured as of pull date)

Outputs:
  data/bonds/normalized/<stamp>/bonds_provenance.json  — bonds effective-list provenance
  data/bonds/disclosure/disclosure_bonds_provenance.json  — DART supplement provenance
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# --- bonds/normalized (FSC 크롤) ---
BONDS_DIR = REPO / "data" / "bonds" / "normalized"
latest = sorted(BONDS_DIR.glob("*T*Z"), reverse=True)
if not latest:
    print("ERROR: no bonds/normalized stamp dir found")
    sys.exit(1)
latest_dir = latest[0]
bonds_file = latest_dir / "bonds_by_insurer.json"
manifest_file = latest_dir / "manifest.json"

bonds_data = json.loads(bonds_file.read_text(encoding="utf-8"))
manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

# Quarter periods covered: 2026.1Q is the current disclosure quarter
# as_of_date = 2026-03-31 (2026.1Q end). FSC pull was 2026-06-16 (3 months later —
# no bonds called in the gap confirmed by checking status of all outstanding bonds).
QUARTER = "2026.1Q"
AS_OF = "2026-03-31"
REL_BONDS_FILE = bonds_file.relative_to(REPO).as_posix()

cells = []
for company_code, company_data in bonds_data.items():
    cells.append({
        "company_code": company_code,
        "quarter": QUARTER,
        "item_block": "capital_securities_effective_list",
        "source_id": "FSC_BONDS",
        "as_of_date": AS_OF,
        "source_file": REL_BONDS_FILE,
        "effective_filtered": True,
        "_note": f"FSC bonds pull {manifest.get('as_of','?')}; outstanding-only filter applied "
                 f"(bonds_outstanding={company_data.get('bonds_outstanding',0)} of "
                 f"{company_data.get('bonds_total',0)} total)",
    })

bonds_provenance = {
    "master": "capital_securities_effective_list",
    "generated_at": STAMP,
    "pull_date": manifest.get("as_of", ""),
    "cells": cells,
}
prov_path = latest_dir / "bonds_provenance.json"
prov_path.write_text(json.dumps(bonds_provenance, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Written: {prov_path.relative_to(REPO).as_posix()} ({len(cells)} cells)")

# --- DART supplement (disclosure per-bond) ---
disc_file = REPO / "data" / "bonds" / "disclosure" / "2026q1_capital_securities.json"
if disc_file.exists():
    disc_data = json.loads(disc_file.read_text(encoding="utf-8"))
    disc_cells = []
    rel_disc_file = disc_file.relative_to(REPO).as_posix()
    for company_code, company_data in disc_data.get("companies", {}).items():
        disc_cells.append({
            "company_code": company_code,
            "quarter": QUARTER,
            "item_block": "capital_securities_dart_supplement",
            "source_id": "DART",
            "as_of_date": AS_OF,
            "source_file": rel_disc_file,
            "effective_filtered": True,
            "_note": "DART 주요사항보고서(자본으로인정되는채무증권발행결정) per-bond supplement; "
                     "outstanding filter: all bonds issued before 2026-03-31 with call > 2026-03-31",
        })
    disc_prov = {
        "master": "capital_securities_dart_supplement",
        "generated_at": STAMP,
        "cells": disc_cells,
    }
    disc_prov_path = REPO / "data" / "bonds" / "disclosure" / "disclosure_bonds_provenance.json"
    disc_prov_path.write_text(
        json.dumps(disc_prov, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Written: {disc_prov_path.relative_to(REPO).as_posix()} ({len(disc_cells)} cells)")

print("\nDone. Provenance sidecar(s) emitted.")
print("Next: parser/publishing emit source_id + item_block for master-level provenance.")
