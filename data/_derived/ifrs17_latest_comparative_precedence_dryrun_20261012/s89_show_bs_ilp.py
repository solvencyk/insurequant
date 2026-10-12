"""Read-only: summaries of bs_block_verdicts.csv and ilp_yearend_2024_census.csv and the Lina probe json."""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
bs = list(csv.DictReader(open(HERE / "bs_block_verdicts.csv", encoding="utf-8-sig")))
print("BS rows", len(bs), "columns", list(bs[0].keys()))
print(dict(Counter(r["verdict"] for r in bs)))
for r in bs:
    if not r["verdict"].startswith("변화 없음"):
        print({k: v for k, v in r.items() if v not in ("", None)})
print("=" * 100)
il = list(csv.DictReader(open(HERE / "ilp_yearend_2024_census.csv", encoding="utf-8-sig")))
print("ILP rows", len(il), "columns", list(il[0].keys()))
for key in ("cls", "verdict", "status"):
    if key in il[0]:
        print(key, dict(Counter(r[key] for r in il)))
for r in il[:3]:
    print(r)
print("=" * 100)
for fn in ("lina_csm_probe.json", "lina_csm_probe2.json"):
    print(fn)
    print(json.dumps(json.loads((HERE / fn).read_text(encoding="utf-8")), ensure_ascii=False)[:2500])
