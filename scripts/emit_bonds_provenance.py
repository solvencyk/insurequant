# -*- coding: utf-8 -*-
"""Emit provenance sidecar for the DART capital-securities disclosure supplement.

Downloader Phase 2 contract (inbox/downloader/20260616T1242Z):
  source_file  = repo-relative path to the bonds normalized file
  as_of_date   = quarter-end of the disclosure period (2026-03-31 for 2026.1Q)
  effective_filtered = True (bonds_outstanding already excludes called/matured as of pull date)

Outputs:
  data/bonds/disclosure/disclosure_bonds_provenance.json  — DART supplement provenance

2026-08-03: the FSC (data.go.kr) bonds/normalized half of this script was retired along
with the `bonds` downloader source (inbox/downloader/20260803T0057Z) — capital-securities
issuance is now sourced entirely from DART per-bond extraction
(data/bonds/capital_securities_fy2025.json). See docs/changelog_downloader.md 2026-08-03.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")

STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# Quarter periods covered: 2026.1Q is the current disclosure quarter
QUARTER = "2026.1Q"
AS_OF = "2026-03-31"

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
