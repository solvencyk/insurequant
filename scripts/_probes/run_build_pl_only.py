#!/usr/bin/env python3
"""Call build_root_masters.build_pl() ONLY (never main(), never build_csm()) -- per repo rule,
build_root_masters.main() is forbidden (destructive precedent). This refreshes root
PL_breakdown.json from the just-rebuilt data/dart/viz/pl_breakdown_master.json."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")

from scripts import build_root_masters as brm  # noqa: E402

n = brm.build_pl()
print(f"build_pl() wrote {n} rows to {brm.PL_OUT}")
