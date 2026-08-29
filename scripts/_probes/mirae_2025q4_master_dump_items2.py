import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
print(list(rows[0].keys()))
print(rows[0])
names = sorted(set(r.get("회사명") or r.get("회사") for r in rows))
mirae = [n for n in names if n and "미래" in n]
print("mirae-matching names:", mirae)
