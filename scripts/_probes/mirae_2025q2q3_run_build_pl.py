"""Call build_root_masters.build_pl() ONLY (never main()) to propagate the
data/dart/viz/pl_breakdown_master.json surgical patch into root PL_breakdown.json.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.build_root_masters import build_pl  # noqa: E402

n = build_pl()
print(f"build_pl() wrote {n} rows to PL_breakdown.json")
