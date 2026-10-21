"""Read-only: gold overlay census exactly as tests/test_rule_coverage_manifest.py does it, for live files or candidates.

Usage: python census_check.py <gold.json> <ledger.json>
Prints (gold cells, masked cells) for the CSM overlay, the unpinned masked cells (must be 0) and stale pins.
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

import validate_data_contract as G  # noqa: E402  (same import the manifest test uses)

gold = json.load(open(sys.argv[1], encoding="utf-8"))
ledger = json.load(open(sys.argv[2], encoding="utf-8"))
diag = json.load(open(ROOT / "data/dart/viz/csm_waterfall_master_diag.json", encoding="utf-8"))
rows = G.gold_overlay_census("CSM", gold.get("set", []), diag)
masked = [r for r in rows if r["verdict"] in G._GOLD_MASKED]
pins = ledger.get("entries", {})
unpinned = [r["key"] for r in masked if r["key"] not in pins]
seen = {r["key"] for r in rows}
stale = [k for k in pins if k.startswith("CSM|") and k not in seen]
drift = [r["key"] for r in rows if r["key"] in pins and r["verdict"] not in G._GOLD_MASKED]
print(f"CSM census (gold cells, masked cells) = ({len(rows)}, {len(masked)})")
print("masked but unpinned:", unpinned)
print("pinned but no longer masked (would be GOLD_OVERLAY_DRIFT RED):", drift)
print("pins whose gold cell is gone (stale YELLOW):", stale)
kr = [(r["quarter"], r["item"], r["gold"], r["src"], r["verdict"]) for r in rows if r["company"] == "KR0073"]
print("KR0073 gold cells:", len(kr))
