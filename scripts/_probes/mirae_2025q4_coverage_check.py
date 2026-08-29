import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
cov = json.loads((ROOT / "data/_derived/pl_breakdown_coverage.json").read_text(encoding="utf-8"))
hits = [r for r in cov if r.get("code") == "KR0079" and r.get("quarter") == "2025.4Q"]
for r in hits:
    print(r)
